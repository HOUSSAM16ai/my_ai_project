"""
مدير إبطال التخزين المؤقت (Smart Invalidation).

يوفر أدوات متقدمة لحذف وتنظيف البيانات من الذاكرة المؤقتة بذكاء،
مثل الحذف بناءً على الأنماط (Patterns) أو العلامات (Tags).
"""

import logging

from app.caching.base import CacheBackend

logger = logging.getLogger(__name__)


class InvalidationManager:
    """
    مدير استراتيجيات الإبطال (Invalidation).
    """

    def __init__(self, backend: CacheBackend) -> None:
        self.backend = backend

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        إبطال جميع المفاتيح التي تطابق نمطاً معيناً.

        Args:
            pattern: النمط (e.g. "user:123:*")

        Returns:
            int: عدد المفاتيح التي تم حذفها.
        """
        keys = await self.backend.scan_keys(pattern)
        if not keys:
            return 0

        count = 0
        for key in keys:
            if await self.backend.delete(key):
                count += 1

        logger.info(f"🧹 Invalidated {count} keys matching pattern '{pattern}'")
        return count

    async def invalidate_user_cache(self, user_id: str) -> int:
        """
        مساعد لإبطال كل ما يخص مستخدم معين.
        يفترض اتباع نمط تسمية المفاتيح: "user:{id}:*"
        """
        pattern = f"user:{user_id}:*"
        return await self.invalidate_pattern(pattern)

    async def invalidate_resource(self, resource_type: str, resource_id: str) -> int:
        """
        مساعد لإبطال كاش مورد معين.
        e.g., "product:999:details", "product:999:reviews" -> "product:999:*"
        """
        pattern = f"{resource_type}:{resource_id}:*"
        return await self.invalidate_pattern(pattern)
