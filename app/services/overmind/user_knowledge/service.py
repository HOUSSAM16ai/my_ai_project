"""
خدمة معرفة المستخدمين الموحدة (Unified User Knowledge Service).

Facade Pattern يوفر واجهة موحدة لجميع عمليات معرفة المستخدمين.

المبادئ:
- Facade Pattern: واجهة بسيطة لنظام معقد
- Dependency Injection: حقن التبعيات
- Context Manager: إدارة الموارد تلقائياً
"""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.di import get_logger
from app.services.overmind.user_knowledge.basic_info import (
    get_user_basic_info,
    list_all_users,
)
from app.services.overmind.user_knowledge.performance import get_user_performance
from app.services.overmind.user_knowledge.relations import get_user_relations
from app.services.overmind.user_knowledge.search import search_users
from app.services.overmind.user_knowledge.statistics import get_user_statistics

logger = get_logger(__name__)


class UserKnowledge:
    """
    معرفة المستخدم الشاملة (Comprehensive User Knowledge).

    Facade Pattern يوفر واجهة موحدة لجميع عمليات معرفة المستخدمين:
    - من هو؟ (الهوية)
    - ماذا يفعل؟ (النشاطات)
    - كيف يتصرف؟ (السلوك)
    - ماذا يفضل؟ (التفضيلات)
    - كيف أداؤه؟ (المقاييس)

    الاستخدام:
        >>> async with UserKnowledge() as uk:
        >>>     user_info = await uk.get_user_complete_profile(user_id=1)
        >>>     print(user_info['basic']['name'])
        >>>     print(user_info['statistics']['total_missions'])
    """

    def __init__(self) -> None:
        """تهيئة نظام معرفة المستخدمين."""
        self._session: AsyncSession | None = None

    async def __aenter__(self):
        """فتح الجلسة (Context Manager)."""
        async for session in get_db():
            self._session = session
            break
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """إغلاق الجلسة."""
        if self._session:
            await self._session.close()

    # =========================================================================
    # المعلومات الأساسية (Basic Information)
    # =========================================================================

    async def get_user_basic_info(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على المعلومات الأساسية للمستخدم.

        Args:
            user_id: معرّف المستخدم

        Returns:
            dict: المعلومات الأساسية
        """
        if not self._session:
            return {}
        return await get_user_basic_info(self._session, user_id)

    # =========================================================================
    # الإحصائيات والنشاطات (Statistics & Activities)
    # =========================================================================

    async def get_user_statistics(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على إحصائيات المستخدم.

        Args:
            user_id: معرّف المستخدم

        Returns:
            dict: إحصائيات شاملة
        """
        if not self._session:
            return {}
        return await get_user_statistics(self._session, user_id)

    # =========================================================================
    # السلوك والأداء (Behavior & Performance)
    # =========================================================================

    async def get_user_performance(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على مقاييس أداء المستخدم.

        Args:
            user_id: معرّف المستخدم

        Returns:
            dict: مقاييس الأداء
        """
        if not self._session:
            return {}
        return await get_user_performance(self._session, user_id)

    # =========================================================================
    # العلاقات والروابط (Relations & Connections)
    # =========================================================================

    async def get_user_relations(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على علاقات المستخدم مع الكيانات الأخرى.

        Args:
            user_id: معرّف المستخدم

        Returns:
            dict: العلاقات والروابط
        """
        if not self._session:
            return {}
        return await get_user_relations(self._session, user_id)

    # =========================================================================
    # الملف الشامل (Complete Profile)
    # =========================================================================

    async def get_user_complete_profile(self, user_id: int) -> dict[str, Any]:
        """
        الحصول على الملف الشخصي الكامل والشامل للمستخدم.

        Args:
            user_id: معرّف المستخدم

        Returns:
            dict: الملف الشخصي الكامل

        يجمع جميع المعلومات:
            - basic: المعلومات الأساسية
            - statistics: الإحصائيات
            - performance: مقاييس الأداء
            - relations: العلاقات
        """
        logger.info(f"Building complete profile for user {user_id}")

        # جمع جميع المعلومات
        basic = await self.get_user_basic_info(user_id)

        if not basic:
            logger.warning(f"User {user_id} not found")
            return {
                "error": "User not found",
                "user_id": user_id,
            }

        statistics = await self.get_user_statistics(user_id)
        performance = await self.get_user_performance(user_id)
        relations = await self.get_user_relations(user_id)

        profile = {
            "user_id": user_id,
            "basic": basic,
            "statistics": statistics,
            "performance": performance,
            "relations": relations,
            "generated_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Complete profile generated for user {user_id}")
        return profile

    # =========================================================================
    # قائمة المستخدمين (Users List)
    # =========================================================================

    async def list_all_users(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        عرض قائمة جميع المستخدمين مع معلومات مختصرة.

        Args:
            limit: عدد المستخدمين المطلوب
            offset: الإزاحة (للصفحات)

        Returns:
            list[dict]: قائمة المستخدمين
        """
        if not self._session:
            return []
        return await list_all_users(self._session, limit, offset)

    # =========================================================================
    # البحث (Search)
    # =========================================================================

    async def search_users(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        البحث عن مستخدمين.

        Args:
            query: نص البحث (اسم أو بريد)
            limit: عدد النتائج

        Returns:
            list[dict]: نتائج البحث
        """
        if not self._session:
            return []
        return await search_users(self._session, query, limit)
