import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import httpx
from app.core.gateway.simple_client import SimpleAIClient
from app.core.types import JSONDict

class TestSimpleAIClient(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_config_patch = patch('app.core.gateway.simple_client.get_ai_config')
        self.mock_config = self.mock_config_patch.start()
        self.mock_config.return_value.openrouter_api_key = "test-key"
        self.mock_config.return_value.primary_model = "primary"
        self.mock_config.return_value.get_fallback_models.return_value = ["fallback1"]

        self.mock_client_patch = patch('app.core.gateway.connection.ConnectionManager.get_client')
        self.mock_client = self.mock_client_patch.start()
        self.mock_httpx_client = AsyncMock(spec=httpx.AsyncClient)
        self.mock_client.return_value = self.mock_httpx_client

        # Mock Cognitive Engine to avoid memory logic in tests
        self.mock_cog_patch = patch('app.core.gateway.simple_client.get_cognitive_engine')
        self.mock_cog = self.mock_cog_patch.start()
        self.mock_cog.return_value.recall.return_value = None

    async def asyncTearDown(self):
        self.mock_config_patch.stop()
        self.mock_client_patch.stop()
        self.mock_cog_patch.stop()

    async def test_stream_chat_primary_success(self):
        client = SimpleAIClient()
        messages = [{"role": "user", "content": "hello"}]

        # Mock streaming response
        mock_response = MagicMock()
        mock_response.status_code = 200

        async def async_lines():
            yield "data: {\"choices\": [{\"delta\": {\"content\": \"hi\"}}]}"
            yield "data: [DONE]"

        mock_response.aiter_lines.return_value = async_lines()
        mock_response.aread = AsyncMock() # needed for error handling path check

        # Mocking the async context manager return
        # stream() returns an async context manager
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__.return_value = mock_response
        self.mock_httpx_client.stream.return_value = mock_ctx

        chunks = []
        async for chunk in client.stream_chat(messages):
            chunks.append(chunk)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]['choices'][0]['delta']['content'], "hi")

        # Verify primary model was used
        call_args = self.mock_httpx_client.stream.call_args
        self.assertEqual(call_args[1]['json']['model'], "primary")

    @patch('app.core.gateway.simple_client.SimpleAIClient._stream_model')
    async def test_fallback_logic(self, mock_stream_model):
        client = SimpleAIClient()
        messages = [{"role": "user", "content": "hello"}]

        # Setup: Primary fails, Fallback succeeds
        async def stream_side_effect(client, model_id, msgs):
            if model_id == "primary":
                raise httpx.ConnectError("Failed")
            if model_id == "fallback1":
                yield {"content": "success"}
                return
            yield {"content": "should not reach"}

        mock_stream_model.side_effect = stream_side_effect

        chunks = []
        async for chunk in client.stream_chat(messages):
            chunks.append(chunk)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["content"], "success")

    @patch('app.core.gateway.simple_client.SimpleAIClient._stream_model')
    async def test_safety_net_logic(self, mock_stream_model):
        client = SimpleAIClient()
        messages = [{"role": "user", "content": "hello"}]

        # Setup: All models fail
        async def stream_side_effect(client, model_id, msgs):
            # This needs to be an async generator that raises immediately
            if True:
                raise httpx.ConnectError("Failed")
            yield {} # unreachable but needed to make it a generator function

        mock_stream_model.side_effect = stream_side_effect

        chunks = []
        async for chunk in client.stream_chat(messages):
            chunks.append(chunk)

        # Should return safety net chunks
        self.assertTrue(len(chunks) > 0)
        self.assertEqual(chunks[0]['model'], "system/safety-net")
