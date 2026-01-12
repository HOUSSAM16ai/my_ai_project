from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.gateway.circuit_breaker import CircuitBreaker
from app.core.gateway.exceptions import AIAllModelsExhaustedError
from app.core.gateway.mesh import SAFETY_NET_MODEL_ID, NeuralRoutingMesh
from app.core.gateway.node import NeuralNode


# Mock ModelProvider for tests
class ModelProvider:
    ANTHROPIC = "anthropic/claude-3.5-sonnet"
    OPENAI = "openai/gpt-4o"


class TestSuperhumanAIGateway:
    """
    Tests for the Superhuman AI Gateway (Neural Routing Mesh).
    """

    @pytest.mark.asyncio
    async def test_complexity_routing(self):
        """Test that prompts are routed based on cognitive complexity"""
        mock_router = MagicMock()
        mock_router.get_ranked_nodes.return_value = [ModelProvider.ANTHROPIC]

        with patch("app.core.gateway.mesh.get_omni_router", return_value=mock_router):
            client = NeuralRoutingMesh("test_key")

            if ModelProvider.ANTHROPIC not in client.nodes_map:
                client.nodes_map[ModelProvider.ANTHROPIC] = NeuralNode(
                    model_id=ModelProvider.ANTHROPIC,
                    circuit_breaker=CircuitBreaker("Test-Synapse", 5, 30.0),
                )

            client._stream_from_node_with_retry = MagicMock()

            async def mock_stream_gen(*args, **kwargs):
                yield {
                    "choices": [{"delta": {"content": "response"}}],
                }

            client._stream_from_node_with_retry.side_effect = mock_stream_gen

            messages = [{"role": "user", "content": "Explain quantum gravity"}]
            async for _ in client.stream_chat(messages):
                pass

            mock_router.get_ranked_nodes.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test that circuit breaker states are respected"""
        with patch("app.core.gateway.mesh._ai_config") as mock_config:
            mock_config.openrouter_api_key = "test_key"
            client = NeuralRoutingMesh("test_key")

            # Remove Safety Net to force exhaustion error
            if SAFETY_NET_MODEL_ID in client.nodes_map:
                del client.nodes_map[SAFETY_NET_MODEL_ID]

            # Mock node to be open (failing)
            mock_node = MagicMock()
            mock_node.circuit_breaker.allow_request.return_value = False
            mock_node.rate_limit_cooldown_until = 0.0

            # Inject mock node
            client.nodes_map[ModelProvider.OPENAI] = mock_node

            client.omni_router.get_ranked_nodes = MagicMock(return_value=[ModelProvider.OPENAI])

            with pytest.raises(AIAllModelsExhaustedError):
                async for _ in client.stream_chat([{"role": "user", "content": "test"}]):
                    pass

    @pytest.mark.asyncio
    async def test_fallback_chain(self):
        """Test automatic fallback to next provider on failure"""
        with patch("app.core.gateway.mesh._ai_config") as mock_config:
            mock_config.openrouter_api_key = "test_key"
            client = NeuralRoutingMesh("test_key")

            node1 = MagicMock()
            node1.model_id = "fail_model"
            node1.circuit_breaker.allow_request.return_value = True
            node1.rate_limit_cooldown_until = 0.0
            node1.semaphore = AsyncMock()
            node1.semaphore.__aenter__.return_value = None

            node2 = MagicMock()
            node2.model_id = "success_model"
            node2.circuit_breaker.allow_request.return_value = True
            node2.rate_limit_cooldown_until = 0.0
            node2.semaphore = AsyncMock()
            node2.semaphore.__aenter__.return_value = None

            client.nodes_map = {"fail_model": node1, "success_model": node2}
            client._get_prioritized_nodes = MagicMock(return_value=[node1, node2])

            async def side_effect(node, messages):
                if node.model_id == "fail_model":
                    raise ValueError("Fail")
                yield {"choices": [{"delta": {"content": "Success"}}]}

            client._stream_from_node_with_retry = MagicMock(side_effect=side_effect)

            response = []
            async for chunk in client.stream_chat([{"role": "user", "content": "test"}]):
                response.append(chunk)

            assert len(response) > 0
            assert response[0]["choices"][0]["delta"]["content"] == "Success"
