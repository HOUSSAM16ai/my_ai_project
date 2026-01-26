import asyncio

import pytest

from app.core.gateway.cache import CacheFactory, InMemoryCacheProvider, generate_cache_key


@pytest.fixture(autouse=True)
def init_db() -> None:
    """تعطيل تهيئة قاعدة البيانات لهذه الوحدة."""


@pytest.fixture(autouse=True)
def clean_db() -> None:
    """تعطيل تنظيف قاعدة البيانات لهذه الوحدة."""
    yield


@pytest.mark.asyncio
async def test_cache_put_get_tracks_hits_and_misses() -> None:
    cache = InMemoryCacheProvider(max_size_items=2, default_ttl=10)

    assert await cache.get("missing") is None
    assert await cache.put("key", "value") is True
    assert await cache.get("key") == "value"

    stats = await cache.get_stats()

    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["size"] == 1


@pytest.mark.asyncio
async def test_cache_eviction_and_clear() -> None:
    cache = InMemoryCacheProvider(max_size_items=1, default_ttl=10)

    await cache.put("first", 1)
    await cache.put("second", 2)

    assert await cache.get("first") is None
    stats = await cache.get_stats()
    assert stats["evictions"] == 1
    assert stats["size"] == 1

    assert await cache.clear() is True
    cleared_stats = await cache.get_stats()

    assert cleared_stats["size"] == 0
    assert cleared_stats["hits"] == 0
    assert cleared_stats["misses"] == 0


@pytest.mark.asyncio
async def test_cache_expiration_with_ttl() -> None:
    cache = InMemoryCacheProvider(max_size_items=1, default_ttl=1)

    await cache.put("temp", "value", ttl=0)

    await asyncio.sleep(0)

    assert await cache.get("temp") is None


def test_cache_factory_unknown_provider_falls_back() -> None:
    provider = CacheFactory.get_provider("unknown")

    assert isinstance(provider, InMemoryCacheProvider)


def test_generate_cache_key_is_deterministic() -> None:
    key_a = generate_cache_key({"b": 2, "a": 1})
    key_b = generate_cache_key({"a": 1, "b": 2})

    assert key_a == key_b


def test_generate_cache_key_handles_unserializable() -> None:
    class Unserializable:
        def __repr__(self) -> str:
            return "<unserializable>"

    key = generate_cache_key(Unserializable())

    assert isinstance(key, str)
    assert len(key) == 64
