"""
Progress router — retrieve student progress and analytics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from db import get_db
from models.student import Student
from models.session import Session
from routers.auth import get_current_student

router = APIRouter()


# ── Request/Response Models ────────────────────────────────────────────────────

class SubjectProgress(BaseModel):
    name: str
    sessions: int
    success_rate: float


class RecentSession(BaseModel):
    id: str
    question: str
    subject: str
    resolved: bool
    started_at: str


class StudentProgressResponse(BaseModel):
    subjects: list[SubjectProgress]
    recent_sessions: list[RecentSession]


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.get("/{student_id}/progress", response_model=StudentProgressResponse)
async def get_student_progress(
    student_id: str,
    current_student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a student's progress breakdown by subject.
    """
    # For now, only allow students to view their own progress
    # Teachers will need a separate endpoint
    stmt = select(Session).where(Session.student_id == current_student.id)
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Group by subject
    subject_stats: dict[str, list[bool]] = {}
    for session in sessions:
        if session.subject not in subject_stats:
            subject_stats[session.subject] = []
        subject_stats[session.subject].append(session.resolved)

    # Calculate success rates
    subjects_data = []
    for subject, resolved_list in subject_stats.items():
        success_rate = sum(resolved_list) / len(resolved_list) if resolved_list else 0
        subjects_data.append(SubjectProgress(
            name=subject,
            sessions=len(resolved_list),
            success_rate=round(success_rate, 2),
        ))

    # Recent sessions (last 10)
    recent_sessions_data = []
    for session in sessions[-10:]:
        recent_sessions_data.append(RecentSession(
            id=str(session.id),
            question=session.question[:50] + ("..." if len(session.question) > 50 else ""),
            subject=session.subject,
            resolved=session.resolved,
            started_at=session.started_at.isoformat(),
        ))

    return StudentProgressResponse(
        subjects=subjects_data,
        recent_sessions=recent_sessions_data,
    )
