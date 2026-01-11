"""
مصنع التخزين المؤقت (Cache Factory).

نمط المصنع (Factory Pattern) لإنشاء وإدارة مثيل التخزين المؤقت المناسب
بناءً على الإعدادات البيئية.

يخفي تفاصيل الإنشاء ويوفر نقطة وصول مركزية (Singleton-like).
"""

import os
from typing import TYPE_CHECKING, Literal

from app.caching.base import CacheBackend
from app.caching.memory_cache import InMemoryCache

if TYPE_CHECKING:
    from app.caching.redis_cache import RedisCache

# نوع الواجهة الخلفية (Backend Type)
CacheBackendType = Literal["memory", "redis"]


class CacheFactory:
    """
    مصنع لإنشاء موفري خدمة التخزين المؤقت.
    """

    _instance: CacheBackend | None = None

    @classmethod
    def get_cache(cls) -> CacheBackend:
        """
        الحصول على مثيل التخزين المؤقت العام (Singleton).

        إذا لم يتم تهيئته، يقوم بإنشاء الإعداد الافتراضي بناءً على متغيرات البيئة.
        """
        if cls._instance is None:
            cls._instance = cls.create_cache()
        return cls._instance

    @staticmethod
    def create_cache() -> CacheBackend:
        """
        إنشاء مثيل جديد بناءً على البيئة.

        يبحث عن متغير البيئة `CACHE_TYPE`:
        - 'redis': يستخدم Redis (يتطلب `REDIS_URL`).
        - 'memory' (الافتراضي): يستخدم InMemoryCache.
        """
        cache_type = os.getenv("CACHE_TYPE", "memory").lower()
        ttl_jitter_ratio = CacheFactory._get_ttl_jitter_ratio()

        if cache_type == "redis":
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            from app.caching.redis_cache import RedisCache

            return RedisCache(redis_url=redis_url, ttl_jitter_ratio=ttl_jitter_ratio)

        # الافتراضي: ذاكرة
        return InMemoryCache(ttl_jitter_ratio=ttl_jitter_ratio)

    @staticmethod
    def _get_ttl_jitter_ratio() -> float:
        """قراءة نسبة عشوائية TTL من متغير البيئة."""

        raw_value = os.getenv("CACHE_TTL_JITTER_RATIO")
        if raw_value is None:
            return 0.0
        try:
            return float(raw_value)
        except ValueError as exc:
            raise ValueError("CACHE_TTL_JITTER_RATIO يجب أن يكون رقماً عشرياً") from exc


def get_cache() -> CacheBackend:
    """دالة مساعدة سهلة للوصول للمخزن المؤقت."""
    return CacheFactory.get_cache()
