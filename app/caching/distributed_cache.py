"""
التخزين المؤقت الموزع متعدد المستويات (Distributed Multi-Level Caching).

يجمع هذا المكون بين سرعة الذاكرة المحلية (L1) وقدرة التخزين الموزع (L2 Redis)
لتحقيق أفضل أداء ممكن مع الحفاظ على الاتساق.

المعمارية:
- L1: In-Memory (سريع جداً، محلي لكل نسخة خدمة).
- L2: Redis (موزع، مشترك بين جميع النسخ).
"""

import logging
from typing import Any

from app.caching.base import CacheBackend

logger = logging.getLogger(__name__)


class MultiLevelCache(CacheBackend):
    """
    منسق التخزين المؤقت متعدد الطبقات.
    """

    def __init__(
        self,
        l1_cache: CacheBackend,
        l2_cache: CacheBackend,
        sync_l1: bool = True
    ) -> None:
        """
        تهيئة المنسق.

        Args:
            l1_cache: المستوى الأول (Memory).
            l2_cache: المستوى الثاني (Redis).
            sync_l1: هل نقوم بملء L1 عند العثور على القيمة في L2؟
        """
        self.l1 = l1_cache
        self.l2 = l2_cache
        self.sync_l1 = sync_l1

    async def get(self, key: str) -> Any | None:
        """
        استرجاع قيمة.

        الاستراتيجية:
        1. التحقق من L1.
        2. إذا لم توجد، التحقق من L2.
        3. إذا وجدت في L2، تحديث L1 (Read-Through).
        """
        # 1. Check L1
        val = await self.l1.get(key)
        if val is not None:
            return val

        # 2. Check L2
        val = await self.l2.get(key)
        if val is not None:
            # 3. Populate L1 (Backfill)
            if self.sync_l1:
                # نستخدم TTL افتراضي قصير للـ L1 لتجنب البيانات القديمة
                await self.l1.set(key, val, ttl=60)
            return val

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        تخزين قيمة.

        الاستراتيجية:
        1. الكتابة في L2 أولاً (لضمان التوزيع).
        2. الكتابة في L1 (أو إبطالها).
        """
        # Write to L2 (Source of Truth for distribution)
        l2_success = await self.l2.set(key, value, ttl=ttl)

        if l2_success:
            # Write to L1
            await self.l1.set(key, value, ttl=ttl)

            # TODO: Publish invalidation event for other instances
            # (سنقوم بتنفيذ هذا في مرحلة لاحقة عبر Pub/Sub)

        return l2_success

    async def delete(self, key: str) -> bool:
        """
        حذف قيمة.

        يحذف من كلا المستويين.
        """
        l2_res = await self.l2.delete(key)
        l1_res = await self.l1.delete(key)
        return l2_res or l1_res

    async def exists(self, key: str) -> bool:
        """التحقق من الوجود (في أي مستوى)."""
        if await self.l1.exists(key):
            return True
        return await self.l2.exists(key)

    async def clear(self) -> bool:
        """مسح الكل."""
        l1 = await self.l1.clear()
        l2 = await self.l2.clear()
        return l1 and l2

    async def scan_keys(self, pattern: str) -> list[str]:
        """
        البحث عن المفاتيح.

        يعتمد بشكل أساسي على L2 لأنه يحتوي على المجموعة الشاملة.
        """
        return await self.l2.scan_keys(pattern)
