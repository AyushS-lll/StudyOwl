"""
Sessions router — start a session, submit attempts, retrieve session info.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from uuid import UUID

from db import get_db
from models.student import Student
from models.session import Session
from routers.auth import get_current_student
from services import session_manager, ocr_service
from sqlalchemy import select


# Standard headers for streaming endpoints. `X-Accel-Buffering: no` disables
# response buffering on nginx-family reverse proxies, which would otherwise
# coalesce the chunks and defeat the streaming UX.
_STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}


def _ndjson(event: dict) -> bytes:
    """Serialize one event as a newline-terminated JSON line."""
    return (json.dumps(event, default=str) + "\n").encode("utf-8")

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
    final_answer: str | None = None
    review_mode: bool = False
    review_url: str | None = None
    learning_resources: list[LearningResource] = []


class ClarifyRequest(BaseModel):
    message: str


class ClarifyResponse(BaseModel):
    clarification: str
    remaining: int  # Clarifications left at the current hint level.


class SessionDetailResponse(BaseModel):
    id: str
    question: str
    subject: str
    hint_level: int
    resolved: bool
    started_at: str
    resolved_at: str | None = None


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/start")
async def start_session(
    req: StartSessionRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new homework session.

    PR 9: this endpoint now streams an NDJSON event sequence:
      {"type": "session_created", "session_id", "subject", "hint_level"}
      {"type": "chunk", "text"} * N
      {"type": "done"}  (or {"type": "error", "message"} on failure)

    Auth + OCR happen synchronously before streaming begins so that errors
    in those paths return a proper HTTPException rather than mid-stream.
    """
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Only students can start homework sessions")

    # Extract text from photo if provided (synchronous, pre-stream).
    photo_url = None
    if req.photo_b64:
        extracted_text = await ocr_service.extract_text_from_photo(req.photo_b64)
        if extracted_text:
            req.question = extracted_text
        # TODO: Upload to R2 and get URL
        photo_url = None

    async def event_stream():
        async for event in session_manager.start_session_stream(
            db=db,
            student_id=student.id,
            question=req.question,
            photo_url=photo_url,
        ):
            yield _ndjson(event)

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers=_STREAM_HEADERS,
    )


@router.post("/{session_id}/attempt")
async def submit_attempt(
    session_id: str,
    req: AttemptRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a student's answer attempt.

    PR 9: this endpoint streams an NDJSON event sequence. See
    `session_manager.process_attempt_stream` for the event shapes.
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    stmt = (
        select(Session)
        .options(joinedload(Session.student))
        .where(Session.id == session_uuid)
    )
    result = await db.execute(stmt)
    session = result.unique().scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access homework sessions")
    if session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")

    async def event_stream():
        async for event in session_manager.process_attempt_stream(
            db=db,
            session=session,
            attempt_text=req.attempt_text,
        ):
            yield _ndjson(event)

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers=_STREAM_HEADERS,
    )


@router.post("/{session_id}/clarify", response_model=ClarifyResponse)
async def clarify_session(
    session_id: str,
    req: ClarifyRequest,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a clarifying question about the current hint. Does NOT count as an
    attempt and does NOT advance the hint level. Capped per hint level by
    settings.clarifications_per_level_limit.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Clarification message is empty")

    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    stmt = (
        select(Session)
        .options(joinedload(Session.student))
        .where(Session.id == session_uuid)
    )
    session = (await db.execute(stmt)).unique().scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access homework sessions")
    if session.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this session")
    if session.resolved:
        raise HTTPException(status_code=409, detail="Session is already resolved")

    try:
        result = await session_manager.process_clarification(
            db=db,
            session=session,
            message=req.message,
        )
    except PermissionError as exc:
        # Cap exceeded — distinct from auth 403.
        raise HTTPException(status_code=429, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ClarifyResponse(**result)


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

    if student.role != "student":
        raise HTTPException(status_code=403, detail="Only students can access homework sessions")
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
