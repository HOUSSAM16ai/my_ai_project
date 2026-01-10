"""
طبقة تدقيق مركزية لتسجيل العمليات الحساسة.

تُستخدم هذه الخدمة في مسارات الإدارة والسياسات الأمنية لضمان أثر تتبع واضح
وقابل للتدقيق، بما يتماشى مع متطلبات الامتثال وحوكمة الأمن.
"""
from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.models import AuditLog, utc_now


class AuditService:
    """
    خدمة تسجيل أحداث التدقيق مع حقن التبعية للجلسة.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        actor_user_id: int | None,
        action: str,
        target_type: str,
        target_id: str | None,
        metadata: Mapping[str, object],
        ip: str | None,
        user_agent: str | None,
    ) -> AuditLog:
        """
        إنشاء سجل تدقيق جديد مع طابع زمني.
        """

        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=dict(metadata),
            ip=ip,
            user_agent=user_agent,
            created_at=utc_now(),
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry
