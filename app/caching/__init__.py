"""
حزمة التخزين المؤقت (Caching Package).

توفر واجهات وتنفيذات لنظام التخزين المؤقت المتقدم.
"""

from app.caching.base import CacheBackend
from app.caching.distributed_cache import MultiLevelCache
from app.caching.invalidation import InvalidationManager
from app.caching.memory_cache import InMemoryCache
from app.caching.redis_cache import RedisCache
from app.caching.strategies import (
    EvictionPolicy,
    LFUPolicy,
    LRUPolicy,
    StrategicMemoryCache,
)

__all__ = [
    "CacheBackend",
    "InMemoryCache",
    "RedisCache",
    "EvictionPolicy",
    "LRUPolicy",
    "LFUPolicy",
    "StrategicMemoryCache",
    "MultiLevelCache",
    "InvalidationManager",
]
