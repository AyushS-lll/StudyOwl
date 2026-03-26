"""
Session manager — orchestrates the hint state machine.

Controls hint level progression, attempt counting, and escalation logic.
All student interactions flow through process_attempt().
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.session import Session
from models.attempt import Attempt
from services import hint_engine, answer_verifier, alert_service, subject_router


async def start_session(
    db: AsyncSession,
    student_id: UUID,
    question: str,
    photo_url: str | None = None,
) -> tuple[Session, str]:
    """
    Create a new session, classify the subject, and return the first hint.

    Returns:
        Tuple of (Session ORM object, first hint string).
    """
    subject = await subject_router.classify(question)

    session = Session(
        student_id=student_id,
        question=question,
        subject=subject,
        hint_level=1,
        fails_at_level=0,
        photo_url=photo_url,
        started_at=datetime.now(timezone.utc),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    first_hint = hint_engine.get_hint(
        question=question,
        subject=subject,
        level=1,
        previous_attempts=[],
    )

    return session, first_hint


async def process_attempt(
    db: AsyncSession,
    session: Session,
    attempt_text: str,
) -> dict:
    """
    Process a student's answer attempt against the current session state.

    State machine:
      - Correct → log success, close session.
      - Wrong   → increment fail counter, optionally advance hint level, fetch next hint.
      - 3 fails at same level → trigger teacher alert.
      - Distress detected → trigger teacher alert immediately.

    Returns:
        Dict with keys: status ('correct'|'wrong'), hint (if wrong),
        hint_level (if wrong), message.
    """
    # Distress check (fires alert regardless of attempt correctness)
    if hint_engine.detect_distress(attempt_text):
        await _trigger_alert(db, session, reason="Student distress signal")

    # Fetch all previous attempt texts for this session
    previous_attempts = [a.attempt_text for a in session.attempts]

    # Verify the attempt
    is_correct = await answer_verifier.check(
        question=session.question,
        answer=attempt_text,
        subject=session.subject,
    )

    # Log the attempt
    attempt = Attempt(
        session_id=session.id,
        attempt_text=attempt_text,
        is_correct=is_correct,
        hint_level=session.hint_level,
    )
    db.add(attempt)

    if is_correct:
        session.resolved = True
        session.resolved_at = datetime.now(timezone.utc)
        await db.commit()
        return {"status": "correct", "message": "Brilliant work! You got it!"}

    # Wrong answer — advance state
    session.fails_at_level += 1

    if session.fails_at_level >= settings.max_fails_before_alert:
        await _trigger_alert(
            db, session,
            reason=f"Stuck at hint level {session.hint_level} after {session.fails_at_level} attempts",
        )

    if session.hint_level < 3:
        session.hint_level += 1
        session.fails_at_level = 0

    hint = hint_engine.get_hint(
        question=session.question,
        subject=session.subject,
        level=session.hint_level,
        previous_attempts=previous_attempts + [attempt_text],
    )

    attempt.hint_shown = hint
    await db.commit()

    return {
        "status": "wrong",
        "hint": hint,
        "hint_level": session.hint_level,
        "message": None,
    }


async def _trigger_alert(db: AsyncSession, session: Session, reason: str) -> None:
    """Fire a teacher alert if one hasn't been sent for this session yet."""
    if session.teacher_alerted:
        return
    session.teacher_alerted = True
    await db.commit()
    await alert_service.notify_teacher(session, reason=reason)
