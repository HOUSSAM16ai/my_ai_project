import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.chat.tools.content import search_content

@pytest.mark.asyncio
async def test_search_content_query_generation():
    """
    Verify that search_content generates the correct SQL query parameters
    and handles keyword splitting correctly.
    """
    # Mock the session factory and session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [] # Return empty for this test
    mock_session.execute.return_value = mock_result

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None

    with patch("app.services.chat.tools.content.async_session_factory", mock_factory):
        # Test 1: Simple Search
        await search_content(q="Math 2024", limit=5)

        # Verify call args
        args, kwargs = mock_session.execute.call_args
        sql = str(args[0])
        params = args[1]

        # Check SQL structure
        assert "SELECT i.id, i.title" in sql
        assert "FROM content_items i" in sql
        assert "LEFT JOIN content_search cs" in sql

        # Check Params (Updated keys for body/title split)
        # title query keys: tq_0, tq_1
        # body query keys: bq_0, bq_1
        assert "tq_0" in params
        assert "bq_0" in params
        assert params["tq_0"] == "%Math%"
        assert params["bq_0"] == "%Math%"

        assert params["tq_1"] == "%2024%"
        assert params["limit"] == 5

        # Check Logic (Hybrid)
        assert "title LIKE :tq_0" in sql
        assert "cs.plain_text LIKE :bq_0" in sql

        print("Test passed!")
