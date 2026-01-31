from unittest.mock import AsyncMock, MagicMock

import pytest

from microservices.research_agent.src.content.service import ContentService


@pytest.mark.asyncio
async def test_content_service_search_logic():
    """
    Verify that ContentService generates the correct SQL query parameters.
    This tests the Service and Repository layer directly, bypassing the Tool wrapper.
    """
    # Create the Mock Session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_session.execute.return_value = mock_result

    # Create the Mock Factory
    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__.return_value = mock_session
    mock_factory.return_value.__aexit__.return_value = None

    # Inject Mock Factory into Service
    service = ContentService(session_factory=mock_factory)

    # Test 1: Simple Search
    await service.search_content(q="Math 2024", limit=5)

    assert mock_session.execute.called
    args, _ = mock_session.execute.call_args
    sql = str(args[0])
    params = args[1]

    # Check SQL structure
    assert "SELECT" in sql
    assert "FROM content_items i" in sql
    assert "LEFT JOIN content_search cs" in sql

    # Check Params
    assert params["tq_0"] == "%Math%"
    assert params["bq_0"] == "%Math%"
    assert params["tq_1"] == "%2024%"
    assert params["limit"] == 5

    # Check Logic
    assert "i.title LIKE :tq_0" in sql
    assert "cs.plain_text LIKE :bq_0" in sql

    # Test 2: Branch Filter
    mock_session.reset_mock()
    mock_session.execute.return_value = mock_result

    await service.search_content(branch="experimental_sciences")

    assert mock_session.execute.called
    args, _ = mock_session.execute.call_args
    sql = str(args[0])
    params = args[1]

    # Should be normalized
    assert params["branch"] == "experimental_sciences"
    assert "i.branch = :branch" in sql
