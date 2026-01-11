"""
حزمة التخزين المؤقت (Caching Package).

توفر واجهات وتنفيذات لنظام التخزين المؤقت المتقدم.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.caching.base import CacheBackend
from app.caching.distributed_cache import MultiLevelCache
from app.caching.invalidation import InvalidationManager
from app.caching.memory_cache import InMemoryCache
from app.caching.stats import CacheStatsSnapshot, MultiLevelCacheStatsSnapshot
from app.caching.strategies import (
    EvictionPolicy,
    LFUPolicy,
    LRUPolicy,
    StrategicMemoryCache,
)

if TYPE_CHECKING:
    from app.caching.redis_cache import RedisCache

__all__ = [
    "CacheBackend",
    "CacheStatsSnapshot",
    "EvictionPolicy",
    "InMemoryCache",
    "InvalidationManager",
    "LFUPolicy",
    "LRUPolicy",
    "MultiLevelCacheStatsSnapshot",
    "MultiLevelCache",
    "RedisCache",
    "StrategicMemoryCache",
]


def __getattr__(name: str) -> object:
    """تحميل كسول لبعض الوحدات الثقيلة مثل Redis."""

    if name == "RedisCache":
        from app.caching.redis_cache import RedisCache

        return RedisCache
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
