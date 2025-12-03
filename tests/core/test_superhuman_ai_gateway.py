from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.ai_gateway import NeuralRoutingMesh


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
        # Mocking get_ranked_nodes instead of route
        mock_router.get_ranked_nodes.return_value = [ModelProvider.ANTHROPIC]

        # Initialize client with mock
        # Since we can't easily inject the router into NeuralRoutingMesh __init__ without refactoring,
        # we patch get_omni_router
        with patch("app.core.ai_gateway.get_omni_router", return_value=mock_router):
            with patch("app.core.ai_gateway.OPENROUTER_API_KEY", "test_key"):
                client = NeuralRoutingMesh("test_key")

                # Inject the model ID expected by the mock router into the client's node map
                # The client initializes only from config, so we must manually add the test model
                # to the nodes_map to prevent KeyError during the lookup.
                from app.core.ai_gateway import (
                    CIRCUIT_FAILURE_THRESHOLD,
                    CIRCUIT_RECOVERY_TIMEOUT,
                    CircuitBreaker,
                    NeuralNode,
                )

                if ModelProvider.ANTHROPIC not in client.nodes_map:
                    client.nodes_map[ModelProvider.ANTHROPIC] = NeuralNode(
                        model_id=ModelProvider.ANTHROPIC,
                        circuit_breaker=CircuitBreaker(
                            "Test-Synapse", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT
                        ),
                    )

                # Mock internal _stream_from_node to avoid network calls
                client._stream_from_node = MagicMock()

                async def mock_stream_gen(*args, **kwargs):
                    yield {"content": "response"}

                client._stream_from_node.side_effect = mock_stream_gen

                messages = [{"role": "user", "content": "Explain quantum gravity"}]
                async for _ in client.stream_chat(messages):
                    pass

                # Verify router was consulted
                mock_router.get_ranked_nodes.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test that circuit breaker states are respected"""
        with patch("app.core.ai_gateway.OPENROUTER_API_KEY", "test_key"):
            client = NeuralRoutingMesh("test_key")

            # Mock node to be open (failing)
            mock_node = MagicMock()
            mock_node.circuit_breaker.allow_request.return_value = False

            # Inject mock node
            client.nodes_map[ModelProvider.OPENAI] = mock_node

            # If all nodes fail/open, it raises AIAllModelsExhaustedError
            # We need to make sure ALL nodes are failing for the test to pass the "raises" check
            # OR we just check that this specific node wasn't called.

            # Let's try to verify that it skips the open node.
            # We'll mock the router to return ONLY this node.
            client.omni_router.get_ranked_nodes = MagicMock(return_value=[ModelProvider.OPENAI])

            # It should return empty list from _get_prioritized_nodes because the only candidate is OPEN
            # Thus it will raise AIAllModelsExhaustedError (or return empty if handled)

            # Check implementation of stream_chat:
            # priority_nodes = self._get_prioritized_nodes(prompt)
            # if not priority_nodes, loop is skipped.
            # raises AIAllModelsExhaustedError at end.

            from app.core.ai_gateway import AIAllModelsExhaustedError

            with pytest.raises(AIAllModelsExhaustedError):
                async for _ in client.stream_chat([{"role": "user", "content": "test"}]):
                    pass

    @pytest.mark.asyncio
    async def test_fallback_chain(self):
        """Test automatic fallback to next provider on failure"""
        with patch("app.core.ai_gateway.OPENROUTER_API_KEY", "test_key"):
            client = NeuralRoutingMesh("test_key")

            # Setup two nodes: 1 Fail, 1 Success
            node1 = MagicMock()
            node1.model_id = "fail_model"
            node1.circuit_breaker.allow_request.return_value = True
            # semaphore mock
            node1.semaphore = AsyncMock()
            node1.semaphore.__aenter__.return_value = None

            node2 = MagicMock()
            node2.model_id = "success_model"
            node2.circuit_breaker.allow_request.return_value = True
            node2.semaphore = AsyncMock()
            node2.semaphore.__aenter__.return_value = None

            client.nodes_map = {"fail_model": node1, "success_model": node2}

            # Router returns both
            client._get_prioritized_nodes = MagicMock(return_value=[node1, node2])

            # Mock _stream_from_node
            async def stream_fail(*args, **kwargs):
                raise Exception("Fail")
                yield  # unreachable

            async def stream_success(*args, **kwargs):
                yield {"content": "Success"}

            # We need to patch _stream_from_node to behave differently per node
            # Side effect can be a function that checks args
            async def side_effect(node, messages):
                if node.model_id == "fail_model":
                    raise Exception("Fail")
                yield {"content": "Success"}

            client._stream_from_node = MagicMock(side_effect=side_effect)

            response = []
            async for chunk in client.stream_chat([{"role": "user", "content": "test"}]):
                response.append(chunk)

            assert len(response) > 0
            assert response[0]["content"] == "Success"
