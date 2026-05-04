"""
Alerts router — retrieve active alerts for teachers.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload
from pydantic import BaseModel

from datetime import datetime, timezone

from db import get_db
from models.student import Student
from models.session import Session
from routers.auth import get_current_student

router = APIRouter()


# ── Request/Response Models ────────────────────────────────────────────────────

class AlertSession(BaseModel):
    id: str
    student_name: str
    question: str
    hint_level: int
    fails_at_level: int
    started_at: str


class AlertsResponse(BaseModel):
    pending_alerts: list[AlertSession]


class TeacherMetrics(BaseModel):
    total_students: int
    sessions_today: int
    average_success_rate: float
    pending_alerts: int


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=AlertsResponse)
async def get_alerts(
    teacher: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all active student alerts for a teacher.
    Only teachers can access this endpoint.
    """
    if teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access alerts")

    # Get all sessions that have alerted and not yet resolved
    stmt = select(Session).options(joinedload(Session.student)).where(and_(Session.teacher_alerted == True, Session.resolved == False))
    result = await db.execute(stmt)
    sessions = result.unique().scalars().all()

    alerts = []
    for session in sessions:
        alerts.append(AlertSession(
            id=str(session.id),
            student_name=session.student.name,
            question=session.question,
            hint_level=session.hint_level,
            fails_at_level=session.fails_at_level,
            started_at=session.started_at.isoformat(),
        ))

    return AlertsResponse(pending_alerts=alerts)


@router.get("/metrics", response_model=TeacherMetrics)
async def get_metrics(
    teacher: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve classroom analytics for teachers.
    """
    if teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can access alerts")

    stmt = select(Session)
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    total_students_stmt = select(func.count(Student.id))
    total_students_result = await db.execute(total_students_stmt)
    total_students = total_students_result.scalar_one()

    sessions_today = sum(
        1 for session in sessions
        if session.started_at.date() == datetime.now(timezone.utc).date()
    )

    resolved_count = sum(1 for session in sessions if session.resolved)
    average_success_rate = round((resolved_count / len(sessions) if sessions else 0) * 100, 2)

    alert_stmt = select(Session).where(and_(Session.teacher_alerted == True, Session.resolved == False))
    alert_result = await db.execute(alert_stmt)
    pending_alerts = len(alert_result.scalars().all())

    return TeacherMetrics(
        total_students=total_students,
        sessions_today=sessions_today,
        average_success_rate=average_success_rate,
        pending_alerts=pending_alerts,
    )
