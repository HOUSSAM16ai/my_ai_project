import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.search_engine import get_retriever, get_refined_query
from app.services.chat.tools.content import search_content

# Mock DSPy
@patch("dspy.LM")
@patch("dspy.configure")
@patch("app.services.search_engine.query_refiner.QueryRefiner")
def test_query_refiner(mock_refiner_cls, mock_configure, mock_lm):
    mock_module = MagicMock()
    mock_module.return_value.refined_query = "refined 2024"
    mock_refiner_cls.return_value = mock_module

    q = get_refined_query("raw query", "key")
    assert q == "refined 2024"

# Mock LlamaIndex Retriever
def test_retriever_init():
    with patch("app.services.search_engine.retriever.SupabaseVectorStore") as mock_vec:
        with patch("app.services.search_engine.retriever.HuggingFaceEmbedding") as mock_embed:
            with patch("app.services.search_engine.retriever.VectorStoreIndex.from_vector_store") as mock_idx:
                retriever = get_retriever("postgres://...")
                assert retriever is not None
                mock_vec.assert_called_once()
                mock_embed.assert_called_once()

# Mock Content Tool Search integration
@pytest.mark.asyncio
async def test_search_content_integration():
    # We mock os.environ to simulate DB_URL presence
    with patch.dict("os.environ", {"DATABASE_URL": "fake_url", "OPENROUTER_API_KEY": "fake_key"}):
        # Mock get_refined_query
        with patch("app.services.chat.tools.content.get_refined_query", return_value="refined q") as mock_refine:
            # Mock get_retriever
            mock_retriever = MagicMock()
            node = MagicMock()
            node.node.metadata = {"content_id": "123"}
            mock_retriever.search.return_value = [node]

            with patch("app.services.chat.tools.content.get_retriever", return_value=mock_retriever):
                # Mock DB session
                with patch("app.services.chat.tools.content.async_session_factory") as mock_factory:
                    mock_session = AsyncMock()
                    # Setup context manager correctly for async call
                    mock_ctx = MagicMock()
                    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
                    mock_ctx.__aexit__ = AsyncMock(return_value=None)
                    mock_factory.return_value = mock_ctx

                    # Mock SQL execute result
                    mock_result = MagicMock()
                    row = MagicMock()
                    row.id = "123"
                    row.title = "Test"
                    row.type = "exercise"
                    row.level = "L1"
                    row.subject = "Math"
                    row.set_name = "S1"
                    row.year = 2024
                    row.lang = "ar"

                    mock_result.fetchall.return_value = [row]
                    mock_session.execute.return_value = mock_result

                    results = await search_content(q="raw query")

                    assert len(results) == 1
                    assert results[0]["id"] == "123"
                    # Verification that semantic path was taken
                    mock_refine.assert_called_once()
