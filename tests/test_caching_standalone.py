import asyncio
import importlib.util
import os
import unittest
from unittest.mock import MagicMock, patch

from app.caching.factory import CacheFactory, get_cache
from app.caching.memory_cache import InMemoryCache

REDIS_AVAILABLE = importlib.util.find_spec("redis") is not None


class TestCaching(unittest.TestCase):
    def test_memory_cache(self):
        async def run_test():
            cache = InMemoryCache(default_ttl=1)

            # Test Set/Get
            await cache.set("test_key", "test_value")
            val = await cache.get("test_key")
            self.assertEqual(val, "test_value")

            # Test Exists
            exists = await cache.exists("test_key")
            self.assertTrue(exists)

            # Test Delete
            await cache.delete("test_key")
            val = await cache.get("test_key")
            self.assertIsNone(val)

            # Test TTL
            await cache.set("ttl_key", "ttl_value", ttl=1)
            # Wait for expiration
            await asyncio.sleep(1.1)
            val = await cache.get("ttl_key")
            self.assertIsNone(val)

        asyncio.run(run_test())

    @unittest.skipUnless(REDIS_AVAILABLE, "redis غير متاح في بيئة الاختبار")
    @patch("app.caching.redis_cache.redis.from_url")
    def test_redis_cache(self, mock_redis_from_url):
        async def run_test():
            # Setup Mock
            mock_client = MagicMock()
            mock_redis_from_url.return_value = mock_client

            # AsyncMock for get/set methods
            async def mock_get(key):
                if key == "test_key":
                    return '"test_value"'
                return None

            async def mock_set(key, value, ex=None):
                return True

            mock_client.get.side_effect = mock_get
            mock_client.set.side_effect = mock_set

            from app.caching.redis_cache import RedisCache

            cache = RedisCache("redis://localhost")

            # Test Set
            await cache.set("test_key", "test_value")
            mock_client.set.assert_called()

            # Test Get
            val = await cache.get("test_key")
            self.assertEqual(val, "test_value")

        asyncio.run(run_test())

    def test_factory_defaults(self):
        # Ensure default is memory
        if "CACHE_TYPE" in os.environ:
            del os.environ["CACHE_TYPE"]

        # Reset singleton
        CacheFactory._instance = None

        cache = get_cache()
        self.assertIsInstance(cache, InMemoryCache)

if __name__ == "__main__":
    unittest.main()
