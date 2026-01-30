from __future__ import annotations

from typing import Protocol

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.user import User
from app.services.system.domain import DatabasePulse


class DatabaseConnectionDiagnostic(Protocol):
    """بروتوكول فحص اتصال قاعدة البيانات وفق مبدأ الفصل بين الواجهات."""

    async def evaluate(self, session: AsyncSession) -> DatabasePulse:
        """ينفذ فحص الاتصال باستخدام الجلسة المعطاة ويعيد نتيجة مفصلة."""


class AdminPresenceDiagnostic(Protocol):
    """بروتوكول للتحقق من وجود مستخدم مسؤول معزول عن التفاصيل التحتية."""

    async def admin_exists(self, session: AsyncSession) -> bool:
        """يتحقق من توفر حساب المسؤول بناءً على معايير قابلة للتهيئة."""


class SQLAlchemyConnectionDiagnostic:
    """تطبيق لفحص الاتصال يعتمد على SQLAlchemy دون كشف تفاصيله للمستدعي."""

    def __init__(self, health_query: str = "SELECT 1"):
        self._health_query = text(health_query)

    async def evaluate(self, session: AsyncSession) -> DatabasePulse:
        """ينفذ استعلام نبض بسيط ويحول الاستثناءات إلى بنية مفهومة."""
        try:
            await session.execute(self._health_query)
            return {
                "connected": True,
                "status": "healthy",
                "error": None,
            }
        except Exception as exc:  # pragma: no cover - دفاع ضد أخطاء غير متوقعة
            return {
                "connected": False,
                "status": "unhealthy",
                "error": str(exc),
            }


class SQLAlchemyAdminPresenceDiagnostic:
    """تطبيق يتحقق من وجود حساب مسؤول محدد عبر استعلام SQLAlchemy."""

    def __init__(self, admin_email: str):
        self._admin_email = admin_email

    async def admin_exists(self, session: AsyncSession) -> bool:
        """يستخدم استعلامًا آمنًا للتحقق من وجود الحساب المطلوب."""
        result = await session.execute(
            select(User.id).where(User.email == self._admin_email).limit(1)
        )
        return result.scalars().first() is not None
