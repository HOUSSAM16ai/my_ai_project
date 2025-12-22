# tests/services/overmind/test_super_agent.py
# =================================================================================================
# TEST: SUPER AGENT ARCHITECTURE (SOLID/CS50)
# =================================================================================================

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.overmind.orchestrator import OvermindOrchestrator
from app.services.overmind.domain.cognitive import SuperBrain
from app.models import Mission, MissionStatus, Task, TaskStatus

@pytest.fixture
def mock_state_manager():
    state = AsyncMock()
    # Mock mission retrieval
    mission = Mission(id=1, objective="Build a pyramid", status=MissionStatus.PENDING)
    state.get_mission.return_value = mission

    # Mock status updates to change mission state sequentially
    async def update_status_side_effect(mission_id, status, message=None):
        mission.status = status
    state.update_mission_status.side_effect = update_status_side_effect

    # Mock tasks
    state.get_tasks.return_value = []

    return state

@pytest.fixture
def mock_executor():
    executor = AsyncMock()
    executor.execute_task.return_value = {"status": "success", "result_text": "Done"}
    return executor

@pytest.fixture
def mock_planner():
    planner = AsyncMock()
    planner.create_plan.return_value = {
        "objective": "Build a pyramid",
        "steps": [{"id": 1, "action": "lay_foundation"}],
        "meta": {"source": "MockPlanner"}
    }
    return planner

@pytest.fixture
def mock_reflector():
    reflector = AsyncMock()
    # First critique approves it
    reflector.critique_plan.return_value = {"approved": True, "feedback": "Solid plan."}
    return reflector

@pytest.mark.asyncio
async def test_super_agent_lifecycle(mock_state_manager, mock_executor, mock_planner, mock_reflector):
    """
    Verifies the full Cognitive Loop:
    Observe -> Think (Plan + Critique) -> Act (Execute) -> Reflect
    """
    orchestrator = OvermindOrchestrator(
        state_manager=mock_state_manager,
        executor=mock_executor,
        planner=mock_planner,
        reflector=mock_reflector
    )

    # Lifecycle Simulation via side effects
    m_pending = Mission(id=1, objective="Test", status=MissionStatus.PENDING)
    m_planned = Mission(id=1, objective="Test", status=MissionStatus.PLANNED)
    m_running = Mission(id=1, objective="Test", status=MissionStatus.RUNNING)
    m_success = Mission(id=1, objective="Test", status=MissionStatus.SUCCESS)

    # Prepend PENDING for the initial check in run_mission
    mock_state_manager.get_mission.side_effect = [
        m_pending,  # Initial check
        m_pending,  # Cycle 0
        m_planned,  # Cycle 1
        m_running,  # Cycle 2
        m_success,  # Cycle 3
        None
    ]

    # Mock tasks for the monitoring phase
    task1 = Task(id=1, mission_id=1, status=TaskStatus.SUCCESS, task_key="1", tool_name="test")
    mock_state_manager.get_tasks.return_value = [task1]

    await orchestrator.run_mission(1)

    # Verification
    mock_planner.create_plan.assert_awaited_once()
    mock_reflector.critique_plan.assert_awaited_once()
    mock_state_manager.persist_plan.assert_awaited_once()
    assert mock_state_manager.persist_plan.call_args[1]['planner_name'] == "SuperBrain"
    assert mock_state_manager.update_mission_status.call_count >= 1

@pytest.mark.asyncio
async def test_super_agent_self_correction(mock_state_manager, mock_executor, mock_planner, mock_reflector):
    """
    Verifies that the agent handles critique rejection (Self-Correction).
    """
    orchestrator = OvermindOrchestrator(
        state_manager=mock_state_manager,
        executor=mock_executor,
        planner=mock_planner,
        reflector=mock_reflector
    )

    # Critique rejects first, then approves
    mock_reflector.critique_plan.side_effect = [
        {"approved": False, "feedback": "Too risky."},
        {"approved": True, "feedback": "Better."}
    ]

    m_pending = Mission(id=1, objective="Risky", status=MissionStatus.PENDING)
    # We only need the first cycle to test the Thinking phase logic
    mock_state_manager.get_mission.side_effect = [m_pending, m_pending, None]

    await orchestrator.run_mission(1)

    # Verify that plan was called twice (initial + retry)
    assert mock_planner.create_plan.call_count == 2

    # Verify persistence of the approved plan
    mock_state_manager.persist_plan.assert_awaited_once()
    args, kwargs = mock_state_manager.persist_plan.call_args
    assert kwargs['plan_schema']['meta']['status'] == "approved"
