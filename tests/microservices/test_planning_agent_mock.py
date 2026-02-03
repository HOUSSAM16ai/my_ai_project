from unittest.mock import patch

import pytest
from pydantic import SecretStr

from microservices.planning_agent.main import _generate_plan
from microservices.planning_agent.settings import PlanningAgentSettings


@pytest.mark.asyncio
async def test_generate_plan_success():
    """Test successful plan generation via Graph."""
    mock_settings = PlanningAgentSettings(
        OPENROUTER_API_KEY=SecretStr("sk-test"),
        AI_MODEL="test-model",
        AI_BASE_URL="http://test/api",
    )

    mock_result = {"plan": ["Step 1", "Step 2"]}

    # Patch the graph object imported in main.py
    with patch("microservices.planning_agent.main.graph") as mock_graph:
        mock_graph.invoke.return_value = mock_result

        steps = await _generate_plan("Learn Python", [], mock_settings)

        assert steps == ["Step 1", "Step 2"]
        mock_graph.invoke.assert_called_once()


@pytest.mark.asyncio
async def test_generate_plan_fallback_on_error():
    """Test fallback when Graph fails."""
    mock_settings = PlanningAgentSettings(OPENROUTER_API_KEY=SecretStr("sk-test"))

    with patch("microservices.planning_agent.main.graph") as mock_graph:
        mock_graph.invoke.side_effect = Exception("Graph Error")

        steps = await _generate_plan("Learn Python", [], mock_settings)

        # Verify fallback steps are returned
        assert len(steps) >= 3
        assert "تحليل هدف" in steps[0]


@pytest.mark.asyncio
async def test_generate_plan_fallback_no_key():
    """Test fallback when no API key is present."""
    mock_settings = PlanningAgentSettings(OPENROUTER_API_KEY=None)

    steps = await _generate_plan("Learn Python", [], mock_settings)

    assert len(steps) >= 3
    assert "تحليل هدف" in steps[0]
