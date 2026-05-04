"""
Session manager — orchestrates the hint state machine.

Controls hint level progression, attempt counting, and escalation logic.
All student interactions flow through process_attempt().
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.session import Session
from models.attempt import Attempt
from . import hint_engine
from . import answer_verifier
from . import alert_service
from . import subject_router
from . import travily_service


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

    first_hint = await hint_engine.get_hint(
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
    if await hint_engine.detect_distress(attempt_text):
        await _trigger_alert(db, session, reason="Student distress signal")

    # Fetch all previous attempt texts for this session using async-safe SQL
    result = await db.execute(
        select(Attempt.attempt_text).where(Attempt.session_id == session.id)
    )
    previous_attempts = [row[0] for row in result.all()]

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

    # Wrong answer — if the student has already seen all three hints, reveal the direct answer.
    total_wrong_attempts = len(previous_attempts) + 1
    if session.hint_level == 3 and total_wrong_attempts >= settings.max_fails_before_review:
        direct_answer = await hint_engine.get_direct_answer(session.question, session.subject)
        learning_resources = await travily_service.fetch_learning_resources(session.question, limit=5)
        session.resolved = True
        session.resolved_at = datetime.now(timezone.utc)
        await db.commit()
        return {
            "status": "wrong",
            "hint": None,
            "hint_level": session.hint_level,
            "message": "You have reached the final hint, so here is the correct answer along with resources to review.",
            "review_mode": True,
            "review_url": None,
            "learning_resources": learning_resources,
            "final_answer": direct_answer,
        }

    review_mode = total_wrong_attempts >= settings.max_fails_before_review
    review_url = None

    if review_mode:
        session.hint_level = 3
        hint = None
        learning_resources = await travily_service.fetch_learning_resources(session.question, limit=5)
        if learning_resources:
            hint = (
                "You've used up your 3 attempts and need to review a related concept before trying again. "
                "Check out the resources below to learn more, then try a new question."
            )
        else:
            hint = (
                "You've used up your 3 attempts. Review a related worked example or article about solving linear equations, "
                "then come back and try again."
            )
    else:
        if session.hint_level < 3:
            session.hint_level += 1
            session.fails_at_level = 0
        else:
            session.fails_at_level += 1
        hint = await hint_engine.get_hint(
            question=session.question,
            subject=session.subject,
            level=session.hint_level,
            previous_attempts=previous_attempts + [attempt_text],
        )
        learning_resources = []

    if session.fails_at_level >= settings.max_fails_before_alert:
        await _trigger_alert(
            db, session,
            reason=f"Stuck at hint level {session.hint_level} after {session.fails_at_level} attempts",
        )

    attempt.hint_shown = hint
    await db.commit()

    return {
        "status": "wrong",
        "hint": hint,
        "hint_level": session.hint_level,
        "message": None,
        "review_mode": review_mode,
        "review_url": review_url,
        "learning_resources": learning_resources,
    }


async def _trigger_alert(db: AsyncSession, session: Session, reason: str) -> None:
    """Fire a teacher alert if one hasn't been sent for this session yet."""
    if session.teacher_alerted:
        return
    session.teacher_alerted = True
    await db.commit()
    await alert_service.notify_teacher(session, reason=reason)
