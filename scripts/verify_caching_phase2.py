"""
Standalone verification script for Caching Phase 2 (Tags & Warming).
Bypasses pytest collection overhead.
"""

import asyncio
import logging
import sys

from app.caching.invalidation import InvalidationManager
from app.caching.memory_cache import InMemoryCache
from app.caching.warming import CacheWarmer

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("verifier")


async def test_tagging():
    logger.info("🧪 Testing Tagging Logic...")
    cache = InMemoryCache()
    manager = InvalidationManager(cache)

    # Set items
    await cache.set("product:A", "expensive")
    await cache.set("product:B", "cheap")
    await cache.set("product:C", "moderate")

    # Add tags
    await manager.add_tags("product:A", ["electronics", "sony"])
    await manager.add_tags("product:B", ["electronics", "samsung"])
    await manager.add_tags("product:C", ["books"])

    # Verify members
    members = await cache.set_members("tag:electronics")
    assert "product:A" in members
    assert "product:B" in members
    assert "product:C" not in members
    logger.info("✅ Tag membership verified.")

    # Invalidate tag
    count = await manager.invalidate_tag("electronics")

    # Should delete product A and B
    assert count == 2
    assert await cache.get("product:A") is None
    assert await cache.get("product:B") is None
    assert await cache.get("product:C") == "moderate"
    logger.info("✅ Tag invalidation verified.")

    # Tag entry itself should be gone
    assert await cache.exists("tag:electronics") is False
    logger.info("✅ Tag cleanup verified.")


async def test_warming():
    logger.info("🧪 Testing Cache Warming...")
    cache = InMemoryCache()
    warmer = CacheWarmer(cache)

    async def fetch_config():
        await asyncio.sleep(0.01)
        return {"theme": "dark"}

    def fetch_static():
        return "static_data"

    warmer.register("app_config", fetch_config)
    warmer.register("static_blob", fetch_static)

    results = await warmer.warm_up()

    assert results["app_config"] is True
    assert results["static_blob"] is True
    logger.info("✅ Warm-up execution verified.")

    # Check if data is in cache
    config = await cache.get("app_config")
    assert config == {"theme": "dark"}

    static = await cache.get("static_blob")
    assert static == "static_data"
    logger.info("✅ Warm-up data persistence verified.")


async def main():
    try:
        await test_tagging()
        await test_warming()
        logger.info("🎉 ALL TESTS PASSED!")
    except AssertionError as e:
        logger.error(f"❌ Assertion Failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
