
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.ai_gateway import NeuralRoutingMesh, NeuralNode, CircuitBreaker, AIConnectionError, CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT

@pytest.mark.asyncio
async def test_rate_limit_cooldown_behavior():
    """
    Verifies that a Neural Node hitting a 429 is placed in a "Penalty Box" (Cool-down)
    and is skipped for subsequent requests within the cooldown period.
    """

    # 1. Setup NeuralRoutingMesh with two nodes: Primary and Backup
    with patch("app.core.ai_gateway.OPENROUTER_API_KEY", "test_key"), \
         patch("app.core.ai_gateway.get_cognitive_engine") as mock_get_engine:

        # Disable Cognitive Recall to ensure routing logic is tested
        mock_engine = MagicMock()
        mock_engine.recall.return_value = None
        mock_get_engine.return_value = mock_engine

        client = NeuralRoutingMesh("test_key")

        # Define models
        primary_model = "primary-model"
        backup_model = "backup-model"

        # Create nodes
        client.nodes_map = {}
        client.nodes_map[primary_model] = NeuralNode(
            model_id=primary_model,
            circuit_breaker=CircuitBreaker("Primary", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT)
        )
        client.nodes_map[backup_model] = NeuralNode(
            model_id=backup_model,
            circuit_breaker=CircuitBreaker("Backup", CIRCUIT_FAILURE_THRESHOLD, CIRCUIT_RECOVERY_TIMEOUT)
        )

        # Ensure omni_router knows about them (mocking it)
        client.omni_router = MagicMock()
        client.omni_router.get_ranked_nodes.return_value = [primary_model, backup_model]

        # Mock ConnectionManager.get_client
        mock_client = AsyncMock()
        mock_client.stream = MagicMock()

        # Response 1 (Primary): 429
        # Note: In the code, we call `await response.aread()`
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.aread = AsyncMock(return_value=b"Rate Limit Exceeded")
        resp_429.__aenter__ = AsyncMock(return_value=resp_429)
        resp_429.__aexit__ = AsyncMock(return_value=None)

        # Response 2 (Backup): 200 OK
        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.raise_for_status = MagicMock()

        async def async_lines_gen():
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
            yield 'data: [DONE]'

        resp_200.aiter_lines = MagicMock(return_value=async_lines_gen())
        resp_200.__aenter__ = AsyncMock(return_value=resp_200)
        resp_200.__aexit__ = AsyncMock(return_value=None)

        # We need a side effect for client.stream calls
        def stream_side_effect(*args, **kwargs):
            json_body = kwargs.get('json', {})
            model = json_body.get('model')

            if model == primary_model:
                 return resp_429
            elif model == backup_model:
                return resp_200
            return resp_200

        mock_client.stream.side_effect = stream_side_effect

        # PATCH TIME.TIME to simulate cooldown expiry or valid cooldown
        mock_time = MagicMock(return_value=1000.0)

        with patch("app.core.ai_gateway.ConnectionManager.get_client", return_value=mock_client), \
             patch("time.time", mock_time):

            # --- REQUEST 1 ---
            messages = [{"role": "user", "content": "hi"}]

            chunks = []
            try:
                async for chunk in client.stream_chat(messages):
                    chunks.append(chunk)
            except Exception as e:
                pytest.fail(f"Stream failed unexpectedly: {e}")

            assert len(chunks) > 0
            assert chunks[0]['choices'][0]['delta']['content'] == "Hello"

            # Verify primary was attempted
            calls = mock_client.stream.call_args_list
            primary_calls = [c for c in calls if c.kwargs.get('json', {}).get('model') == primary_model]
            assert len(primary_calls) == 1

            # Verify cooldown set (time.time is 1000, so until 1060)
            primary_node = client.nodes_map[primary_model]
            assert primary_node.rate_limit_cooldown_until == 1060.0

            # --- REQUEST 2 ---
            # Reset mocks
            mock_client.stream.reset_mock()

            # Advance time slightly (still within cooldown)
            mock_time.return_value = 1010.0

            # Run stream again
            chunks = []
            async for chunk in client.stream_chat(messages):
                chunks.append(chunk)

            # Verify primary was attempted (Should be 0 after fix)
            calls = mock_client.stream.call_args_list
            primary_calls = [c for c in calls if c.kwargs.get('json', {}).get('model') == primary_model]

            # This assertion checks the "Fix"
            assert len(primary_calls) == 0, f"Primary model should have been skipped, but was called {len(primary_calls)} times"

            # Verify backup was used
            backup_calls = [c for c in calls if c.kwargs.get('json', {}).get('model') == backup_model]
            assert len(backup_calls) == 1
