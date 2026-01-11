"""
تنفيذ التخزين المؤقت باستخدام Redis (Redis Cache).

يستخدم مكتبة redis-py (asyncio) لتوفير تخزين مؤقت موزع وعالي الأداء.
مناسب للبيئات الموزعة حيث تشترك عدة خدمات في نفس حالة التخزين المؤقت.
يتضمن حماية Circuit Breaker لضمان عدم تعطل النظام عند فشل Redis.

المتطلبات:
- خادم Redis يعمل.
- مكتبة redis-py مثبتة.
"""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.caching.base import CacheBackend
from app.core.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    get_circuit_breaker,
)

logger = logging.getLogger(__name__)


class RedisCache(CacheBackend):
    """
    تخزين مؤقت باستخدام Redis مع حماية Circuit Breaker.

    المميزات:
    - موزع (مشترك بين الخدمات).
    - دائم (اختياري).
    - محمي بـ Circuit Breaker لتجنب التأخير عند فشل الاتصال.
    """

    def __init__(
        self,
        redis_url: str,
        default_ttl: int = 300,
        breaker_config: CircuitBreakerConfig | None = None
    ) -> None:
        """
        تهيئة عميل Redis.

        Args:
            redis_url: رابط الاتصال بـ Redis (e.g., redis://localhost:6379/0)
            default_ttl: مدة الصلاحية الافتراضية بالثواني.
            breaker_config: إعدادات قاطع الدائرة (اختياري).
        """
        self._redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self._default_ttl = default_ttl

        # إعداد قاطع الدائرة
        config = breaker_config or CircuitBreakerConfig(
            failure_threshold=5,
            timeout=30.0,
            success_threshold=2
        )
        # استخدام MD5 لضمان ثبات الاسم عبر التشغيلات المختلفة
        url_hash = hashlib.md5(redis_url.encode()).hexdigest()
        self._breaker = get_circuit_breaker(f"redis_cache_breaker_{url_hash}", config)

        logger.info(f"✅ Redis Cache initialized with URL: {redis_url}")

    async def _execute_with_breaker(self, operation_name: str, func, *args, **kwargs) -> Any:
        """
        تنفيذ عملية Redis داخل قاطع الدائرة.
        """
        if not self._breaker.allow_request():
            logger.warning(f"⚠️ Redis Circuit Breaker is OPEN. Skipping {operation_name}.")
            return None

        try:
            result = await func(*args, **kwargs)
            self._breaker.record_success()
            return result
        except Exception as e:
            self._breaker.record_failure()
            logger.error(f"❌ Redis {operation_name} error: {e}")
            return None

    async def get(self, key: str) -> Any | None:
        """
        استرجاع قيمة.
        """
        # دالة مساعدة لتغليف الاستدعاء
        async def _do_get():
            value = await self._redis.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        return await self._execute_with_breaker("get", _do_get)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        تخزين قيمة.
        """
        ttl_val = ttl if ttl is not None else self._default_ttl

        async def _do_set():
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                serialized_value = str(value)

            await self._redis.set(key, serialized_value, ex=ttl_val)
            return True

        result = await self._execute_with_breaker("set", _do_set)
        return result is True

    async def delete(self, key: str) -> bool:
        """حذف عنصر."""
        async def _do_delete():
            await self._redis.delete(key)
            return True

        result = await self._execute_with_breaker("delete", _do_delete)
        return result is True

    async def exists(self, key: str) -> bool:
        """التحقق من الوجود."""
        async def _do_exists():
            return await self._redis.exists(key) > 0

        result = await self._execute_with_breaker("exists", _do_exists)
        return result is True

    async def clear(self) -> bool:
        """مسح قاعدة البيانات الحالية."""
        async def _do_clear():
            await self._redis.flushdb()
            return True

        result = await self._execute_with_breaker("clear", _do_clear)
        return result is True

    async def scan_keys(self, pattern: str) -> list[str]:
        """
        البحث عن مفاتيح.
        """
        async def _do_scan():
            keys: list[str] = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            return keys

        result = await self._execute_with_breaker("scan", _do_scan)
        return result if result is not None else []

    async def close(self) -> None:
        """إغلاق الاتصال."""
        await self._redis.close()
