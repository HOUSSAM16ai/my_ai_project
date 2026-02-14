from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import reasoning agent components
from microservices.reasoning_agent.src.remote_retriever import RemoteKnowledgeGraphRetriever


@pytest.mark.asyncio
async def test_remote_retriever_calls_api():
    """Verify RemoteKnowledgeGraphRetriever makes correct API call."""
    with patch("httpx.AsyncClient") as mock_client:
        # The instance returned by context manager
        mock_instance = mock_client.return_value.__aenter__.return_value

        # Setup the response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "data": [{"text": "Test Node", "metadata": {"id": "1"}, "score": 0.9}],
        }

        # Configure post to be an async method that returns the response
        mock_instance.post = AsyncMock(return_value=mock_response)

        retriever = RemoteKnowledgeGraphRetriever()
        nodes = await retriever.aretrieve("test query")

        assert len(nodes) == 1
        assert nodes[0].text == "Test Node"
        assert nodes[0].score == 0.9

        # Verify call arguments
        mock_instance.post.assert_called_once()
        args, kwargs = mock_instance.post.call_args
        assert "http://research-agent:8000/execute" in args[0]
        assert kwargs["json"]["action"] == "retrieve_knowledge_graph"
        assert kwargs["json"]["payload"]["query"] == "test query"
