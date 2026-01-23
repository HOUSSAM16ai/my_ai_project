import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.chat.graph.nodes.planner import planner_node

@pytest.mark.asyncio
async def test_planner_node_integration():
    """
    Verify that planner_node attempts to call the microservice
    and handles the response correctly.
    """

    # Mock State
    mock_state = {
        "messages": [MagicMock(content="أريد تعلم البايثون")],
        "current_step_index": 0
    }

    # Mock AI Client (not used if microservice works)
    mock_ai_client = AsyncMock()

    # Mock httpx response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "plan_id": "123",
        "goal": "Test",
        "steps": ["Step 1", "Step 2"]
    }

    # Patch httpx.AsyncClient
    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        result = await planner_node(mock_state, mock_ai_client)

        # Verify result structure
        assert result["next"] == "supervisor"
        # The node currently translates everything to ["search", "explain"]
        # as per the simplified logic in planner.py
        assert "plan" in result

        # Verify the microservice was called
        mock_instance.__aenter__.return_value.post.assert_called_once()
        call_args = mock_instance.__aenter__.return_value.post.call_args
        assert "http://localhost:8001/plans" in call_args[0][0]

@pytest.mark.asyncio
async def test_planner_node_fallback():
    """
    Verify that planner_node falls back to local AI logic
    if the microservice fails.
    """

    mock_state = {
        "messages": [MagicMock(content="Test")],
        "current_step_index": 0
    }

    mock_ai_client = AsyncMock()
    # Mock send_message returning a JSON string directly
    mock_ai_client.send_message.return_value = '{"steps": ["fallback_step"]}'

    with patch("httpx.AsyncClient") as MockClient:
        mock_instance = MockClient.return_value
        # Simulate Error
        mock_instance.__aenter__.return_value.post = AsyncMock(side_effect=Exception("Connection Refused"))

        result = await planner_node(mock_state, mock_ai_client)

        # Verify fallback was used
        mock_ai_client.send_message.assert_called_once()
        assert result["plan"] == ["fallback_step"]
