from unittest.mock import AsyncMock, patch

import pytest

from app.core.domain.models import Mission, MissionStatus
from app.services.overmind.domain.cognitive import SuperBrain
from app.services.overmind.executor import TaskExecutor
from app.services.overmind.factory import create_overmind
from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.state import MissionStateManager


@pytest.fixture
def mock_db_session():
    return AsyncMock()


@pytest.fixture
def mock_state_manager():
    manager = AsyncMock(spec=MissionStateManager)
    manager.update_mission_status = AsyncMock()
    manager.complete_mission = AsyncMock()
    manager.log_event = AsyncMock()
    return manager


@pytest.fixture
def mock_executor():
    return AsyncMock(spec=TaskExecutor)


@pytest.fixture
def mock_brain():
    brain = AsyncMock(spec=SuperBrain)
    brain.process_mission = AsyncMock(return_value={"result": "success"})
    return brain


@pytest.mark.asyncio
async def test_overmind_orchestrator_run_mission_success(
    mock_state_manager, mock_executor, mock_brain
):
    """
    Test that the orchestrator successfully runs the SuperBrain loop.
    """
    mission = Mission(id=1, status=MissionStatus.PENDING, objective="Test Mission")
    mock_state_manager.get_mission.return_value = mission

    orchestrator = OvermindOrchestrator(
        state_manager=mock_state_manager, executor=mock_executor, brain=mock_brain
    )

    await orchestrator.run_mission(mission_id=1)

    # Verification
    mock_state_manager.get_mission.assert_called_with(1)
    mock_state_manager.update_mission_status.assert_any_call(
        1, MissionStatus.RUNNING, "Council of Wisdom Convening"
    )
    mock_brain.process_mission.assert_called_once()

    # We now call complete_mission instead of update_mission_status for success
    mock_state_manager.complete_mission.assert_called_once()
    args, kwargs = mock_state_manager.complete_mission.call_args
    assert args[0] == 1  # mission_id
    assert kwargs['result_json'] == {"result": "success"}


@pytest.mark.asyncio
async def test_overmind_orchestrator_run_mission_not_found(
    mock_state_manager, mock_executor, mock_brain
):
    """
    Test that the orchestrator handles non-existent missions gracefully.
    """
    mock_state_manager.get_mission.return_value = None

    orchestrator = OvermindOrchestrator(
        state_manager=mock_state_manager, executor=mock_executor, brain=mock_brain
    )

    await orchestrator.run_mission(mission_id=999)

    mock_state_manager.get_mission.assert_called_with(999)
    mock_brain.process_mission.assert_not_called()


@pytest.mark.asyncio
async def test_overmind_orchestrator_run_mission_failure(
    mock_state_manager, mock_executor, mock_brain
):
    """
    Test that the orchestrator handles catastrophic brain failures.
    """
    mission = Mission(id=1, status=MissionStatus.PENDING)
    mock_state_manager.get_mission.return_value = mission
    mock_brain.process_mission.side_effect = Exception("Brain Melt")

    orchestrator = OvermindOrchestrator(
        state_manager=mock_state_manager, executor=mock_executor, brain=mock_brain
    )

    await orchestrator.run_mission(mission_id=1)

    mock_state_manager.update_mission_status.assert_called_with(
        1, MissionStatus.FAILED, "Cognitive Error: Brain Melt"
    )


@pytest.mark.asyncio
async def test_overmind_factory_assembly(mock_db_session):
    """
    Test that the factory correctly assembles the Overmind components.
    """
    with (
        patch("app.services.overmind.factory.get_ai_client"),
        patch("app.services.overmind.factory.get_registry"),
        patch("app.services.overmind.factory.MissionStateManager"),
        patch("app.services.overmind.factory.TaskExecutor"),
        patch("app.services.overmind.factory.StrategistAgent") as mock_strat,
        patch("app.services.overmind.factory.ArchitectAgent"),
        patch("app.services.overmind.factory.OperatorAgent"),
        patch("app.services.overmind.factory.AuditorAgent"),
        patch("app.services.overmind.factory.SuperBrain") as mock_brain_cls,
    ):
        mock_db = AsyncMock()
        orchestrator = await create_overmind(mock_db)

        assert isinstance(orchestrator, OvermindOrchestrator)
        mock_brain_cls.assert_called_once()
        mock_strat.assert_called_once()
