from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat.graph.nodes.planner import planner_node
from app.services.kagent.domain import AgentResponse


@pytest.mark.asyncio
async def test_planner_node_integration():
    """
    Verify that planner_node attempts to call the microservice via Kagent
    and handles the response correctly.
    """

    # Mock State
    mock_state = {"messages": [MagicMock(content="أريد تعلم البايثون")], "current_step_index": 0}

    # Mock Kagent Mesh
    mock_kagent = AsyncMock()
    mock_kagent.execute_action.return_value = AgentResponse(
        status="success", data={"steps": ["Step 1", "Step 2"]}, metrics={}
    )

    result = await planner_node(mock_state, mock_kagent)

    # Verify result structure
    assert result["next"] == "supervisor"
    assert result["plan"] == ["Step 1", "Step 2"]

    # Verify Kagent was called
    mock_kagent.execute_action.assert_called_once()
    call_args = mock_kagent.execute_action.call_args
    agent_request = call_args[0][0]
    assert agent_request.target_service == "planning_agent"
    assert agent_request.action == "generate_plan"


@pytest.mark.asyncio
async def test_planner_node_fallback():
    """
    Verify that planner_node falls back to default plan
    if the microservice fails via Kagent.
    """

    mock_state = {"messages": [MagicMock(content="Test")], "current_step_index": 0}

    # Mock Kagent Failure
    mock_kagent = AsyncMock()
    mock_kagent.execute_action.return_value = AgentResponse(
        status="error", error="Service Unavailable"
    )

    result = await planner_node(mock_state, mock_kagent)

    # Verify fallback was used (default plan is ["search", "explain"])
    mock_kagent.execute_action.assert_called_once()
    assert result["plan"] == ["search", "explain"]
