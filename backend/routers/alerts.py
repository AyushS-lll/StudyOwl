"""
Alerts router — list, acknowledge, and resolve teacher alerts.

Reads/writes go through the `alerts` table introduced in PR 7. The legacy
`Session.teacher_alerted` flag is still maintained by session_manager for one
PR cycle of backward compat, but this router no longer reads it.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from uuid import UUID

from db import get_db
from models.alert import Alert
from models.session import Session
from models.student import Student
from routers.auth import get_current_student


router = APIRouter()


# ── Request/Response Models ────────────────────────────────────────────────────


class AlertOut(BaseModel):
    id: str
    session_id: str
    student_name: str
    question: str
    hint_level: int
    fails_at_level: int
    severity: str
    reason_kind: str
    reason_text: str
    notification_status: str
    created_at: str
    acknowledged_at: str | None = None
    acknowledged_by_name: str | None = None


class AlertsResponse(BaseModel):
    pending_alerts: list[AlertOut]


class TeacherMetrics(BaseModel):
    total_students: int
    sessions_today: int
    average_success_rate: float
    pending_alerts: int


def _require_teacher(teacher: Student) -> None:
    if teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access alerts")


def _alert_out(alert: Alert) -> AlertOut:
    return AlertOut(
        id=str(alert.id),
        session_id=str(alert.session_id),
        student_name=alert.session.student.name if alert.session.student else "Unknown",
        question=alert.session.question,
        hint_level=alert.session.hint_level,
        fails_at_level=alert.session.fails_at_level,
        severity=alert.severity,
        reason_kind=alert.reason_kind,
        reason_text=alert.reason_text,
        notification_status=alert.notification_status,
        created_at=alert.created_at.isoformat(),
        acknowledged_at=alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        acknowledged_by_name=alert.acknowledger.name if alert.acknowledger else None,
    )


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("/", response_model=AlertsResponse)
async def get_alerts(
    teacher: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Active (unresolved) alerts for the teacher dashboard."""
    _require_teacher(teacher)

    stmt = (
        select(Alert)
        .options(
            joinedload(Alert.session).joinedload(Session.student),
            joinedload(Alert.acknowledger),
        )
        .where(Alert.resolved_at.is_(None))
        .order_by(Alert.created_at.desc())
    )
    result = await db.execute(stmt)
    alerts = result.unique().scalars().all()

    return AlertsResponse(pending_alerts=[_alert_out(a) for a in alerts])


@router.get("/metrics", response_model=TeacherMetrics)
async def get_metrics(
    teacher: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Classroom-level analytics, including count of unresolved alerts."""
    _require_teacher(teacher)

    sessions_result = await db.execute(select(Session))
    sessions = sessions_result.scalars().all()

    total_students = (
        await db.execute(select(func.count(Student.id)))
    ).scalar_one()

    today = datetime.now(timezone.utc).date()
    sessions_today = sum(1 for s in sessions if s.started_at.date() == today)

    resolved_count = sum(1 for s in sessions if s.resolved)
    average_success_rate = round(
        (resolved_count / len(sessions) if sessions else 0) * 100, 2
    )

    pending_alerts = (
        await db.execute(
            select(func.count(Alert.id)).where(Alert.resolved_at.is_(None))
        )
    ).scalar_one()

    return TeacherMetrics(
        total_students=total_students,
        sessions_today=sessions_today,
        average_success_rate=average_success_rate,
        pending_alerts=pending_alerts,
    )


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: str,
    teacher: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark an alert as acknowledged by the calling teacher. Idempotent: if
    already acknowledged, returns the existing record without overwriting
    `acknowledged_by` (first-write-wins).
    """
    _require_teacher(teacher)
    alert = await _load_alert(db, alert_id)

    if alert.resolved_at is not None:
        raise HTTPException(status_code=409, detail="Alert already resolved")

    if alert.acknowledged_at is None:
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = teacher.id
        await db.commit()
        await db.refresh(alert)

    # Reload with joinedloads so the response payload has the names.
    return _alert_out(await _load_alert(db, alert_id))


@router.post("/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(
    alert_id: str,
    teacher: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """Mark an alert resolved. Idempotent: re-resolving is a no-op."""
    _require_teacher(teacher)
    alert = await _load_alert(db, alert_id)

    if alert.resolved_at is None:
        alert.resolved_at = datetime.now(timezone.utc)
        # If the resolver hadn't ack'd yet, count this as implicit ack too.
        if alert.acknowledged_at is None:
            alert.acknowledged_at = alert.resolved_at
            alert.acknowledged_by = teacher.id
        await db.commit()

    return _alert_out(await _load_alert(db, alert_id))


async def _load_alert(db: AsyncSession, alert_id: str) -> Alert:
    try:
        uuid_id = UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    stmt = (
        select(Alert)
        .options(
            joinedload(Alert.session).joinedload(Session.student),
            joinedload(Alert.acknowledger),
        )
        .where(Alert.id == uuid_id)
    )
    alert = (await db.execute(stmt)).unique().scalars().first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
