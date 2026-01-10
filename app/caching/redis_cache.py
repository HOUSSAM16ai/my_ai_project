"""
تنفيذ التخزين المؤقت باستخدام Redis (Redis Cache).

يستخدم مكتبة redis-py (asyncio) لتوفير تخزين مؤقت موزع وعالي الأداء.
مناسب للبيئات الموزعة حيث تشترك عدة خدمات في نفس حالة التخزين المؤقت.

المتطلبات:
- خادم Redis يعمل.
- مكتبة redis-py مثبتة.
"""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.caching.base import CacheBackend

logger = logging.getLogger(__name__)


class RedisCache(CacheBackend):
    """
    تخزين مؤقت باستخدام Redis.

    المميزات:
    - موزع (مشترك بين الخدمات).
    - دائم (اختياري).
    - يدعم هياكل بيانات معقدة (هنا نستخدم السلاسل البسيطة مع JSON).
    """

    def __init__(self, redis_url: str, default_ttl: int = 300) -> None:
        """
        تهيئة عميل Redis.

        Args:
            redis_url: رابط الاتصال بـ Redis (e.g., redis://localhost:6379/0)
            default_ttl: مدة الصلاحية الافتراضية بالثواني.
        """
        self._redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self._default_ttl = default_ttl
        logger.info(f"✅ Redis Cache initialized with URL: {redis_url}")

    async def get(self, key: str) -> Any | None:
        """
        استرجاع قيمة.

        يقوم بفك تشفير JSON تلقائياً.
        """
        try:
            value = await self._redis.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"❌ Redis get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        تخزين قيمة.

        يقوم بتشفير القيمة كـ JSON قبل التخزين.
        """
        try:
            ttl_val = ttl if ttl is not None else self._default_ttl

            # محاولة تحويل القيمة لـ JSON، وإذا فشل نستخدم النص كما هو
            try:
                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                serialized_value = str(value)

            await self._redis.set(key, serialized_value, ex=ttl_val)
            return True
        except Exception as e:
            logger.error(f"❌ Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """حذف عنصر."""
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"❌ Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """التحقق من الوجود."""
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"❌ Redis exists error for key {key}: {e}")
            return False

    async def clear(self) -> bool:
        """مسح قاعدة البيانات الحالية (FLUSHDB)."""
        try:
            await self._redis.flushdb()
            return True
        except Exception as e:
            logger.error(f"❌ Redis clear error: {e}")
            return False

    async def scan_keys(self, pattern: str) -> list[str]:
        """
        البحث عن مفاتيح تطابق نمطاً معيناً باستخدام SCAN.

        Args:
            pattern: نمط البحث (e.g., "user:*")

        Returns:
            list[str]: قائمة المفاتيح المطابقة
        """
        keys: list[str] = []
        try:
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            return keys
        except Exception as e:
            logger.error(f"❌ Redis scan error for pattern {pattern}: {e}")
            return []

    async def close(self) -> None:
        """إغلاق الاتصال."""
        await self._redis.close()
