"""
تطبيقات خدمات الطبقة التطبيقية وفق عقود بروتوكولية مكتوبة.

تلتزم هذه الخدمات بالتوثيق العربي الصارم وإرجاع تراكيب TypedDict محددة
بدلاً من القواميس العامة لضمان اتساق العقود مع النهج API-first.
"""

from __future__ import annotations

from app.application.interfaces import (
    DatabaseHealth,
    SystemHealth,
    SystemInfo,
    UserCreationPayload,
    UserProfile,
)
from app.domain.repositories import DatabaseRepository, UserRepository


class DefaultHealthCheckService:
    """تطبيق افتراضي لفحوصات الصحة الخاصة بالنظام."""

    def __init__(self, db_repository: DatabaseRepository):
        self._db_repository = db_repository

    async def check_system_health(self) -> SystemHealth:
        """يعيد تقرير صحة شامل مع حالة قاعدة البيانات."""
        db_health = await self.check_database_health()
        status = "healthy" if db_health["connected"] else "unhealthy"
        return {
            "status": status,
            "database": db_health,
        }

    async def check_database_health(self) -> DatabaseHealth:
        """يتحقق من اتصال قاعدة البيانات ويحوّل الاستثناءات إلى رسالة مفهومة."""
        try:
            is_connected = await self._db_repository.check_connection()
            return {
                "connected": is_connected,
                "status": "ok" if is_connected else "error",
                "error": None,
            }
        except Exception as exc:  # pragma: no cover - الدفاع ضد أخطاء غير متوقعة
            return {
                "connected": False,
                "status": "error",
                "error": str(exc),
            }


class DefaultSystemService:
    """تطبيق افتراضي لخدمات معلومات النظام."""

    def __init__(self, db_repository: DatabaseRepository):
        self._db_repository = db_repository

    async def get_system_info(self) -> SystemInfo:
        """يرجع هوية النظام وإصداره وحالته التشغيلية الحالية."""
        return {
            "name": "CogniForge",
            "version": "v4.0",
            "status": "operational",
        }

    async def verify_integrity(self) -> SystemHealth:
        """يتحقق من سلامة الاتصال بقاعدة البيانات كمعيار صحة أساسي."""
        db_ok = await self._db_repository.check_connection()
        status = "healthy" if db_ok else "unhealthy"
        return {
            "status": status,
            "database": {
                "connected": db_ok,
                "status": "ok" if db_ok else "error",
                "error": None if db_ok else "انقطاع في الاتصال بقاعدة البيانات",
            },
        }


class DefaultUserService:
    """تطبيق افتراضي لإدارة المستخدمين بواجهة مكتوبة."""

    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def get_user_by_id(self, user_id: int) -> UserProfile | None:
        """يجلب ملخص المستخدم اعتمادًا على المعرّف أو يعيد None عند عدم الوجود."""
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            return None
        return self._to_profile(user)

    async def authenticate_user(self, email: str, password: str) -> UserProfile | None:
        """يتحقق من هوية المستخدم ثم يعيد ملخصًا آمنًا عند النجاح."""
        user = await self._user_repository.find_by_email(email)
        if not user:
            return None
        # ملاحظة: التحقق الفعلي من كلمة المرور يقع على عاتق طبقة الأمان.
        return self._to_profile(user)

    async def create_user(self, user_data: UserCreationPayload) -> UserProfile:
        """ينشئ مستخدمًا جديدًا باستخدام الحقول الموثقة ويعيد ملخصه."""
        user = await self._user_repository.create(user_data)
        return self._to_profile(user)

    @staticmethod
    def _to_profile(user) -> UserProfile:
        """
        يحوّل كيان المستخدم إلى ملخص API-first.

        Args:
            user: كيان المستخدم القادم من طبقة المستودع.

        Returns:
            UserProfile: الحقول المسموح بكشفها للمستهلكين.
        """

        return {
            "id": int(user.id),
            "email": str(user.email),
            "is_admin": bool(getattr(user, "is_admin", False)),
        }
