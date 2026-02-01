import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.gateway.simple_client import SimpleAIClient


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.openrouter_api_key = "test_key"
    config.primary_model = "primary"
    config.get_fallback_models.return_value = ["fallback"]
    return config


@pytest.fixture
def mock_cognitive_engine():
    engine = MagicMock()
    engine.recall.return_value = None  # Cache miss
    engine.memorize = MagicMock()
    return engine


@pytest.fixture
def client(mock_config, mock_cognitive_engine):
    with patch("app.core.gateway.simple_client.get_ai_config", return_value=mock_config):
        with patch(
            "app.core.gateway.simple_client.get_cognitive_engine",
            return_value=mock_cognitive_engine,
        ):
            client = SimpleAIClient()
            yield client


@pytest.mark.asyncio
async def test_stream_chat_cache_hit(client, mock_cognitive_engine):
    # Setup cache hit
    mock_cognitive_engine.recall.return_value = [{"role": "assistant", "content": "cached"}]

    messages = [{"role": "user", "content": "hello"}]
    chunks = []
    async for chunk in client.stream_chat(messages):
        chunks.append(chunk)

    assert len(chunks) == 1
    assert chunks[0]["content"] == "cached"
    # Should NOT call external API logic (we won't check here but implicitly logic implies it returns early)


@pytest.mark.asyncio
async def test_stream_chat_primary_success(client, mock_config):
    # Mock httpx client response
    mock_httpx_client = MagicMock()  # Not AsyncMock, stream is synced called returning CM
    mock_response = AsyncMock()
    mock_response.status_code = 200

    # SSE chunk format
    chunk_data = {"choices": [{"delta": {"content": "world"}}]}

    async def mock_iter_lines():
        yield f"data: {json.dumps(chunk_data)}"
        yield "data: [DONE]"

    mock_response.aiter_lines = mock_iter_lines

    class MockStreamContext:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return mock_response

        async def __aexit__(self, *args):
            pass

    # Context manager setup
    mock_httpx_client.stream.side_effect = MockStreamContext

    # Patch logger to see errors
    with patch("app.core.gateway.simple_client.logger") as mock_logger:
        with patch(
            "app.core.gateway.connection.ConnectionManager.get_client",
            return_value=mock_httpx_client,
        ):
            messages = [{"role": "user", "content": "hello"}]
            chunks = [c async for c in client.stream_chat(messages)]

            # Debug if failed
            if len(chunks) != 1:
                # Print error calls
                print(mock_logger.error.call_args_list)
                print(mock_logger.warning.call_args_list)

            assert len(chunks) == 1
            assert chunks[0]["choices"][0]["delta"]["content"] == "world"


@pytest.mark.asyncio
async def test_stream_chat_fallback_chain(client):
    # Primary fails, Fallback success.
    mock_httpx_client = MagicMock()

    # Response 1 (Primary): 500
    primary_response = AsyncMock()
    primary_response.status_code = 500
    primary_response.aread = AsyncMock()

    # Response 2 (Fallback): 200 OK
    fallback_response = AsyncMock()
    fallback_response.status_code = 200
    chunk_data = {"choices": [{"delta": {"content": "fallback"}}]}

    async def fallback_iter():
        yield f"data: {json.dumps(chunk_data)}"
        yield "data: [DONE]"

    fallback_response.aiter_lines = fallback_iter

    # Side effects for stream call
    # We need to return different context managers based on call?
    # Or just based on model payload?

    # Simple strategy: First call raises/fails, second succeeds?
    # client.stream() returns a context manager.

    call_count = 0

    class MockStreamContext:
        def __init__(self, *args, **kwargs):
            nonlocal call_count
            self.count = call_count
            call_count += 1

        async def __aenter__(self):
            if self.count == 0:
                return primary_response
            return fallback_response

        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_httpx_client.stream.side_effect = MockStreamContext

    with patch(
        "app.core.gateway.connection.ConnectionManager.get_client", return_value=mock_httpx_client
    ):
        messages = [{"role": "user", "content": "retry me"}]
        chunks = [c async for c in client.stream_chat(messages)]

        assert "fallback" in str(chunks)


@pytest.mark.asyncio
async def test_safety_net_activation(client):
    # All fail
    mock_httpx_client = AsyncMock()
    mock_httpx_client.stream.side_effect = Exception("All models broken")

    with patch(
        "app.core.gateway.connection.ConnectionManager.get_client", return_value=mock_httpx_client
    ):
        messages = [{"role": "user", "content": "panic"}]
        chunks = [c async for c in client.stream_chat(messages)]

        # Check for safety net content
        content = "".join(
            [c["choices"][0]["delta"].get("content", "") for c in chunks if c.get("choices")]
        )
        assert "System Alert" in content
