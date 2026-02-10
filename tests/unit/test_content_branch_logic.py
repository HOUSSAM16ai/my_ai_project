import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock external modules BEFORE importing app modules to avoid dependency issues
sys.modules["llama_index"] = MagicMock()
sys.modules["llama_index.core"] = MagicMock()
sys.modules["llama_index.core.schema"] = MagicMock()
sys.modules["llama_index.core.vector_stores"] = MagicMock()
sys.modules["llama_index.embeddings.huggingface"] = MagicMock()
sys.modules["llama_index.vector_stores.supabase"] = MagicMock()

import pytest

from app.services.chat.tools.content import _normalize_branch, search_content


@pytest.mark.asyncio
async def test_normalize_branch():
    assert _normalize_branch("experimental_sciences") == "علوم تجريبية"
    assert _normalize_branch("Math Tech") == "تقني رياضي"
    assert _normalize_branch("لغات") == "لغات أجنبية"
    assert _normalize_branch("unknown") == "unknown"


@pytest.mark.asyncio
async def test_search_content_with_branch_generates_correct_query():
    # Mock SuperSearchOrchestrator
    mock_orchestrator = AsyncMock()
    mock_orchestrator.execute.return_value = "Mock Report Content"

    # Mock the class where it is defined, not where it is imported inside the function
    with patch(
        "microservices.research_agent.src.search_engine.super_search.SuperSearchOrchestrator",
        return_value=mock_orchestrator,
    ):
        await search_content(
            q="Probability",
            year=2024,
            set_name="subject_1",
            branch="experimental_sciences",
        )

        # Verify calls
        mock_orchestrator.execute.assert_called_once()
        call_args = mock_orchestrator.execute.call_args[0][0]

        # Verify query construction contains key elements
        assert "Probability" in call_args
        assert "Branch: علوم تجريبية" in call_args
        assert "Year: 2024" in call_args


@pytest.mark.asyncio
async def test_search_content_without_branch():
    # Mock SuperSearchOrchestrator
    mock_orchestrator = AsyncMock()
    mock_orchestrator.execute.return_value = "Mock Report Content"

    with patch(
        "microservices.research_agent.src.search_engine.super_search.SuperSearchOrchestrator",
        return_value=mock_orchestrator,
    ):
        await search_content(q="Test Query")

        # Verify calls
        mock_orchestrator.execute.assert_called_once()
        call_args = mock_orchestrator.execute.call_args[0][0]

        assert "Test Query" in call_args
        assert "Branch:" not in call_args
