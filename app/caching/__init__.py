"""
نظام التخزين المؤقت المتقدم (Advanced Caching System).

يوفر تخزين مؤقت متعدد المستويات مع استراتيجيات ذكية.
"""

__all__ = [
    "CacheBackend",
    "InMemoryCache",
    "RedisCache",
    "CacheFactory",
    "get_cache",
]

from app.caching.base import CacheBackend
from app.caching.memory_cache import InMemoryCache
from app.caching.redis_cache import RedisCache
from app.caching.factory import CacheFactory, get_cache
