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
from app.caching.namespace_cache import NamespacedCache
from app.core.agents.principles import resolve_autonomy_namespace

if TYPE_CHECKING:
    pass

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
            socket_timeout = CacheFactory._get_float_env("REDIS_SOCKET_TIMEOUT")
            connect_timeout = CacheFactory._get_float_env("REDIS_SOCKET_CONNECT_TIMEOUT")
            health_check_interval = CacheFactory._get_int_env("REDIS_HEALTH_CHECK_INTERVAL")
            from app.caching.redis_cache import RedisCache

            backend = RedisCache(
                redis_url=redis_url,
                ttl_jitter_ratio=ttl_jitter_ratio,
                socket_timeout=socket_timeout,
                socket_connect_timeout=connect_timeout,
                health_check_interval=health_check_interval,
            )
        else:
            backend = InMemoryCache(ttl_jitter_ratio=ttl_jitter_ratio)

        namespace = CacheFactory._get_cache_namespace()
        if namespace:
            return NamespacedCache(backend=backend, namespace=namespace)
        return backend

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

    @staticmethod
    def _get_cache_namespace() -> str | None:
        """تحديد مساحة أسماء الكاش لضمان استقلالية الخدمات."""
        return resolve_autonomy_namespace(os.environ)

    @staticmethod
    def _get_float_env(name: str) -> float | None:
        """قراءة قيمة رقمية اختيارية من متغير البيئة."""
        raw_value = os.getenv(name)
        if raw_value is None:
            return None
        try:
            return float(raw_value)
        except ValueError as exc:
            raise ValueError(f"{name} يجب أن يكون رقماً عشرياً") from exc

    @staticmethod
    def _get_int_env(name: str) -> int | None:
        """قراءة قيمة عددية صحيحة اختيارية من متغير البيئة."""
        raw_value = os.getenv(name)
        if raw_value is None:
            return None
        try:
            return int(raw_value)
        except ValueError as exc:
            raise ValueError(f"{name} يجب أن يكون رقماً صحيحاً") from exc


def get_cache() -> CacheBackend:
    """دالة مساعدة سهلة للوصول للمخزن المؤقت."""
    return CacheFactory.get_cache()
