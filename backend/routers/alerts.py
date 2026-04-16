"""
Alerts router — retrieve active alerts for teachers.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

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
    stmt = select(Session).where(Session.teacher_alerted, ~Session.resolved)
    result = await db.execute(stmt)
    sessions = result.scalars().all()

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
