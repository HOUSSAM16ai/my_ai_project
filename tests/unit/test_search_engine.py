import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.search_engine.retriever import ContentRetriever
from llama_index.core.schema import NodeWithScore, TextNode

@pytest.mark.asyncio
async def test_retriever_fallback_logic():
    # Mock the singleton initialization to avoid loading real models
    with patch("app.services.search_engine.retriever.ContentRetriever._initialize") as mock_init:
        # Mock get_content_service
        with patch("app.services.search_engine.retriever.get_content_service") as mock_get_service:
            mock_content_service = AsyncMock()
            mock_get_service.return_value = mock_content_service

            # Reset singleton instance
            ContentRetriever._instance = None

            # Setup ContentRetriever
            retriever = ContentRetriever()
            # Force _ready to False to trigger fallback immediately
            retriever._ready = False

            # Mock SQL results
            mock_item = MagicMock()
            mock_item.title = "Test Doc"
            mock_item.id = "123"
            mock_item.year = 2024
            mock_item.subject = "Math"

            mock_content_service.search_content.return_value = [mock_item]

            # Test retrieve
            results = await retriever.retrieve("query", filters={"year": 2024})

            assert len(results) == 1
            assert results[0].node.metadata["title"] == "Test Doc"
            assert results[0].node.metadata["source"] == "sql_fallback"

            # Verify SQL service called
            mock_content_service.search_content.assert_called_once()
