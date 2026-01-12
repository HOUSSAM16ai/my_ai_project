"""
تغليف مساحة الأسماء للكاش (Cache Namespace Wrapper).

يوفر هذا المكون حاجز تجريد واضح لعزل مفاتيح الكاش بين الخدمات
في بيئة API-First Microservices. كل خدمة تحصل على مساحة أسماء مستقلة
لتجنب التصادم وضمان الاستقلالية (Microservice Independence).
"""

import asyncio

from app.caching.base import CacheBackend


class NamespacedCache(CacheBackend):
    """
    غلاف كاش يضيف بادئة Namespace للمفاتيح.

    المبادئ:
    - فصل التغيير: يمكن تبديل التخزين المؤقت دون تغيير المستهلكين.
    - استقلالية الخدمات: كل خدمة تستخدم مساحة أسماء مستقلة.
    - واجهة متسقة: المستهلك يتعامل مع مفاتيح مجردة.
    """

    def __init__(self, backend: CacheBackend, namespace: str, separator: str = ":") -> None:
        """
        تهيئة غلاف مساحة الأسماء.

        Args:
            backend: مزود التخزين المؤقت الفعلي.
            namespace: مساحة الأسماء المنطقية للخدمة.
            separator: فاصل البادئة عن المفتاح.
        """
        if not namespace.strip():
            raise ValueError("namespace لا يمكن أن يكون فارغاً")
        self._backend = backend
        self._namespace = namespace.strip()
        self._separator = separator
        self._prefix = f"{self._namespace}{self._separator}"

    def _prefixed(self, key: str) -> str:
        """إضافة بادئة Namespace للمفتاح إذا لم تكن موجودة."""
        if key.startswith(self._prefix):
            return key
        return f"{self._prefix}{key}"

    def _prefixed_pattern(self, pattern: str) -> str:
        """إضافة البادئة إلى نمط البحث مع تجنب التكرار."""
        if pattern.startswith(self._prefix):
            return pattern
        return f"{self._prefix}{pattern}"

    def _strip_prefix(self, key: str) -> str:
        """إزالة بادئة Namespace لإرجاع المفاتيح بصيغة منطقية."""
        if key.startswith(self._prefix):
            return key[len(self._prefix) :]
        return key

    async def get(self, key: str) -> object | None:
        """استرجاع عنصر مع تطبيق البادئة."""
        return await self._backend.get(self._prefixed(key))

    async def set(self, key: str, value: object, ttl: int | None = None) -> bool:
        """تخزين عنصر مع تطبيق البادئة."""
        return await self._backend.set(self._prefixed(key), value, ttl=ttl)

    async def delete(self, key: str) -> bool:
        """حذف عنصر مع تطبيق البادئة."""
        return await self._backend.delete(self._prefixed(key))

    async def exists(self, key: str) -> bool:
        """التحقق من وجود عنصر مع تطبيق البادئة."""
        return await self._backend.exists(self._prefixed(key))

    async def clear(self) -> bool:
        """
        مسح مفاتيح هذه المساحة فقط.

        يتجنب التأثير على مساحات أسماء خدمات أخرى.
        """
        keys = await self._backend.scan_keys(self._prefixed_pattern("*"))
        if not keys:
            return True
        await asyncio.gather(*(self._backend.delete(key) for key in keys))
        return True

    async def scan_keys(self, pattern: str) -> list[str]:
        """البحث عن مفاتيح ضمن نفس مساحة الأسماء."""
        keys = await self._backend.scan_keys(self._prefixed_pattern(pattern))
        return [self._strip_prefix(key) for key in keys if key.startswith(self._prefix)]
