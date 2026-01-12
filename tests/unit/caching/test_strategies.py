"""
اختبارات استراتيجيات التخزين المؤقت.
"""

import asyncio

from app.caching.strategies import LFUPolicy, LRUPolicy, StrategicMemoryCache


class TestLRUPolicy:
    def test_lru_eviction(self):
        """اختبار طرد العنصر الأقل استخداماً مؤخراً."""
        policy = LRUPolicy[str](capacity=2)

        # Add A, B
        assert policy.on_add("A") is None
        assert policy.on_add("B") is None

        # Access A (A becomes most recent, B becomes least recent)
        policy.on_access("A")

        # Add C -> Should evict B
        evicted = policy.on_add("C")
        assert evicted == "B"

        # Current state: A (old), C (new)
        # Add D -> Should evict A
        evicted = policy.on_add("D")
        assert evicted == "A"


class TestLFUPolicy:
    def test_lfu_eviction(self):
        """اختبار طرد العنصر الأقل تكراراً."""
        policy = LFUPolicy[str](capacity=2)

        # Add A, B
        policy.on_add("A")
        policy.on_access("A")  # Count: 1
        policy.on_access("A")  # Count: 2

        policy.on_add("B")
        policy.on_access("B")  # Count: 1

        # Add C -> Should evict B (Count 1 < Count 2)
        evicted = policy.on_add("C")
        assert evicted == "B"


class TestStrategicCache:
    def test_integration_with_lru(self):
        """اختبار التكامل مع الذاكرة الاستراتيجية."""
        policy = LRUPolicy[str](capacity=2)
        cache = StrategicMemoryCache(policy)

        async def run_test():
            await cache.set("k1", "v1")
            await cache.set("k2", "v2")

            # Access k1
            assert await cache.get("k1") == "v1"

            # Add k3 -> Evicts k2 (since k1 was just accessed)
            await cache.set("k3", "v3")

            assert await cache.get("k2") is None
            assert await cache.get("k1") == "v1"
            assert await cache.get("k3") == "v3"

        asyncio.run(run_test())
