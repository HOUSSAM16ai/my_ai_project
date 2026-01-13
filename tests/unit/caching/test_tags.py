"""
Tests for Cache Invalidation and Tagging (Phase 2 completion).
"""

import pytest

from app.caching.invalidation import InvalidationManager
from app.caching.memory_cache import InMemoryCache


@pytest.mark.asyncio
async def test_invalidation_pattern():
    cache = InMemoryCache()
    manager = InvalidationManager(cache)

    await cache.set("user:1:profile", "data1")
    await cache.set("user:1:settings", "data2")
    await cache.set("user:2:profile", "data3")

    # Invalidate user 1
    count = await manager.invalidate_pattern("user:1:*")
    assert count == 2

    assert await cache.get("user:1:profile") is None
    assert await cache.get("user:1:settings") is None
    assert await cache.get("user:2:profile") == "data3"


@pytest.mark.asyncio
async def test_tagging_logic():
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

    # Verify internal tag structure (implementation detail, but good for white-box testing)
    members = await cache.set_members("tag:electronics")
    assert "product:A" in members
    assert "product:B" in members
    assert "product:C" not in members

    # Invalidate tag
    count = await manager.invalidate_tag("electronics")

    # Should delete product A and B
    assert count == 2
    assert await cache.get("product:A") is None
    assert await cache.get("product:B") is None
    assert await cache.get("product:C") == "moderate"

    # Tag entry itself should be gone
    assert await cache.exists("tag:electronics") is False


@pytest.mark.asyncio
async def test_tagging_empty():
    cache = InMemoryCache()
    manager = InvalidationManager(cache)

    count = await manager.invalidate_tag("non_existent")
    assert count == 0
