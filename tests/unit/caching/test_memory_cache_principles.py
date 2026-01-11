"""اختبارات مبادئ التخزين المؤقت في الذاكرة."""

import asyncio

import pytest

from app.caching.memory_cache import InMemoryCache


@pytest.mark.asyncio
async def test_get_or_set_coalesces_requests():
    """يتحقق من تجميع الطلبات المتزامنة لتفادي تدافع الكاش."""
    cache = InMemoryCache(default_ttl=5)
    counter = {"calls": 0}

    async def compute():
        counter["calls"] += 1
        await asyncio.sleep(0.01)
        return "value"

    results = await asyncio.gather(
        *[cache.get_or_set("key", compute) for _ in range(5)]
    )

    assert results == ["value"] * 5
    assert counter["calls"] == 1


@pytest.mark.asyncio
async def test_cache_stats_tracking():
    """يتحقق من تتبع الإحصائيات الأساسية للكاش."""
    cache = InMemoryCache(default_ttl=10)

    await cache.get("missing")
    await cache.set("key", "value")
    await cache.get("key")
    await cache.delete("key")

    stats = await cache.get_stats()

    assert stats.hits == 1
    assert stats.misses == 1
    assert stats.sets == 1
    assert stats.deletes == 1
    assert stats.hit_ratio == 0.5
    assert stats.miss_ratio == 0.5
