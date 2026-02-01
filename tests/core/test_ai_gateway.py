from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.ai_gateway import AIGatewayFacade


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.generate_text = AsyncMock(return_value={"result": "ok"})
    client.forge_new_code = AsyncMock(return_value={"result": "code"})
    return client


@pytest.mark.asyncio
async def test_facade_client_property(mock_client):
    with patch("app.core.ai_gateway.get_ai_client", return_value=mock_client):
        facade = AIGatewayFacade()
        assert facade.client == mock_client
        # Second access should be cached
        assert facade.client == mock_client


@pytest.mark.asyncio
async def test_facade_methods(mock_client):
    with patch("app.core.ai_gateway.get_ai_client", return_value=mock_client):
        facade = AIGatewayFacade()

        res = await facade.generate_text("test")
        assert res == {"result": "ok"}

        res = await facade.forge_new_code()
        assert res == {"result": "code"}


def test_facade_getattr(mock_client):
    with patch("app.core.ai_gateway.get_ai_client", return_value=mock_client):
        facade = AIGatewayFacade()
        # Should proxy 'stream_chat' to client
        mock_client.stream_chat = "mock_stream"
        assert facade.stream_chat == "mock_stream"
