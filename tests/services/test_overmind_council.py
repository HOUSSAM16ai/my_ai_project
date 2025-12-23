import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models import Mission, MissionStatus, Task, TaskStatus

# We import the class, but we must patch where it is USED or where it imports the dependency.
# Since get_registry is imported inside orchestrator.py or at module level, we patch it there.
from app.services.overmind.orchestrator import OvermindOrchestrator

@pytest.mark.asyncio
@patch("app.services.overmind.orchestrator.get_registry")
async def test_council_collaboration_flow(mock_get_registry):
    """
    اختبار تدفق تعاون مجلس الحكماء.
    Verifies that Strategist, Architect, Auditor, and Operator work together.
    """
    # Setup Registry Mock
    mock_registry_instance = MagicMock()
    mock_get_registry.return_value = mock_registry_instance

    # 1. Setup Mocks
    mock_state_manager = AsyncMock()
    mock_ai_client = AsyncMock()

    # Mock Mission Data
    mission = Mission(
        id=1,
        objective="Build a Python script for Fibonacci",
        status=MissionStatus.PENDING
    )

    # Mock State Manager returns
    mock_state_manager.get_mission.return_value = mission
    mock_state_manager.get_tasks.return_value = []

    # Create Orchestrator
    orchestrator = OvermindOrchestrator(mock_state_manager, mock_ai_client)

    # Mock Agents interactions
    orchestrator.brain.planner.create_plan = AsyncMock(return_value={
        "steps": [{"step_id": 1, "name": "Write Code", "tool": "write_file"}],
        "approved": True
    })
    orchestrator.brain.architect.design_solution = AsyncMock(return_value={
        "blueprint": {"files": ["fib.py"]}
    })
    orchestrator.brain.reflector.critique_plan = AsyncMock(return_value={
        "valid": True, "feedback": "Approved"
    })

    # 2. Run Planning Phase
    await orchestrator._phase_planning(mission)

    # 3. Verify Council Interactions
    orchestrator.brain.planner.create_plan.assert_awaited_once()
    orchestrator.brain.architect.design_solution.assert_awaited_once()
    orchestrator.brain.reflector.critique_plan.assert_awaited_once()

    mock_state_manager.persist_plan.assert_awaited_once()

@pytest.mark.asyncio
@patch("app.services.overmind.orchestrator.get_registry")
async def test_council_rejection_flow(mock_get_registry):
    """
    اختبار رفض المجلس للخطة.
    """
    mock_registry_instance = MagicMock()
    mock_get_registry.return_value = mock_registry_instance

    mock_state_manager = AsyncMock()
    mission = Mission(id=2, objective="Bad Objective", status=MissionStatus.PENDING)

    orchestrator = OvermindOrchestrator(mock_state_manager, None)

    # Mock Auditor Rejection
    orchestrator.brain.planner.create_plan = AsyncMock(return_value={"steps": []})
    orchestrator.brain.architect.design_solution = AsyncMock(return_value={})
    orchestrator.brain.reflector.critique_plan = AsyncMock(return_value={
        "valid": False, "feedback": "Too dangerous"
    })

    await orchestrator._phase_planning(mission)

    # Verify mission failed
    args, _ = mock_state_manager.update_mission_status.call_args
    assert args[0] == 2
    assert args[1] == MissionStatus.FAILED
    assert "Plan Rejected" in args[2]

@pytest.mark.asyncio
@patch("app.services.overmind.orchestrator.get_registry")
async def test_execution_oversight(mock_get_registry):
    """
    اختبار الرقابة على التنفيذ.
    """
    mock_registry_instance = MagicMock()
    mock_get_registry.return_value = mock_registry_instance

    mock_state_manager = AsyncMock()
    orchestrator = OvermindOrchestrator(mock_state_manager, None)

    task = MagicMock()
    task.id = 101
    task.tool_name = "test_tool"

    # Mock Execution Success
    orchestrator.brain.executor.execute_task = AsyncMock(return_value={"status": "success"})
    orchestrator.brain.reflector.verify_execution = AsyncMock(return_value={"verified": True})

    await orchestrator._execute_single_task(task, mission_id=1)

    mock_state_manager.mark_task_complete.assert_awaited_once()
    orchestrator.brain.reflector.verify_execution.assert_awaited_once()
