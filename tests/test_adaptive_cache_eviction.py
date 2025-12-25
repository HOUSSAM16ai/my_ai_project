import asyncio

import pytest

from app.services.admin.streaming.breakthrough import AdaptiveCache


@pytest.mark.asyncio
async def test_adaptive_cache_eviction_fix():
    print("Testing AdaptiveCache eviction fix...")

    # Create a small cache for testing
    cache = AdaptiveCache(max_size=3)

    async def compute_val():
        return "value"

    # 1. Fill the cache
    await cache.get_or_compute("key1", compute_val)
    await cache.get_or_compute("key2", compute_val)
    await cache.get_or_compute("key3", compute_val)

    assert len(cache.cache) == 3

    # 2. Add a 4th item. With eviction, it SHOULD be cached, evicting someone else.
    await cache.get_or_compute("key4", compute_val)

    assert "key4" in cache.cache, "key4 was NOT cached (eviction failed)."
    assert len(cache.cache) == 3, "Cache size should remain at max_size"

    # 3. Test Expiration Cleanup
    # Set a short TTL item
    cache = AdaptiveCache(max_size=1)

    # Add item with short TTL
    await cache.get_or_compute("short_ttl", compute_val, ttl=0.1)

    # Wait for expiration
    await asyncio.sleep(0.2)

    # Try to add new item
    await cache.get_or_compute("new_item", compute_val)

    assert "new_item" in cache.cache, "'new_item' was NOT cached (expired item was not cleaned up)."
    assert "short_ttl" not in cache.cache, "'short_ttl' should have been removed."
