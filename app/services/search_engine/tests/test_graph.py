import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.search_engine.graph import search_graph
from app.services.search_engine.retriever import ContentRetriever
from llama_index.core.schema import NodeWithScore, TextNode

@pytest.mark.asyncio
async def test_search_graph_flow():
    """
    Test the LangGraph flow with mocked retrieval.
    """
    # Mock Retrieve Node output
    mock_retriever = MagicMock()
    mock_node = NodeWithScore(
        node=TextNode(text="Test Content", metadata={"year": 2024, "subject": "Math"}),
        score=0.9
    )
    # Mock retrieve to return a list of NodeWithScore
    mock_retriever.retrieve = AsyncMock(return_value=[mock_node])

    with patch("app.services.search_engine.graph.get_retriever", return_value=mock_retriever):
        state = {
            "query": "test query",
            "filters": {"year": 2024},
            "documents": [],
            "answer": ""
        }

        result = await search_graph.ainvoke(state)

        assert "documents" in result
        assert len(result["documents"]) == 1
        assert "Test Content" in result["documents"][0]
        assert "answer" in result
        assert "Test Content" in result["answer"] # Simple generation just joins docs

@pytest.mark.asyncio
async def test_search_graph_empty():
    """Test graph with no results."""
    mock_retriever = MagicMock()
    mock_retriever.retrieve = AsyncMock(return_value=[])

    with patch("app.services.search_engine.graph.get_retriever", return_value=mock_retriever):
        state = {
            "query": "impossible query",
            "documents": [],
            "answer": ""
        }

        result = await search_graph.ainvoke(state)
        assert result["documents"] == []
        assert "could not find" in result["answer"]
