"""
تنفيذ التخزين المؤقت في الذاكرة (In-Memory Cache).

يستخدم هذا التنفيذ قاموس Python بسيط مع دعم لانتهاء الصلاحية (TTL)
والحجم الأقصى (Max Size) باستخدام خوارزمية LRU (Least Recently Used) مبسطة.

المبادئ:
- البساطة: استخدام أدوات اللغة الأساسية.
- الكفاءة: عمليات O(1) في معظم الحالات.
- الأمان: استخدام AsyncIO Lock لضمان سلامة البيانات في البيئة غير المتزامنة.
"""

import asyncio
import fnmatch
import time
from collections import OrderedDict
from typing import Any

from app.caching.base import CacheBackend


class InMemoryCache(CacheBackend):
    """
    تخزين مؤقت في الذاكرة المحلية.

    المميزات:
    - سريع جداً (بدون شبكة).
    - يدعم TTL (مدة الصلاحية).
    - يدعم الحد الأقصى للعناصر (LRU Eviction).
    - آمن للتزامن (Thread-safe via asyncio.Lock).
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300) -> None:
        """
        تهيئة الذاكرة المؤقتة.

        Args:
            max_size: الحد الأقصى لعدد العناصر.
            default_ttl: مدة الصلاحية الافتراضية بالثواني.
        """
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """
        استرجاع قيمة.

        يتحقق من انتهاء الصلاحية ويحدث ترتيب LRU.
        """
        async with self._lock:
            if key not in self._cache:
                return None

            value, expire_at = self._cache[key]

            # التحقق من انتهاء الصلاحية
            if time.time() > expire_at:
                del self._cache[key]
                return None

            # تحديث ترتيب LRU (نقل للنهاية)
            self._cache.move_to_end(key)
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        تخزين قيمة.

        يطبق سياسة الطرد (Eviction) إذا امتلأت الذاكرة.
        """
        ttl_val = ttl if ttl is not None else self._default_ttl
        expire_at = time.time() + ttl_val

        async with self._lock:
            # إذا كان المفتاح موجوداً، نقوم بتحديثه ونقله للنهاية
            if key in self._cache:
                self._cache.move_to_end(key)

            self._cache[key] = (value, expire_at)

            # تطبيق سياسة الحجم الأقصى (LRU Eviction)
            if len(self._cache) > self._max_size:
                # حذف أقدم عنصر (الأول)
                self._cache.popitem(last=False)

            return True

    async def delete(self, key: str) -> bool:
        """حذف عنصر."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """التحقق من الوجود مع مراعاة الصلاحية."""
        async with self._lock:
            if key not in self._cache:
                return False

            _, expire_at = self._cache[key]
            if time.time() > expire_at:
                del self._cache[key]
                return False

            return True

    async def clear(self) -> bool:
        """مسح الكل."""
        async with self._lock:
            self._cache.clear()
            return True

    async def scan_keys(self, pattern: str) -> list[str]:
        """
        البحث عن مفاتيح تطابق نمطاً معيناً.

        Args:
            pattern: نمط البحث (e.g., "user:*"). يدعم fnmatch.

        Returns:
            list[str]: قائمة المفاتيح المطابقة الصالحة.
        """
        async with self._lock:
            keys = []
            now = time.time()
            # ننسخ المفاتيح لتجنب مشاكل التعديل أثناء التكرار إذا احتجنا لذلك،
            # لكننا هنا نقرأ فقط.
            for key, (_, expire_at) in list(self._cache.items()):
                if now > expire_at:
                    # تنظيف الكسول (Lazy cleanup) أثناء البحث قد يكون مفيداً
                    # لكن للحفاظ على سرعة البحث وتفادي التعديل، سنتجاوزها فقط
                    continue

                if fnmatch.fnmatch(key, pattern):
                    keys.append(key)
            return keys
