"""
Unit Test for Redis Event Bridge (Streaming BFF).
Mocks Redis and Internal EventBus to verify flow.
"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.redis_bus import RedisEventBridge


class TestRedisBridge(unittest.IsolatedAsyncioTestCase):
    async def test_bridge_flow(self):
        # 1. Mock Redis
        mock_redis_client = AsyncMock()
        mock_pubsub = AsyncMock()

        # redis.pubsub() is synchronous
        mock_redis_client.pubsub = MagicMock(return_value=mock_pubsub)

        # Simulate message stream
        message = {
            "type": "pmessage",
            "channel": "mission:123",
            "data": json.dumps({"event_type": "test", "data": "hello"}),
        }

        # Mock pubsub.listen() as async generator
        async def mock_listen():
            yield message
            # Sleep to allow processing
            await asyncio.sleep(0.1)

        mock_pubsub.listen = MagicMock(side_effect=mock_listen)

        # 2. Mock Internal EventBus
        mock_internal_bus = AsyncMock()

        with (
            patch("app.core.redis_bus.redis.from_url", return_value=mock_redis_client),
            patch("app.core.redis_bus.get_event_bus", return_value=mock_internal_bus),
        ):
            bridge = RedisEventBridge("redis://mock:6379")
            await bridge.start()

            # Wait a bit for the loop to process
            await asyncio.sleep(0.2)

            # 3. Verify Subscription
            mock_pubsub.psubscribe.assert_called_with("mission:*")

            # 4. Verify Forwarding
            mock_internal_bus.publish.assert_called()
            args = mock_internal_bus.publish.call_args
            self.assertEqual(args[0][0], "mission:123")
            self.assertEqual(args[0][1], {"event_type": "test", "data": "hello"})

            await bridge.stop()
