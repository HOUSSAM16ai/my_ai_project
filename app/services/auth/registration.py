"""
خدمة تسجيل المستخدمين الجدد.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.user import User, UserStatus
from app.services.rbac import STANDARD_ROLE, RBACService


class RegistrationManager:
    """مسؤول عن عملية تسجيل المستخدمين الجدد."""

    def __init__(self, session: AsyncSession, rbac: RBACService) -> None:
        self.session = session
        self.rbac = rbac

    async def register_user(
        self,
        *,
        full_name: str,
        email: str,
        password: str,
    ) -> User:
        """إنشاء مستخدم جديد مع التحقق من البريد الإلكتروني وتعيين الدور الافتراضي."""
        await self.rbac.ensure_seed()
        normalized_email = email.lower().strip()
        existing = await self.session.execute(select(User).where(User.email == normalized_email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )

        user = User(
            full_name=full_name,
            email=normalized_email,
            is_admin=False,
            status=UserStatus.ACTIVE,
            is_active=True,
        )
        user.set_password(password)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        await self.rbac.assign_role(user, STANDARD_ROLE)
        return user
