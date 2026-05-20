"""
PR 7 — Tests for the alerts table refactor.

Targets the dedup-by-(session, reason_kind) behavior in session_manager and
the severity mapping in the Alert model. Endpoint-level tests would need a
real DB fixture; not included here (consistent with the rest of this repo's
backend test layout).
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from models.alert import (
    REASON_DISTRESS,
    REASON_INACTIVITY,
    REASON_LEGACY,
    REASON_REPEATED_FAILURE,
    SEVERITY_FOR_REASON,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from services import session_manager


def test_severity_mapping_is_stable():
    """Severity bindings are part of the contract — guard against accidental change."""
    assert SEVERITY_FOR_REASON[REASON_DISTRESS] == SEVERITY_HIGH
    assert SEVERITY_FOR_REASON[REASON_REPEATED_FAILURE] == SEVERITY_MEDIUM
    assert SEVERITY_FOR_REASON[REASON_INACTIVITY] == SEVERITY_LOW
    assert SEVERITY_FOR_REASON[REASON_LEGACY] == SEVERITY_MEDIUM


def _make_db_with_existing_alert(existing_alert) -> AsyncMock:
    """
    Build an AsyncMock that mimics an AsyncSession returning `existing_alert`
    from the first execute() call (the dedup query).
    """
    db = AsyncMock()
    result = MagicMock()
    scalars = MagicMock()
    scalars.first.return_value = existing_alert
    result.scalars.return_value = scalars
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.mark.asyncio
async def test_trigger_alert_dedups_same_reason_kind():
    """If an unresolved alert of the same kind exists, _trigger_alert is a no-op."""
    session = MagicMock(id=uuid4(), student_id=uuid4())
    existing = MagicMock(id=uuid4())  # any non-None row
    db = _make_db_with_existing_alert(existing)

    with patch("services.session_manager.alert_service.notify_teacher",
               new=AsyncMock()) as notify:
        await session_manager._trigger_alert(
            db, session,
            reason_kind=REASON_REPEATED_FAILURE,
            reason_text="stuck",
        )

    # Should NOT have added a new alert or called notify.
    db.add.assert_not_called()
    notify.assert_not_awaited()


@pytest.mark.asyncio
async def test_trigger_alert_inserts_and_notifies_when_no_existing():
    """No existing alert of this kind → insert + notify."""
    session = MagicMock(id=uuid4(), student_id=uuid4())
    db = _make_db_with_existing_alert(existing_alert=None)

    with patch("services.session_manager.alert_service.notify_teacher",
               new=AsyncMock()) as notify:
        await session_manager._trigger_alert(
            db, session,
            reason_kind=REASON_DISTRESS,
            reason_text="Student said 'I give up'",
        )

    db.add.assert_called_once()
    db.commit.assert_awaited()
    notify.assert_awaited_once()
    # Legacy boolean still gets flipped for backward compat.
    assert session.teacher_alerted is True
