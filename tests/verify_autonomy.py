import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock
from app.core.gateway.simple_client import SimpleAIClient
from app.services.chat.graph.nodes.supervisor import SupervisorNode

class TestAutonomy(unittest.IsolatedAsyncioTestCase):
    async def test_cache_disabled(self):
        """Test that SimpleAIClient does NOT return the same cached answer for different prompts."""
        client = SimpleAIClient(api_key="dummy")

        # Mock cognitive engine to ALWAYS return a cached value if called
        client.cognitive_engine = MagicMock()
        client.cognitive_engine.recall.return_value = [{"choices": [{"delta": {"content": "STATIC_ANSWER"}}]}]

        # Mock stream_model to return dynamic answers
        client._stream_model = MagicMock()

        async def mock_stream_1(*args, **kwargs):
            yield {"choices": [{"delta": {"content": "ANSWER_1"}}]}

        async def mock_stream_2(*args, **kwargs):
            yield {"choices": [{"delta": {"content": "ANSWER_2"}}]}

        # First Call
        client._stream_model.side_effect = mock_stream_1
        response1 = await client.send_message("system", "Question 1")

        # Second Call
        client._stream_model.side_effect = mock_stream_2
        response2 = await client.send_message("system", "Question 2")

        print(f"Response 1: {response1}")
        print(f"Response 2: {response2}")

        # If cache was active and mocked, both would be "STATIC_ANSWER"
        self.assertNotEqual(response1, "STATIC_ANSWER", "Should bypass cache")
        self.assertNotEqual(response2, "STATIC_ANSWER", "Should bypass cache")
        self.assertEqual(response1, "ANSWER_1")
        self.assertEqual(response2, "ANSWER_2")

    async def test_supervisor_retry_loop(self):
        """Test that SupervisorNode retries on invalid JSON."""
        mock_ai_client = AsyncMock()

        # First return invalid JSON, then valid JSON
        mock_ai_client.send_message.side_effect = [
            "I am thinking... here is the json: {invalid", # Fail 1
            '{"next": "planner", "reason": "Retry worked"}' # Success 2
        ]

        state = {"messages": [], "plan": []}
        result = await SupervisorNode.decide_next_step(state, mock_ai_client)

        print(f"Supervisor Result: {result}")

        self.assertEqual(result["next"], "planner")
        self.assertEqual(result["routing_trace"][0]["reason"], "Retry worked")
        self.assertEqual(mock_ai_client.send_message.call_count, 2, "Should have called LLM twice (retry)")

if __name__ == "__main__":
    unittest.main()
