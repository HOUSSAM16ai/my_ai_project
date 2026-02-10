"""Unit tests for content tool logic - aligned with refactored super_search_orchestrator."""

import sys
from unittest.mock import AsyncMock, MagicMock

# Mock external modules BEFORE importing app modules
sys.modules["dspy"] = MagicMock()
sys.modules["llama_index"] = MagicMock()
sys.modules["llama_index.core"] = MagicMock()
sys.modules["llama_index.core.schema"] = MagicMock()
sys.modules["llama_index.core.vector_stores"] = MagicMock()
sys.modules["llama_index.embeddings.huggingface"] = MagicMock()
sys.modules["llama_index.vector_stores.supabase"] = MagicMock()
sys.modules["microservices.research_agent.src.search_engine.query_refiner"] = MagicMock()

import pytest

# Mock content service module
mock_content_service_module = MagicMock()
mock_content_service_instance = AsyncMock()
mock_content_service_module.content_service = mock_content_service_instance
sys.modules["microservices.research_agent.src.content.service"] = mock_content_service_module

# Mock super search module (new location)
mock_super_search_module = MagicMock()
mock_orchestrator_instance = AsyncMock()
mock_super_search_module.SuperSearchOrchestrator.return_value = mock_orchestrator_instance
sys.modules["microservices.research_agent.src.search_engine.super_search"] = (
    mock_super_search_module
)

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
    mock_orchestrator_instance.execute.return_value = "Detailed Report Content"

    results = await content_module.search_content(q="Test Query")

    assert len(results) == 1
    assert results[0]["id"] == "research_report"
    assert results[0]["content"] == "Detailed Report Content"
    mock_orchestrator_instance.execute.assert_called_once()


@pytest.mark.asyncio
async def test_search_content_error_handling():
    """Verify error handling returns error object."""
    mock_orchestrator_instance.execute.side_effect = Exception("Network error")

    results = await content_module.search_content(q="Error Query")

    assert len(results) == 1
    assert results[0]["id"] == "error"
    assert "Network error" in results[0]["content"]


@pytest.mark.asyncio
async def test_get_curriculum_structure():
    """Test curriculum structure retrieval."""
    mock_content_service_instance.get_curriculum_structure.return_value = {
        "3as": {"subjects": []}
    }

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
