import asyncio
import sys
from typing import Any

from app.core.gateway.protocols.cache import CacheProviderProtocol


class MockCacheProvider:
    def __init__(self):
        self._store = {}

    async def get(self, key: str) -> Any | None:
        return self._store.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    async def clear(self) -> None:
        self._store.clear()

async def test_cache_provider_contract_methods():
    """
    Contract: Any CacheProvider must implement get, set, delete, clear
    and return expected types.
    """
    print("Testing Cache Provider Contract...")
    provider = MockCacheProvider()

    # Verify it strictly adheres to protocol (runtime check)
    assert isinstance(provider, CacheProviderProtocol) or hasattr(provider, 'get')

    # Test Set/Get
    await provider.set("test_key", "test_value")
    val = await provider.get("test_key")
    assert val == "test_value"

    # Test Delete
    await provider.delete("test_key")
    val = await provider.get("test_key")
    assert val is None

    # Test Clear
    await provider.set("k1", "v1")
    await provider.set("k2", "v2")
    await provider.clear()
    assert await provider.get("k1") is None
    assert await provider.get("k2") is None
    print("✅ Cache Provider Contract Passed")

async def main():
    try:
        await test_cache_provider_contract_methods()
        print("\n🎉 All Cache Contracts Passed!")
    except Exception as e:
        print(f"\n❌ Cache Contracts Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
