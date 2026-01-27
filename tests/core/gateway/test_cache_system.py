import asyncio

import pytest

from app.core.gateway.cache import CacheFactory, InMemoryCacheProvider, generate_cache_key
from app.core.gateway.protocols.cache import CacheProviderProtocol


@pytest.mark.asyncio
async def test_in_memory_cache_basic_ops():
    """Verify basic PUT and GET operations."""
    cache = InMemoryCacheProvider()
    key = "test_key"
    value = {"data": "test_value"}

    # Test PUT
    success = await cache.put(key, value)
    assert success is True

    # Test GET
    retrieved = await cache.get(key)
    assert retrieved == value

    # Test Missing
    assert await cache.get("missing") is None


@pytest.mark.asyncio
async def test_cache_expiration():
    """Verify TTL expiration."""
    # Use a very short TTL
    cache = InMemoryCacheProvider(default_ttl=1)  # 1 second for fallback
    key = "expired_key"
    value = "data"

    # Put with explicit 0.1s TTL
    await cache.put(key, value, ttl=0.1)

    # Verify it exists immediately
    assert await cache.get(key) == value

    # Wait for expiration
    await asyncio.sleep(0.2)

    # Verify it's gone
    assert await cache.get(key) is None


@pytest.mark.asyncio
async def test_lru_eviction():
    """Verify LRU eviction works as expected."""
    # Create cache with max size 2
    cache = InMemoryCacheProvider(max_size_items=2)

    await cache.put("k1", "v1")
    await cache.put("k2", "v2")

    # Both should exist
    assert await cache.get("k1") == "v1"
    assert await cache.get("k2") == "v2"

    # Add third item, should evict k1 (because k2 was accessed last, wait no, k1 was accessed first...
    # Logic: k1 put, k2 put. k1 is LRU.
    # accessing k1 makes k2 LRU? No.
    # Accessing k1 makes k1 MRU. k2 becomes LRU.

    # Let's access k1 to make it MRU
    await cache.get("k1")
    # Now order is: k2 (LRU), k1 (MRU)

    await cache.put("k3", "v3")
    # Should evict k2

    assert await cache.get("k3") == "v3"
    assert await cache.get("k1") == "v1"
    assert await cache.get("k2") is None


@pytest.mark.asyncio
async def test_cache_factory():
    """Verify Factory creates correct instance."""
    provider = CacheFactory.get_provider("memory")
    assert isinstance(provider, InMemoryCacheProvider)
    assert isinstance(provider, CacheProviderProtocol)


@pytest.mark.asyncio
async def test_generate_cache_key():
    """Verify key generation consistency."""
    data1 = {"a": 1, "b": 2}
    data2 = {"b": 2, "a": 1}  # Different order

    key1 = generate_cache_key(data1)
    key2 = generate_cache_key(data2)

    assert key1 == key2


@pytest.mark.asyncio
async def test_generate_cache_key_unserializable_data():
    """Verify key generation handles unserializable payloads."""
    data = {"payload": {"values"}}

    key = generate_cache_key(data)

    assert isinstance(key, str)
    assert len(key) > 0


@pytest.mark.asyncio
async def test_cache_stats_include_sets():
    """Verify cache statistics include set counters."""
    cache = InMemoryCacheProvider()
    await cache.put("stat_key", "value")

    stats = await cache.get_stats()

    assert stats["sets"] == 1
    assert stats["hits"] == 0
    assert stats["misses"] == 0


@pytest.mark.asyncio
async def test_cache_rejects_negative_ttl():
    """Verify cache rejects negative TTL values."""
    cache = InMemoryCacheProvider()

    with pytest.raises(ValueError):
        await cache.put("negative_ttl", "value", ttl=-1)


@pytest.mark.asyncio
async def test_cache_clear_resets_stats():
    """Verify clearing the cache resets statistics counters."""
    cache = InMemoryCacheProvider()
    await cache.put("stat_reset_key", "value")
    await cache.get("stat_reset_key")

    await cache.clear()

    stats = await cache.get_stats()

    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["evictions"] == 0
    assert stats["sets"] == 0
