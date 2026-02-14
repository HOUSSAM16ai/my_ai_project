import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

# Mock heavy dependencies BEFORE importing modules that use them
sys.modules["app.services.overmind.factory"] = MagicMock()
sys.modules["llama_index"] = MagicMock()
sys.modules["llama_index.core"] = MagicMock()
sys.modules["llama_index.core.schema"] = MagicMock()


from app.core.domain.mission import MissionEvent, MissionEventType, MissionStatus
from app.services.overmind.entrypoint import start_mission
from app.services.overmind.state import MissionStateManager


@pytest.mark.asyncio
async def test_start_mission_success(db_session):
    """
    Verifies that start_mission creates a mission, logs the event, and triggers background task.
    """
    session = db_session
    # Mock Redis Lock
    with patch("app.services.overmind.entrypoint.redis.from_url") as mock_redis:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()

        mock_lock = AsyncMock()
        mock_lock.acquire.return_value = True
        mock_client.lock.return_value = mock_lock
        mock_redis.return_value = mock_client

        # Mock background task spawning to avoid real execution logic (which needs heavy dependencies)
        with patch("app.services.overmind.entrypoint.asyncio.create_task") as mock_task:
            mission = await start_mission(
                session=session,
                objective="Test Unified Control Plane",
                initiator_id=1,
                context={"test": True},
                idempotency_key="unique-key-123",
            )

            # 1. Verify DB Creation
            assert mission.id is not None
            assert mission.objective == "Test Unified Control Plane"
            assert mission.status == MissionStatus.PENDING
            assert mission.idempotency_key == "unique-key-123"

            # 2. Verify Event Log
            stmt = select(MissionEvent).where(MissionEvent.mission_id == mission.id)
            result = await session.execute(stmt)
            events = result.scalars().all()

            assert len(events) >= 1
            assert events[0].event_type == MissionEventType.STATUS_CHANGE
            assert events[0].payload_json.get("status") == "starting"

            # 3. Verify Execution Trigger
            mock_task.assert_called_once()

            # Verify Redis Lock Release
            mock_lock.release.assert_called_once()
            mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_start_mission_idempotency(db_session):
    """
    Verifies that start_mission returns existing mission for same idempotency key.
    """
    session = db_session
    key = "idempotent-key-999"

    with patch("app.services.overmind.entrypoint.redis.from_url") as mock_redis:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_lock = AsyncMock()
        mock_lock.acquire.return_value = True
        mock_client.lock.return_value = mock_lock
        mock_redis.return_value = mock_client

        with patch("app.services.overmind.entrypoint.asyncio.create_task") as mock_task:
            # First Call
            m1 = await start_mission(session, "Obj", 1, idempotency_key=key)

            # Second Call
            m2 = await start_mission(session, "Obj", 1, idempotency_key=key)

            assert m1.id == m2.id
            # Should not trigger task twice if we handled it correctly (logic: if status != PENDING return)
            # But here status is PENDING.
            # Ideally create_mission returns existing object.
            # Logic in entrypoint:
            # mission = await create_mission(...) -> returns existing
            # if mission.status != PENDING: return
            # Here status IS pending (since first task mocked, didn't update status).
            # So it proceeds to lock.
            # Lock acquires (mocked True).
            # Triggers task again.

            # To strictly test "No Double Trigger", we need status update.
            # Let's manually update status of m1
            m1.status = MissionStatus.RUNNING
            await session.commit()

            # Third Call
            m3 = await start_mission(session, "Obj", 1, idempotency_key=key)
            assert m3.id == m1.id
            # Check mocks. First call triggered. Second call triggered (because status was pending). Third call should NOT trigger.
            # So call count should be 2.
            assert mock_task.call_count == 2


@pytest.mark.asyncio
async def test_strict_state_transitions(db_session):
    """
    Verifies that invalid state transitions raise an error.
    """
    session = db_session
    sm = MissionStateManager(session)
    mission = await sm.create_mission("Strict Test", 1)

    # Valid: PENDING -> RUNNING
    await sm.update_mission_status(mission.id, MissionStatus.RUNNING)
    assert mission.status == MissionStatus.RUNNING

    # Invalid: RUNNING -> PENDING (Not allowed)
    with pytest.raises(ValueError, match="Invalid Mission Transition"):
        await sm.update_mission_status(mission.id, MissionStatus.PENDING)


@pytest.mark.asyncio
async def test_start_mission_locked(db_session):
    """
    Verifies that if lock is acquired by another process, we skip execution trigger.
    """
    session = db_session
    with patch("app.services.overmind.entrypoint.redis.from_url") as mock_redis:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()

        mock_lock = AsyncMock()
        mock_lock.acquire.return_value = False  # Simulate Locked
        mock_client.lock.return_value = mock_lock
        mock_redis.return_value = mock_client

        with patch("app.services.overmind.entrypoint.asyncio.create_task") as mock_task:
            mission = await start_mission(session=session, objective="Test Locked", initiator_id=1)

            assert mission.id is not None
            mock_task.assert_not_called()
            mock_client.close.assert_called_once()
