"""
Inactivity scheduler — fires teacher alerts for sessions that have been idle
beyond `inactivity_timeout_minutes`.

Runs as an asyncio task on FastAPI lifespan. Safe to run with multiple uvicorn
workers thanks to a Postgres advisory lock + SELECT ... FOR UPDATE SKIP LOCKED.
Postgres-only — the lock primitives don't exist on SQLite, so the scheduler
no-ops elsewhere.
"""

import asyncio
import logging

from sqlalchemy import select, text
from sqlalchemy.orm import joinedload

from config import settings
from db import SessionLocal, engine
from models.alert import Alert, REASON_INACTIVITY, SEVERITY_FOR_REASON
from models.session import Session
from . import alert_service


logger = logging.getLogger(__name__)

# Arbitrary 32-bit integer identifying the scheduler's advisory lock. Picked
# once and never changed; any process using this same key cooperates.
_ADVISORY_LOCK_KEY = 987_123_456


async def _tick() -> int:
    """
    Run one scan. Returns the number of sessions that were alerted this tick.

    Only one worker actually scans per tick — others get the advisory lock
    rejection and return 0 immediately.
    """
    if engine.dialect.name != "postgresql":
        # Advisory locks + FOR UPDATE SKIP LOCKED are Postgres-only.
        # SQLite-backed dev runs effectively disable inactivity escalation.
        return 0

    timeout_minutes = settings.inactivity_timeout_minutes
    max_age_hours = settings.inactivity_max_session_age_hours

    async with SessionLocal() as db:
        got_lock = await db.execute(
            text("SELECT pg_try_advisory_xact_lock(:k)").bindparams(k=_ADVISORY_LOCK_KEY)
        )
        if not got_lock.scalar():
            # Another worker is running this tick. Bail.
            await db.rollback()
            return 0

        # Use DB-side time everywhere to avoid clock-skew between app and DB.
        # The age filter is on last_activity_at (not started_at) so a student
        # who returns to a day-old session and then goes idle still gets caught.
        stmt = (
            select(Session)
            .options(joinedload(Session.student))
            .where(
                Session.resolved.is_(False),
                Session.teacher_alerted.is_(False),
                Session.last_activity_at < text(
                    f"NOW() - INTERVAL '{timeout_minutes} minutes'"
                ),
                Session.last_activity_at > text(
                    f"NOW() - INTERVAL '{max_age_hours} hours'"
                ),
            )
            .with_for_update(of=Session, skip_locked=True)
        )
        result = await db.execute(stmt)
        stuck_sessions = result.unique().scalars().all()

        alerted = 0
        for session in stuck_sessions:
            reason = f"Student inactive for {timeout_minutes}+ minutes"

            # Same-kind dedup: skip if an unresolved inactivity alert already
            # exists for this session. Mirrors session_manager._trigger_alert.
            existing = await db.execute(
                select(Alert).where(
                    Alert.session_id == session.id,
                    Alert.reason_kind == REASON_INACTIVITY,
                    Alert.resolved_at.is_(None),
                )
            )
            if existing.scalars().first() is not None:
                continue

            alert = Alert(
                session_id=session.id,
                student_id=session.student_id,
                severity=SEVERITY_FOR_REASON[REASON_INACTIVITY],
                reason_kind=REASON_INACTIVITY,
                reason_text=reason,
            )
            db.add(alert)
            # Legacy boolean — kept in sync for one PR cycle so old queries
            # that read `teacher_alerted` still see "this session was alerted."
            session.teacher_alerted = True
            try:
                # notify_teacher commits internally and records sent/failed on
                # the alert row.
                await alert_service.notify_teacher(db, alert, session)
            except Exception as exc:
                # Don't let one notification failure block the rest of the tick.
                logger.exception(
                    "Inactivity alert notify failed for session %s: %s",
                    session.id, exc,
                )
            alerted += 1

        await db.commit()
        return alerted


async def run() -> None:
    """
    Long-running task: tick every `inactivity_scan_interval_seconds`.
    Cancels cleanly when the FastAPI lifespan tears down.
    """
    interval = settings.inactivity_scan_interval_seconds
    logger.info(
        "Inactivity scheduler started (interval=%ss, timeout=%smin).",
        interval, settings.inactivity_timeout_minutes,
    )
    try:
        while True:
            try:
                alerted = await _tick()
                if alerted:
                    logger.info("Inactivity tick alerted %s session(s).", alerted)
            except Exception as exc:
                # Never let a single bad tick kill the scheduler loop.
                logger.exception("Inactivity tick error: %s", exc)
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        logger.info("Inactivity scheduler stopped.")
        raise
