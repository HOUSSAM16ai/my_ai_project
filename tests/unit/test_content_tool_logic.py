"""Unit tests for content tool logic - aligned with refactored super_search_orchestrator."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock external modules BEFORE importing app modules
sys.modules["dspy"] = MagicMock()
sys.modules["microservices.research_agent.src.search_engine.query_refiner"] = MagicMock()

# Mock content service module
mock_content_service_module = MagicMock()
mock_content_service_instance = AsyncMock()
mock_content_service_module.content_service = mock_content_service_instance
sys.modules["microservices.research_agent.src.content.service"] = mock_content_service_module

# Mock super orchestrator
mock_super_orchestrator_module = MagicMock()
mock_orchestrator_instance = AsyncMock()
mock_super_orchestrator_module.super_search_orchestrator = mock_orchestrator_instance
sys.modules["microservices.research_agent.src.search_engine.super_orchestrator"] = (
    mock_super_orchestrator_module
)

# Mock graph expander
mock_graph_expander = MagicMock()
mock_graph_expander.enrich_search_with_graph = AsyncMock(side_effect=lambda x, **_kw: x)
sys.modules["microservices.research_agent.src.search_engine.graph_expander"] = mock_graph_expander

# Mock search models
mock_search_models = MagicMock()
mock_search_models.SearchFilters = MagicMock()
mock_search_models.SearchRequest = MagicMock()
sys.modules["microservices.research_agent.src.search_engine.models"] = mock_search_models

# Now import the tool safely
from app.services.chat.tools import content as content_module


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test."""
    mock_orchestrator_instance.reset_mock()
    mock_content_service_instance.reset_mock()


@pytest.mark.asyncio
async def test_search_content_uses_super_orchestrator():
    """Verify that search_content uses super_search_orchestrator."""
    # Setup mock result
    mock_result = MagicMock()
    mock_result.model_dump.return_value = {"id": "123", "title": "Test Result"}
    mock_orchestrator_instance.search.return_value = [mock_result]

    results = await content_module.search_content(q="Test Query")

    assert len(results) == 1
    assert results[0]["title"] == "Test Result"
    mock_orchestrator_instance.search.assert_called_once()


@pytest.mark.asyncio
async def test_search_content_fallback_to_direct_service():
    """When super search returns empty, fallback to direct content_service."""
    mock_orchestrator_instance.search.return_value = []
    mock_content_service_instance.search_content.return_value = [{"id": "fallback"}]

    with patch.object(content_module, "async_session_factory", MagicMock()):
        await content_module.search_content(q="Fallback Query")

    # Should have tried content_service after empty super search
    assert mock_content_service_instance.search_content.called


@pytest.mark.asyncio
async def test_search_content_error_handling():
    """Verify error handling returns empty list gracefully."""
    mock_orchestrator_instance.search.side_effect = Exception("Network error")
    mock_content_service_instance.search_content.side_effect = Exception("DB error")

    results = await content_module.search_content(q="Error Query")

    assert results == []


@pytest.mark.asyncio
async def test_get_curriculum_structure():
    """Test curriculum structure retrieval."""
    mock_content_service_instance.get_curriculum_structure.return_value = {"3as": {"subjects": []}}

    result = await content_module.get_curriculum_structure(level="3as")

    assert "3as" in result
    mock_content_service_instance.get_curriculum_structure.assert_called_with("3as")


@pytest.mark.asyncio
async def test_get_content_raw():
    """Test raw content retrieval."""
    mock_content_service_instance.get_content_raw.return_value = {
        "content": "# Exercise",
        "solution": "# Solution",
    }

    result = await content_module.get_content_raw("ex-123", include_solution=True)

    assert result is not None
    assert "content" in result


@pytest.mark.asyncio
async def test_get_solution_raw():
    """Test solution retrieval."""
    mock_content_service_instance.get_content_raw.return_value = {
        "content": "# Exercise",
        "solution": "# Official Solution",
    }

    result = await content_module.get_solution_raw("ex-123")

    assert result is not None
    assert result["solution_md"] == "# Official Solution"


@pytest.mark.asyncio
async def test_normalize_branch():
    """Test branch normalization logic."""
    # Test matching variant
    result = content_module._normalize_branch("علوم تجريبية")
    # Should return a normalized label
    assert result is not None

    # Test None input
    assert content_module._normalize_branch(None) is None

    # Test empty string
    assert content_module._normalize_branch("") is None
