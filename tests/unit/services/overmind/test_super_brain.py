# tests/services/overmind/test_super_brain.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.overmind.domain.cognitive import SuperBrain
from app.services.overmind.domain.context import InMemoryCollaborationContext
from app.models import Mission
from app.core.protocols import AgentPlanner, AgentArchitect, AgentExecutor, AgentReflector

@pytest.mark.asyncio
async def test_super_brain_loop_success():
    # 1. Setup Mocks
    mock_strategist = AsyncMock(spec=AgentPlanner)
    mock_architect = AsyncMock(spec=AgentArchitect)
    mock_operator = AsyncMock(spec=AgentExecutor)
    mock_auditor = AsyncMock(spec=AgentReflector)

    # Configure happy path returns
    mock_strategist.create_plan.return_value = {"steps": ["do_something"]}

    # First review (Plan) -> Approved
    mock_auditor.review_work.side_effect = [
        {"approved": True, "feedback": "Plan Good"}, # Plan Review
        {"approved": True, "feedback": "Execution Good"} # Execution Review
    ]

    mock_architect.design_solution.return_value = {"tasks": [{"id": 1}]}
    mock_operator.execute_tasks.return_value = {"status": "success"}

    brain = SuperBrain(
        strategist=mock_strategist,
        architect=mock_architect,
        operator=mock_operator,
        auditor=mock_auditor
    )

    mission = Mission(id=1, objective="Build a spaceship")

    # 2. Execute
    result = await brain.process_mission(mission)

    # 3. Verify
    assert result == {"status": "success"}

    # Verify collaborative context was passed
    mock_strategist.create_plan.assert_called_once()
    assert isinstance(mock_strategist.create_plan.call_args[0][1], InMemoryCollaborationContext)

    mock_architect.design_solution.assert_called_once()
    mock_operator.execute_tasks.assert_called_once()

    # Auditor called twice (Plan Review + Final Review)
    assert mock_auditor.review_work.call_count == 2

@pytest.mark.asyncio
async def test_super_brain_self_correction():
    # 1. Setup Mocks
    mock_strategist = AsyncMock(spec=AgentPlanner)
    mock_architect = AsyncMock(spec=AgentArchitect)
    mock_operator = AsyncMock(spec=AgentExecutor)
    mock_auditor = AsyncMock(spec=AgentReflector)

    mock_strategist.create_plan.return_value = {"steps": ["bad_plan"]}

    # First review: Reject Plan. Second review: Approve Plan. Third: Approve Execution.
    mock_auditor.review_work.side_effect = [
        {"approved": False, "feedback": "Bad Plan"}, # 1st Plan Review (Fail)
        {"approved": True, "feedback": "Good Plan"},  # 2nd Plan Review (Pass)
        {"approved": True, "feedback": "Done"}        # Final Review
    ]

    mock_architect.design_solution.return_value = {"tasks": []}
    mock_operator.execute_tasks.return_value = {}

    brain = SuperBrain(
        strategist=mock_strategist,
        architect=mock_architect,
        operator=mock_operator,
        auditor=mock_auditor
    )
    brain.state_class = MagicMock() # Mock if needed, or rely on actual pydantic model

    mission = Mission(id=2, objective="Fix bugs")

    # 2. Execute
    await brain.process_mission(mission)

    # 3. Verify
    # Strategist should be called twice (Initial + Re-planning)
    assert mock_strategist.create_plan.call_count == 2

    # Check if context carried the feedback
    call_args_2 = mock_strategist.create_plan.call_args_list[1]
    context_2 = call_args_2[0][1]
    assert context_2.get("feedback_from_previous_attempt") == "Bad Plan"
