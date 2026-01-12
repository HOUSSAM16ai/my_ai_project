
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.chat.agents.base import AgentResponse
from app.services.chat.agents.orchestrator import OrchestratorAgent
from app.services.chat.tools import ToolRegistry


@pytest.mark.asyncio
async def test_orchestrator_agent_user_count():
    # Mock AIClient and ToolRegistry
    mock_ai_client = MagicMock()
    mock_tools = MagicMock(spec=ToolRegistry)
    mock_tools.execute = AsyncMock(return_value=42)

    agent = OrchestratorAgent(mock_ai_client, mock_tools)

    # Mock DataAccessAgent to return success
    agent.data_agent.process = AsyncMock(return_value=AgentResponse(success=True))

    # Test "how many users" query
    response = await agent.run("how many users are there?")

    # Verify tool call
    mock_tools.execute.assert_called_with("get_user_count", {})
    assert "42 users" in response

@pytest.mark.asyncio
async def test_orchestrator_agent_governance_failure():
    # Mock AIClient and ToolRegistry
    mock_ai_client = MagicMock()
    mock_tools = MagicMock(spec=ToolRegistry)

    agent = OrchestratorAgent(mock_ai_client, mock_tools)

    # Mock DataAccessAgent to return failure
    agent.data_agent.process = AsyncMock(return_value=AgentResponse(success=False, message="Denied"))

    # Test query
    response = await agent.run("how many users are there?")

    # Verify tool call was NOT made
    mock_tools.execute.assert_not_called()
    assert "Governance Error" in response

@pytest.mark.asyncio
async def test_orchestrator_agent_search_codebase():
    # Mock AIClient and ToolRegistry
    mock_ai_client = MagicMock()
    mock_tools = MagicMock(spec=ToolRegistry)

    # Mock search results
    mock_results = [
        {"file_path": "app/main.py", "line_number": 10},
        {"file_path": "app/core/config.py", "line_number": 5}
    ]
    mock_tools.execute = AsyncMock(return_value=mock_results)

    agent = OrchestratorAgent(mock_ai_client, mock_tools)

    # Mock RefactorAgent
    agent.refactor_agent.process = AsyncMock(return_value=AgentResponse(success=True))

    # Test search query
    response = await agent.run("find feature XYZ")

    # Verify tool call
    mock_tools.execute.assert_called_once()
    assert "app/main.py" in response
    assert "app/core/config.py" in response
