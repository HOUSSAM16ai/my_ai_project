
import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import httpx
from app.core.ai_gateway import (
    CircuitBreaker, CircuitState, NeuralRoutingMesh,
    ConnectionManager, AICircuitOpenError, AIProviderError,
    AIConnectionError, PRIMARY_MODEL
)

# --- Test Circuit Breaker Logic ---

def test_circuit_breaker_initial_state():
    cb = CircuitBreaker("Test-Breaker", failure_threshold=3, recovery_timeout=1.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True

def test_circuit_breaker_opens_on_failures():
    cb = CircuitBreaker("Test-Breaker", failure_threshold=3, recovery_timeout=1.0)

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure() # 3rd failure
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False

@pytest.mark.asyncio
async def test_circuit_breaker_recovery_flow():
    cb = CircuitBreaker("Test-Breaker", failure_threshold=2, recovery_timeout=0.1)

    # Fail until Open
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

    # Wait for recovery timeout
    await asyncio.sleep(0.15)

    # Should be allow_request -> True (transitions to HALF_OPEN effectively on check)
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN

    # Success closes it
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure():
    cb = CircuitBreaker("Test-Breaker", failure_threshold=2, recovery_timeout=0.1)

    # Fail until Open
    cb.record_failure()
    cb.record_failure()
    await asyncio.sleep(0.15)

    # Transition to Half Open
    cb.allow_request()
    assert cb.state == CircuitState.HALF_OPEN

    # Failure in Half Open -> Back to Open immediately
    cb.record_failure()
    assert cb.state == CircuitState.OPEN

# --- Test Client Resilience ---

@pytest.mark.asyncio
async def test_client_circuit_breaker_integration():
    # Setup mocks
    mock_omni_router = MagicMock()
    mock_omni_router.get_ranked_nodes.return_value = [PRIMARY_MODEL]

    with patch("app.core.ai_gateway.get_omni_router", return_value=mock_omni_router):
        client = NeuralRoutingMesh(api_key="fake")

        # Access the specific node for the primary model to manipulate its circuit breaker
        primary_node = client.nodes_map[PRIMARY_MODEL]
        # Set a low threshold for testing
        primary_node.circuit_breaker.threshold = 2

        # Mock ConnectionManager to return a mock httpx client
        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_stream_context = AsyncMock()
        mock_httpx.stream.return_value = mock_stream_context

        # Simulate 500 errors
        mock_stream_context.__aenter__.side_effect = httpx.HTTPStatusError(
            "500 Error", request=MagicMock(), response=MagicMock(status_code=500)
        )

        with patch.object(ConnectionManager, "get_client", return_value=mock_httpx):
            # Fail 1
            # We expect AIConnectionError or similar, but the router tries other nodes.
            # Since we only mocked one node return in get_ranked_nodes, it might fail with AIAllModelsExhaustedError if we don't return others.
            # But here we want to test the circuit breaker of the specific node.

            # Since stream_chat catches errors and tries next, we need to ensure it sees the failure.

            # Let's override get_prioritized_nodes to return ONLY our primary node to force failure bubble up if it fails?
            # Or just check the circuit breaker state.

            try:
                async for _ in client.stream_chat([{"content": "test"}]): pass
            except Exception:
                pass # Expected failure

            try:
                async for _ in client.stream_chat([{"content": "test"}]): pass
            except Exception:
                pass # Expected failure

            # At this point, failure count should be 2, so it should be OPEN.
            assert primary_node.circuit_breaker.state == CircuitState.OPEN

            # Fail 3 (Circuit Open - Fast Fail)
            # The router filters out open circuits in _get_prioritized_nodes
            # So if we request again, it should return NO nodes (if this is the only one)
            # and raise AIAllModelsExhaustedError immediately without calling stream.

            mock_httpx.stream.reset_mock()

            with pytest.raises(Exception): # AIAllModelsExhaustedError
                async for _ in client.stream_chat([{"content": "test"}]): pass

            # Should NOT have called stream again
            mock_httpx.stream.assert_not_called()

@pytest.mark.asyncio
async def test_client_retry_logic():
    # Setup mocks
    mock_omni_router = MagicMock()
    mock_omni_router.get_ranked_nodes.return_value = [PRIMARY_MODEL]

    with patch("app.core.ai_gateway.get_omni_router", return_value=mock_omni_router):
        client = NeuralRoutingMesh(api_key="fake")

        # Mock ConnectionManager
        mock_httpx = MagicMock(spec=httpx.AsyncClient)
        mock_stream_context = AsyncMock()
        mock_httpx.stream.return_value = mock_stream_context

        # Simulate: Fail, Fail, Success
        error_503 = httpx.HTTPStatusError(
            "503 Service Unavailable", request=MagicMock(), response=MagicMock(status_code=503)
        )

        # Mock response for success
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.status_code = 200

        # Mock aiter_lines correctly
        async def mock_lines_gen():
            yield "data: {\"content\": \"Hello\"}"
            yield "data: [DONE]"

        mock_response.aiter_lines = MagicMock(return_value=mock_lines_gen())

        # The side effect applies to the context manager entrance
        # Note: NeuralRoutingMesh retries internally in `_stream_from_node` (MAX_RETRIES=3)
        mock_stream_context.__aenter__.side_effect = [error_503, error_503, mock_response]

        with patch.object(ConnectionManager, "get_client", return_value=mock_httpx):
            chunks = []
            async for chunk in client.stream_chat([{"role": "user", "content": "test"}]):
                chunks.append(chunk)

            assert len(chunks) == 1
            assert chunks[0]["content"] == "Hello"

            # Check that it tried 3 times (2 failures + 1 success)
            assert mock_httpx.stream.call_count == 3
