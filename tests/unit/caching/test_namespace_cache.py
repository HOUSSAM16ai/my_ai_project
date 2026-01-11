import pytest

from app.caching.memory_cache import InMemoryCache
from app.caching.namespace_cache import NamespacedCache


@pytest.mark.asyncio
async def test_namespaced_cache_isolates_keys() -> None:
    backend = InMemoryCache()
    cache = NamespacedCache(backend=backend, namespace="service-a")

    await cache.set("alpha", "value-a")
    assert await cache.get("alpha") == "value-a"

    backend_keys = await backend.scan_keys("service-a:*")
    assert backend_keys == ["service-a:alpha"]


@pytest.mark.asyncio
async def test_namespaced_cache_clear_is_scoped() -> None:
    backend = InMemoryCache()
    cache = NamespacedCache(backend=backend, namespace="service-b")

    await backend.set("service-b:keep", "yes")
    await backend.set("service-c:other", "no")

    await cache.clear()

    assert await backend.exists("service-b:keep") is False
    assert await backend.exists("service-c:other") is True


@pytest.mark.asyncio
async def test_namespaced_cache_scan_strips_prefix() -> None:
    backend = InMemoryCache()
    cache = NamespacedCache(backend=backend, namespace="service-d")

    await cache.set("one", "1")
    await cache.set("two", "2")

    keys = sorted(await cache.scan_keys("*"))
    assert keys == ["one", "two"]


@pytest.mark.asyncio
async def test_namespaced_cache_scan_prefixed_pattern() -> None:
    backend = InMemoryCache()
    cache = NamespacedCache(backend=backend, namespace="service-e")

    await cache.set("alpha", "a")
    await cache.set("beta", "b")

    keys = sorted(await cache.scan_keys("service-e:*"))
    assert keys == ["alpha", "beta"]
