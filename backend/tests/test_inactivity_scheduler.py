"""
Tests for the inactivity scheduler.

These are deliberately narrow — a full integration test needs a Postgres
fixture (advisory locks + FOR UPDATE SKIP LOCKED don't work on SQLite). The
narrow tests here pin the obvious failure modes: dialect guard and loop
resilience to a tick exception.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services import inactivity_scheduler


@pytest.mark.asyncio
async def test_tick_noops_on_non_postgres():
    """SQLite (and any other non-PG dialect) must early-return zero."""
    class _FakeDialect:
        name = "sqlite"

    with patch.object(inactivity_scheduler, "engine") as mock_engine, \
         patch.object(inactivity_scheduler, "SessionLocal") as mock_sl:
        mock_engine.dialect = _FakeDialect()
        result = await inactivity_scheduler._tick()
        assert result == 0
        mock_sl.assert_not_called()


@pytest.mark.asyncio
async def test_run_loop_survives_tick_errors():
    """A throwing _tick should be logged but not kill the loop."""
    call_count = 0

    async def flaky_tick():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("simulated tick failure")
        return 0

    async def fake_sleep(_):
        # End the loop by cancelling after we've seen at least two ticks.
        if call_count >= 2:
            raise asyncio.CancelledError()

    with patch.object(inactivity_scheduler, "_tick",
                      new=AsyncMock(side_effect=flaky_tick)), \
         patch("services.inactivity_scheduler.asyncio.sleep",
               new=AsyncMock(side_effect=fake_sleep)):
        with pytest.raises(asyncio.CancelledError):
            await inactivity_scheduler.run()

    assert call_count >= 2, "Loop should have retried after the first failure"
