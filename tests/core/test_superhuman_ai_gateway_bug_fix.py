from unittest.mock import MagicMock, patch

import pytest

from app.core.ai_gateway import (
    CIRCUIT_FAILURE_THRESHOLD,
    CIRCUIT_RECOVERY_TIMEOUT,
    CircuitBreaker,
    NeuralNode,
    NeuralRoutingMesh,
)


class TestGatewayBugFix:
    """
    Verifies the fix for the bug where incorrect mock structure caused
    AIAllModelsExhaustedError due to empty content detection.
    """

    @pytest.mark.asyncio
    async def test_stream_chat_handles_correct_openai_format(self):
        """
        Test that stream_chat accepts chunks in OpenAI format (choices -> delta -> content)
        and successfully extracts content, avoiding the 'Empty response' error.
        This verifies that when the upstream provider (or mock) returns standard OpenAI-formatted chunks,
        the gateway correctly processes them and does not trigger the 'Empty response' validation logic.
        """
        with (
            patch("app.core.ai_gateway.OPENROUTER_API_KEY", "test_key"),
            patch("app.core.ai_gateway.get_omni_router") as mock_get_router,
        ):
            mock_router = MagicMock()
            mock_get_router.return_value = mock_router
            mock_router.get_ranked_nodes.return_value = ["model-1"]

            client = NeuralRoutingMesh("test_key")

            # Manually inject node to ensure predictable routing
            client.nodes_map["model-1"] = NeuralNode(
                model_id="model-1",
                circuit_breaker=CircuitBreaker(
                    "test", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT
                ),
            )

            # Mock _stream_from_node to yield correct OpenAI format
            async def mock_stream_correct(*args, **kwargs):
                yield {
                    "choices": [{"delta": {"content": "Hello"}}],
                }
                yield {
                    "choices": [{"delta": {"content": " World"}}],
                }

            client._stream_from_node = MagicMock(side_effect=mock_stream_correct)

            messages = [{"role": "user", "content": "Hello"}]
            chunks = []
            async for chunk in client.stream_chat(messages):
                chunks.append(chunk)

            # Verification:
            # 1. We received 2 chunks
            assert len(chunks) == 2
            # 2. The content was correctly passed through
            assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
            assert chunks[1]["choices"][0]["delta"]["content"] == " World"

            # 3. CRITICAL: No AIAllModelsExhaustedError was raised.
            # If the bug (mismatch/empty content detection) was present, this would have failed.
