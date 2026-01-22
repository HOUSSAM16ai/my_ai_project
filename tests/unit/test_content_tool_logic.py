import sys
from unittest.mock import MagicMock

# Mock dspy BEFORE importing app modules to avoid slow imports/network calls
sys.modules["dspy"] = MagicMock()
sys.modules["app.services.search_engine.query_refiner"] = MagicMock()

import pytest
from unittest.mock import AsyncMock, patch

# Now import the module under test
# We also need to mock content_service import if it triggers DB connections
# content.py imports content_service from app.services.content.service
# app.services.content.service creates a ContentService() instance
# which imports database stuff.

# Let's mock the content_service module entirely to be safe
mock_content_service_module = MagicMock()
mock_content_service_instance = AsyncMock()
mock_content_service_module.content_service = mock_content_service_instance
sys.modules["app.services.content.service"] = mock_content_service_module

# Now we can import the tool safely
from app.services.chat.tools.content import search_content
from app.services.search_engine.fallback_expander import FallbackQueryExpander

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
        q = kwargs.get("q", "")
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
    q = "Complex Search 2024"
    results = await search_content(q=q)

    # Assert
    assert len(results) == 1
    assert results[0]["title"] == "Found It"

    # Verify it was called multiple times
    assert mock_content_service_instance.search_content.call_count >= 2

    # Verify the calls included the stripped version
    calls = mock_content_service_instance.search_content.call_args_list
    queries_tried = [c.kwargs.get("q") for c in calls]

    print(f"Queries tried: {queries_tried}")

    # FallbackExpander removes 2024 as stop word
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
