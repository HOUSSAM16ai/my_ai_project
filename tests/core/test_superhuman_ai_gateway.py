
import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import httpx
from app.core.ai_gateway import (
    CircuitBreaker, CircuitState, OpenRouterAIClient,
    ConnectionManager, AICircuitOpenError, AIProviderError,
    _GLOBAL_CIRCUIT_BREAKER
)

# --- Test Circuit Breaker Logic ---

def test_circuit_breaker_initial_state():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True

def test_circuit_breaker_opens_on_failures():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure() # 3rd failure
    assert cb.state == CircuitState.OPEN
    assert cb.allow_request() is False

@pytest.mark.asyncio
async def test_circuit_breaker_recovery_flow():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

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
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

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

@pytest.fixture(autouse=True)
def reset_global_circuit_breaker():
    """Reset the global circuit breaker before each test."""
    _GLOBAL_CIRCUIT_BREAKER.state = CircuitState.CLOSED
    _GLOBAL_CIRCUIT_BREAKER.failure_count = 0
    _GLOBAL_CIRCUIT_BREAKER.threshold = 5 # Default
    _GLOBAL_CIRCUIT_BREAKER.last_failure_time = 0.0

@pytest.mark.asyncio
async def test_client_circuit_breaker_integration():
    # Force the global breaker to be fresh for this test
    _GLOBAL_CIRCUIT_BREAKER.threshold = 2

    client = OpenRouterAIClient(api_key="fake")

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
        with pytest.raises(Exception):
            async for _ in client.stream_chat([]): pass

        # Fail 2 (Threshold met)
        with pytest.raises(Exception):
            async for _ in client.stream_chat([]): pass

        assert _GLOBAL_CIRCUIT_BREAKER.state == CircuitState.OPEN

        # Fail 3 (Circuit Open - Fast Fail)
        with pytest.raises(AICircuitOpenError):
            async for _ in client.stream_chat([]): pass

@pytest.mark.asyncio
async def test_client_retry_logic():
    client = OpenRouterAIClient(api_key="fake")

    # Mock ConnectionManager
    mock_httpx = MagicMock(spec=httpx.AsyncClient)
    mock_stream_context = AsyncMock()
    mock_httpx.stream.return_value = mock_stream_context

    # Simulate: Fail, Fail, Success
    # We use side_effect on __aenter__ to simulate connection/status errors
    error_503 = httpx.HTTPStatusError(
        "503 Service Unavailable", request=MagicMock(), response=MagicMock(status_code=503)
    )

    # Mock response for success
    mock_response = MagicMock() # Changed from AsyncMock to MagicMock for the base object to avoid auto-async methods
    mock_response.raise_for_status = MagicMock()

    # Mock aiter_lines correctly
    async def mock_lines_gen():
        yield "data: {\"content\": \"Hello\"}"
        yield "data: [DONE]"

    # aiter_lines is a method called on the response object
    # It must return an async iterator
    mock_response.aiter_lines = MagicMock(return_value=mock_lines_gen())

    # The side effect applies to the context manager entrance
    mock_stream_context.__aenter__.side_effect = [error_503, error_503, mock_response]

    with patch.object(ConnectionManager, "get_client", return_value=mock_httpx):
        # We expect it to succeed after retries
        chunks = []
        async for chunk in client.stream_chat([]):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0]["content"] == "Hello"

        # Check that it tried 3 times (2 failures + 1 success)
        assert mock_httpx.stream.call_count == 3
