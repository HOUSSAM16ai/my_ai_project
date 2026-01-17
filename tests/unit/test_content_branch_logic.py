import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chat.tools.content import search_content, _normalize_branch

@pytest.mark.asyncio
async def test_normalize_branch():
    assert _normalize_branch("experimental_sciences") == "علوم تجريبية"
    assert _normalize_branch("Math Tech") == "تقني رياضي"
    assert _normalize_branch("لغات") == "لغات أجنبية"
    assert _normalize_branch("unknown") == "unknown"

@pytest.mark.asyncio
async def test_search_content_with_branch_generates_correct_query():
    # Mock session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_session.execute.return_value = mock_result

    # Context manager mock
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None

    with patch("app.services.chat.tools.content.async_session_factory", return_value=mock_session_ctx):
        await search_content(
            q="Probability",
            year=2024,
            set_name="subject_1",
            branch="experimental_sciences"
        )

        # Verify query construction
        args, kwargs = mock_session.execute.call_args
        query_text = str(args[0])
        params = args[1]

        # Check standard params
        assert params["set_name"] == "subject_1"
        assert params["q_full"] == "Probability"

        # Check Branch params
        assert "branch_kw" in params
        assert params["branch_kw"] == "%علوم تجريبية%"

        # Check SQL Logic
        assert "i.title LIKE :branch_kw" in query_text

@pytest.mark.asyncio
async def test_search_content_without_branch():
    # Mock session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_session.execute.return_value = mock_result

    # Context manager mock
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None

    with patch("app.services.chat.tools.content.async_session_factory", return_value=mock_session_ctx):
        await search_content(q="Test")

        args, kwargs = mock_session.execute.call_args
        query_text = str(args[0])
        params = args[1]

        assert "branch_kw" not in params
        assert "i.title LIKE :branch_kw" not in query_text
