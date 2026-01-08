"""
مدير كلمات المرور واستعادة الحساب.
"""
from __future__ import annotations

import secrets
from datetime import timedelta
from hashlib import sha256
from typing import Final

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.models import PasswordResetToken, User, utc_now

PASSWORD_RESET_EXPIRE_MINUTES: Final[int] = 30


class PasswordManager:
    """مسؤول عن إدارة طلبات إعادة تعيين كلمة المرور والتحقق من الرموز."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_reset_token(
        self,
        user: User,
        ip: str | None,
        user_agent: str | None,
    ) -> tuple[str, int, PasswordResetToken]:
        """إنشاء رمز لإعادة تعيين كلمة المرور."""
        token_value = secrets.token_urlsafe(32)
        hashed = sha256(token_value.encode()).hexdigest()
        expires_at = utc_now() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
        record = PasswordResetToken(
            hashed_token=hashed,
            user_id=user.id,
            expires_at=expires_at,
            requested_ip=ip,
            user_agent=user_agent,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return token_value, PASSWORD_RESET_EXPIRE_MINUTES * 60, record

    async def verify_and_redeem_token(self, token: str) -> User:
        """التحقق من صحة رمز الاستعادة واسترجاع المستخدم المرتبط."""
        hashed = sha256(token.encode()).hexdigest()
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.hashed_token == hashed)
        )
        record = result.scalar_one_or_none()
        if not record or not record.is_active():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
            )

        user = await self.session.get(User, record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User missing for reset"
            )

        record.mark_redeemed()
        # Note: We rely on the caller to commit the transaction after updating the password
        return user
