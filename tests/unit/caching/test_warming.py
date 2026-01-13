"""
Tests for Cache Warming (Phase 2 completion).
"""

import asyncio

import pytest

from app.caching.memory_cache import InMemoryCache
from app.caching.warming import CacheWarmer


@pytest.mark.asyncio
async def test_cache_warmer_simple():
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

    # Check if data is in cache
    config = await cache.get("app_config")
    assert config == {"theme": "dark"}

    static = await cache.get("static_blob")
    assert static == "static_data"


@pytest.mark.asyncio
async def test_cache_warmer_failure():
    cache = InMemoryCache()
    warmer = CacheWarmer(cache)

    async def broken_loader():
        raise ValueError("DB down")

    warmer.register("broken", broken_loader)

    results = await warmer.warm_up()
    assert results["broken"] is False

    # Cache should be empty for this key
    assert await cache.get("broken") is None
