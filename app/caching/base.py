"""
واجهة نظام التخزين المؤقت (Caching Protocol).

تحدد هذه الواجهة العقد الذي يجب أن تلتزم به جميع تطبيقات التخزين المؤقت.
تتبع مبدأ فصل التجريد عن التنفيذ (Berkeley SICP) وتستخدم توثيق هارفارد.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CacheBackend(Protocol):
    """
    بروتوكول الواجهة الخلفية للتخزين المؤقت.

    يجب أن تدعم جميع عمليات التخزين المؤقت الأساسية بشكل غير متزامن.
    """

    async def get(self, key: str) -> object | None:
        """
        استرجاع قيمة من الذاكرة المؤقتة.

        Args:
            key: مفتاح القيمة

        Returns:
            object | None: القيمة المخزنة أو None إذا لم تكن موجودة
        """
        ...

    async def set(
        self,
        key: str,
        value: object,
        ttl: int | None = None,
    ) -> bool:
        """
        تخزين قيمة في الذاكرة المؤقتة.

        Args:
            key: مفتاح القيمة
            value: القيمة المراد تخزينها
            ttl: مدة الصلاحية بالثواني (اختياري)

        Returns:
            bool: True إذا تم التخزين بنجاح
        """
        ...

    async def delete(self, key: str) -> bool:
        """
        حذف قيمة من الذاكرة المؤقتة.

        Args:
            key: مفتاح القيمة

        Returns:
            bool: True إذا تم الحذف بنجاح
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        التحقق من وجود مفتاح في الذاكرة المؤقتة.

        Args:
            key: مفتاح القيمة

        Returns:
            bool: True إذا كان المفتاح موجوداً
        """
        ...

    async def clear(self) -> bool:
        """
        مسح جميع البيانات من الذاكرة المؤقتة.

        Returns:
            bool: True إذا تم المسح بنجاح
        """
        ...

    async def scan_keys(self, pattern: str) -> list[str]:
        """
        البحث عن مفاتيح تطابق نمطاً معيناً.

        Args:
            pattern: نمط البحث (e.g., "user:*")

        Returns:
            list[str]: قائمة المفاتيح المطابقة
        """
        ...

    async def set_add(self, key: str, members: list[str], ttl: int | None = None) -> bool:
        """
        إضافة عناصر إلى مجموعة (Set).
        مفيد لإدارة العلامات (Tags) والعلاقات.

        Args:
            key: مفتاح المجموعة
            members: العناصر المراد إضافتها
            ttl: مدة الصلاحية (اختياري)

        Returns:
            bool: True إذا تمت العملية بنجاح
        """
        ...

    async def set_remove(self, key: str, members: list[str]) -> bool:
        """
        حذف عناصر من مجموعة.

        Args:
            key: مفتاح المجموعة
            members: العناصر المراد حذفها

        Returns:
            bool: True إذا تمت العملية بنجاح
        """
        ...

    async def set_members(self, key: str) -> set[str]:
        """
        الحصول على جميع عناصر المجموعة.

        Args:
            key: مفتاح المجموعة

        Returns:
            set[str]: مجموعة العناصر
        """
        ...


@runtime_checkable
class PubSubBackend(Protocol):
    """
    بروتوكول للنشر والاشتراك (للتخزين المؤقت الموزع).
    """

    async def publish(self, channel: str, message: str) -> int:
        """نشر رسالة إلى قناة."""
        ...

    def pubsub(self) -> Any:
        """الحصول على كائن PubSub."""
        ...
