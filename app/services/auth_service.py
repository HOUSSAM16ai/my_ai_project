"""
خدمة المصادقة المركزية مع دعم JWT وتدوير رموز التحديث.

تعتمد هذه الخدمة على مبدأ SRP بفصل منطق المصادقة عن طبقة العرض،
وعلى مبدأ DIP بحقن الجلسة والإعدادات وخدمة RBAC.
"""
from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Final, TypedDict

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings, get_settings
from app.core.domain.models import RefreshToken, User, UserStatus, utc_now
from app.core.domain.models import pwd_context
from app.services.audit import AuditService
from app.services.rbac import ADMIN_ROLE, RBACService, STANDARD_ROLE

ACCESS_EXPIRE_MINUTES: Final[int] = 30
REFRESH_EXPIRE_DAYS: Final[int] = 14


class TokenBundle(TypedDict):
    """تمثيل منظم لحزمة الرموز المصدرة."""

    access_token: str
    refresh_token: str
    token_type: str


class AuthService:
    """
    طبقة المصادقة التطبيقية مع واجهات تسجيل الدخول، التسجيل، وتدوير الرموز.
    """

    def __init__(self, session: AsyncSession, settings: AppSettings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.rbac = RBACService(session)
        self.audit = AuditService(session)

    async def register_user(
        self,
        *,
        full_name: str,
        email: str,
        password: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """
        إنشاء مستخدم قياسي جديد مع إسناد دور STANDARD_USER.
        """

        await self.rbac.ensure_seed()
        normalized_email = email.lower().strip()
        existing = await self.session.execute(select(User).where(User.email == normalized_email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

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
        await self.audit.record(
            actor_user_id=user.id,
            action="USER_REGISTERED",
            target_type="user",
            target_id=str(user.id),
            metadata={"email_hash": self._hash_identifier(normalized_email)},
            ip=ip,
            user_agent=user_agent,
        )
        return user

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """
        مصادقة المستخدم والتحقق من حالة الحساب.
        """

        await self.rbac.ensure_seed()
        normalized_email = email.lower().strip()
        result = await self.session.execute(select(User).where(User.email == normalized_email))
        user = result.scalar_one_or_none()
        if not user or not user.password_hash or not user.check_password(password):
            await self.audit.record(
                actor_user_id=None,
                action="AUTH_FAILED",
                target_type="user",
                target_id=None,
                metadata={"email_hash": self._hash_identifier(normalized_email)},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active or user.status in {UserStatus.SUSPENDED, UserStatus.DISABLED}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
        await self.audit.record(
            actor_user_id=user.id,
            action="AUTH_SUCCEEDED",
            target_type="user",
            target_id=str(user.id),
            metadata={"status": user.status.value},
            ip=ip,
            user_agent=user_agent,
        )
        return user

    async def issue_tokens(self, user: User) -> TokenBundle:
        """
        إصدار رموز الوصول والتحديث مع تدوير آمن.
        """

        roles = await self.rbac.user_roles(user.id)
        permissions = await self.rbac.user_permissions(user.id)
        access_token = self._encode_access_token(user, roles, permissions)
        refresh_value = await self._create_refresh_token(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_value,
            "token_type": "Bearer",
        }

    def _encode_access_token(self, user: User, roles: list[str], permissions: set[str]) -> str:
        expires_delta = timedelta(minutes=min(self.settings.ACCESS_TOKEN_EXPIRE_MINUTES, ACCESS_EXPIRE_MINUTES))
        payload = {
            "sub": str(user.id),
            "roles": roles,
            "permissions": sorted(permissions),
            "jti": secrets.token_urlsafe(8),
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + expires_delta,
        }
        return jwt.encode(payload, self.settings.SECRET_KEY, algorithm="HS256")

    async def _create_refresh_token(self, user: User) -> str:
        token_id = str(uuid.uuid4())
        raw_secret = secrets.token_urlsafe(32)
        hashed = pwd_context.hash(raw_secret)
        expires_at = utc_now() + timedelta(days=REFRESH_EXPIRE_DAYS)

        record = RefreshToken(
            token_id=token_id,
            user_id=user.id,
            hashed_token=hashed,
            expires_at=expires_at,
            revoked_at=None,
            created_at=utc_now(),
        )
        self.session.add(record)
        await self.session.commit()
        return f"{token_id}:{raw_secret}"

    async def refresh_session(
        self,
        *,
        refresh_token: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenBundle:
        """
        تدوير رمز الوصول باستخدام رمز التحديث مع حماية من إعادة التشغيل.
        """

        token_id, secret = self._split_refresh_token(refresh_token)
        record = await self._get_refresh_record(token_id)
        if record is None or not record.is_active():
            await self.audit.record(
                actor_user_id=None,
                action="REFRESH_REJECTED",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"reason": "inactive_or_missing"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        if not pwd_context.verify(secret, record.hashed_token):
            await self._revoke_record(record)
            await self.audit.record(
                actor_user_id=None,
                action="REFRESH_REJECTED",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"reason": "hash_mismatch"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = await self.session.get(User, record.user_id)
        if user is None or not user.is_active:
            await self._revoke_record(record)
            await self.audit.record(
                actor_user_id=None,
                action="REFRESH_REJECTED",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"reason": "user_inactive"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

        await self._revoke_record(record)
        refreshed = await self.issue_tokens(user)
        await self.audit.record(
            actor_user_id=user.id,
            action="REFRESH_ROTATED",
            target_type="refresh_token",
            target_id=token_id,
            metadata={"status": user.status.value},
            ip=ip,
            user_agent=user_agent,
        )
        return refreshed

    async def logout(self, *, refresh_token: str, ip: str | None = None, user_agent: str | None = None) -> None:
        token_id, _ = self._split_refresh_token(refresh_token)
        record = await self._get_refresh_record(token_id)
        if record:
            await self._revoke_record(record)
            await self.audit.record(
                actor_user_id=record.user_id,
                action="LOGOUT",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"status": "revoked"},
                ip=ip,
                user_agent=user_agent,
            )

    async def _revoke_record(self, record: RefreshToken) -> None:
        record.revoke(revoked_at=utc_now())
        await self.session.commit()

    def _split_refresh_token(self, token: str) -> tuple[str, str]:
        try:
            token_id_part, secret_part = token.split(":", maxsplit=1)
            return token_id_part, secret_part
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token format") from exc

    async def _get_refresh_record(self, token_id: str) -> RefreshToken | None:
        result = await self.session.execute(select(RefreshToken).where(RefreshToken.token_id == token_id))
        return result.scalar_one_or_none()

    def verify_access_token(self, token: str) -> dict[str, object]:
        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.PyJWTError as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
        return payload

    async def promote_to_admin(self, *, user: User) -> None:
        await self.rbac.ensure_seed()
        await self.rbac.assign_role(user, ADMIN_ROLE)
        if not user.is_admin:
            await self.session.execute(update(User).where(User.id == user.id).values(is_admin=True))
            await self.session.commit()

    def _hash_identifier(self, value: str) -> str:
        """توليد بصمة نصية لحماية الهوية في سجلات التدقيق."""

        digest = sha256(value.encode()).hexdigest()
        return digest[:16]
