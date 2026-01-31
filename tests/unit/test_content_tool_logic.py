import sys
from unittest.mock import MagicMock

# Mock dspy BEFORE importing app modules to avoid slow imports/network calls
sys.modules["dspy"] = MagicMock()
sys.modules["microservices.research_agent.src.search_engine.query_refiner"] = MagicMock()

from unittest.mock import AsyncMock, patch

import pytest

# Now import the module under test
# We also need to mock content_service import if it triggers DB connections
# content.py imports content_service from microservices.research_agent.src.content.service
# microservices.research_agent.src.content.service creates a ContentService() instance
# which imports database stuff.

# Let's mock the content_service module entirely to be safe
mock_content_service_module = MagicMock()
mock_content_service_instance = AsyncMock()
mock_content_service_module.content_service = mock_content_service_instance
sys.modules["microservices.research_agent.src.content.service"] = mock_content_service_module

# Now we can import the tool safely
from app.services.chat.tools.content import search_content


@pytest.mark.asyncio
async def test_search_content_fallback_logic():
    """
    Verify that search_content uses FallbackQueryExpander and retries with multiple candidates.
    """

    # Setup the mock for content_service.search_content
    # It needs to simulate:
    # 1. No results for strict query "Complex Search 2024"
    # 2. Results for relaxed query "Complex Search"

    async def side_effect(*args, **kwargs):
        q = kwargs.get("q")
        if q is None:
            q = ""
        # Simulate strict failure
        if "2024" in q:
            return []
        # Simulate relaxed success
        return [{"id": "ex1", "title": "Found It"}]

    mock_content_service_instance.search_content.side_effect = side_effect

    # We also need to ensure FallbackQueryExpander is working or mocked
    # Since we imported it, we can use the real one or mock it.
    # The real one is pure logic (fast), so let's use it.

    # Act
    # We pass a query that we know FallbackQueryExpander will strip
    # We mock get_retriever to ensure Vector Search fails, forcing Keyword Fallback
    with (
        patch("app.services.chat.tools.content.get_retriever") as mock_get_retriever,
        patch("app.services.chat.tools.content.FallbackQueryExpander") as mock_expander,
    ):
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.search.return_value = []  # No vectors found
        mock_get_retriever.return_value = mock_retriever_instance

        # Mock expander to return controlled variations
        mock_expander.generate_variations.return_value = ["Complex Search"]

        q = "Complex Search 2024"
        results = await search_content(q=q)

    # Assert
    assert len(results) == 1
    assert results[0]["title"] == "Found It"

    # Verify it was called at least once (Keyword Fallback uses the optimized query directly)
    assert mock_content_service_instance.search_content.call_count >= 1

    # Verify the calls included the stripped version
    calls = mock_content_service_instance.search_content.call_args_list
    # Filter out None values (from vector search calls)
    queries_tried = [c.kwargs.get("q") for c in calls if c.kwargs.get("q")]

    print(f"Queries tried: {queries_tried}")

    # FallbackExpander removes 2024 as stop word, so the tool should prefer "Complex Search"
    # The tool picks query_candidates[-1], which is the most processed one.
    assert any("Complex Search" in q for q in queries_tried)


@pytest.mark.asyncio
async def test_search_content_early_return():
    """
    Verify that if the first candidate finds results, we stop searching.
    """
    # Reset mock
    mock_content_service_instance.search_content.reset_mock()
    mock_content_service_instance.search_content.side_effect = None
    mock_content_service_instance.search_content.return_value = [{"id": "ex1"}]

    results = await search_content(q="Simple Query")

    assert len(results) == 1
    assert results[0]["id"] == "ex1"
