"""
PR 8 — Clarifications.

Focused on the cap-enforcement path in session_manager.process_clarification.
End-to-end tests would need a real DB fixture; deferred.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from services import session_manager


def _make_db_with_existing_clarifications(count: int) -> AsyncMock:
    """
    Mock an AsyncSession whose first execute() returns `count` Attempt rows
    (the cap-enforcement query). Subsequent execute()s return empty rows so
    history queries return nothing.
    """
    db = AsyncMock()

    def make_result(rows):
        result = MagicMock()
        scalars = MagicMock()
        scalars.all.return_value = rows
        result.scalars.return_value = scalars
        result.all.return_value = rows
        return result

    call_index = {"i": 0}

    async def fake_execute(stmt):
        i = call_index["i"]
        call_index["i"] += 1
        if i == 0:
            # First call: cap check — return `count` mock attempts.
            return make_result([MagicMock() for _ in range(count)])
        # Subsequent calls (history fetch) — empty.
        return make_result([])

    db.execute = AsyncMock(side_effect=fake_execute)
    db.add = MagicMock()
    db.commit = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_clarification_rejected_at_cap():
    """Beyond the cap, process_clarification raises PermissionError."""
    from config import settings as cfg
    session = MagicMock(
        id=uuid4(), resolved=False, hint_level=1, subject="math", question="q",
    )
    db = _make_db_with_existing_clarifications(cfg.clarifications_per_level_limit)

    with patch("services.session_manager.hint_engine.detect_distress",
               new=AsyncMock(return_value=False)):
        with pytest.raises(PermissionError):
            await session_manager.process_clarification(db, session, message="why?")


@pytest.mark.asyncio
async def test_clarification_rejected_on_empty_message():
    session = MagicMock(id=uuid4(), resolved=False, hint_level=1)
    db = AsyncMock()
    with pytest.raises(ValueError):
        await session_manager.process_clarification(db, session, message="   ")


@pytest.mark.asyncio
async def test_clarification_rejected_when_resolved():
    session = MagicMock(id=uuid4(), resolved=True, hint_level=2)
    db = AsyncMock()
    with pytest.raises(ValueError):
        await session_manager.process_clarification(db, session, message="huh?")


@pytest.mark.asyncio
async def test_clarification_succeeds_under_cap_and_returns_remaining():
    """1 existing clarification + cap of 3 → success, remaining = 1."""
    from config import settings as cfg
    cfg_limit = cfg.clarifications_per_level_limit
    session = MagicMock(
        id=uuid4(), resolved=False, hint_level=1, subject="math", question="q",
    )
    db = _make_db_with_existing_clarifications(cfg_limit - 2)

    with patch("services.session_manager.hint_engine.detect_distress",
               new=AsyncMock(return_value=False)), \
         patch("services.session_manager.hint_engine.clarify",
               new=AsyncMock(return_value="A clarification.")):
        result = await session_manager.process_clarification(
            db, session, message="what does isolate mean?",
        )

    assert result["clarification"] == "A clarification."
    # We had (limit - 2) existing, added 1, so 1 should remain.
    assert result["remaining"] == 1
    db.add.assert_called_once()
    db.commit.assert_awaited()
