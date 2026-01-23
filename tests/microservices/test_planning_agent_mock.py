import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from microservices.planning_agent.main import _generate_plan
from microservices.planning_agent.settings import PlanningAgentSettings
from pydantic import SecretStr

@pytest.mark.asyncio
async def test_generate_plan_success():
    """Test successful plan generation via LLM."""
    mock_settings = PlanningAgentSettings(
        OPENROUTER_API_KEY=SecretStr("sk-test"),
        AI_MODEL="test-model",
        AI_BASE_URL="http://test/api"
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '["Step 1", "Step 2"]'

    with patch("microservices.planning_agent.main.AsyncOpenAI") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.chat.completions.create = AsyncMock(return_value=mock_response)

        steps = await _generate_plan("Learn Python", [], mock_settings)

        assert steps == ["Step 1", "Step 2"]
        mock_instance.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_generate_plan_fallback_on_error():
    """Test fallback when LLM fails."""
    mock_settings = PlanningAgentSettings(
        OPENROUTER_API_KEY=SecretStr("sk-test")
    )

    with patch("microservices.planning_agent.main.AsyncOpenAI") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

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
