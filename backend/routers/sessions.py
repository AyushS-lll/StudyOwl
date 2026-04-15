"""
Sessions router — start a session, submit attempts, retrieve session info.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID

from db import get_db
from models.student import Student
from models.session import Session
from routers.auth import get_current_student
from services import session_manager, ocr_service
from sqlalchemy import select

router = APIRouter()


# ── Request/Response Models ────────────────────────────────────────────────────

class StartSessionRequest(BaseModel):
    question: str
    photo_b64: str | None = None  # Base64-encoded image


class StartSessionResponse(BaseModel):
    session_id: str
    hint: str
    hint_level: int
    subject: str


class AttemptRequest(BaseModel):
    attempt_text: str


class LearningResource(BaseModel):
    title: str
    url: str | None = None
    summary: str | None = None


class AttemptResponse(BaseModel):
    status: str  # "correct" or "wrong"
    hint: str | None = None
    hint_level: int | None = None
    message: str | None = None
    review_mode: bool = False
    review_url: str | None = None
    learning_resources: list[LearningResource] = []


class SessionDetailResponse(BaseModel):
    id: str
    question: str
    subject: str
    hint_level: int
    resolved: bool
    started_at: str
    resolved_at: str | None = None


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    req: StartSessionRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new homework session.
    """
    # Extract text from photo if provided
    photo_url = None
    if req.photo_b64:
        # In production, upload to Cloudflare R2
        # For now, store the base64 (or extract text with OCR)
        extracted_text = await ocr_service.extract_text_from_photo(req.photo_b64)
        if extracted_text:
            req.question = extracted_text
        # TODO: Upload to R2 and get URL
        photo_url = None

    session, hint = await session_manager.start_session(
        db=db,
        student_id=student.id,
        question=req.question,
        photo_url=photo_url,
    )

    return StartSessionResponse(
        session_id=str(session.id),
        hint=hint,
        hint_level=session.hint_level,
        subject=session.subject,
    )


@router.post("/{session_id}/attempt", response_model=AttemptResponse)
async def submit_attempt(
    session_id: str,
    req: AttemptRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a student's answer attempt for a session.
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Fetch session
    stmt = select(Session).where(Session.id == session_uuid)
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    # Process the attempt
    result = await session_manager.process_attempt(
        db=db,
        session=session,
        attempt_text=req.attempt_text,
    )

    return AttemptResponse(**result)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve details of a specific session.
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    stmt = select(Session).where(Session.id == session_uuid)
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return SessionDetailResponse(
        id=str(session.id),
        question=session.question,
        subject=session.subject,
        hint_level=session.hint_level,
        resolved=session.resolved,
        started_at=session.started_at.isoformat(),
        resolved_at=session.resolved_at.isoformat() if session.resolved_at else None,
    )
