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
from app.core.domain.models import PasswordResetToken, RefreshToken, User, UserStatus, utc_now
from app.core.domain.models import pwd_context
from app.services.audit import AuditService
from app.services.rbac import ADMIN_ROLE, RBACService, STANDARD_ROLE

ACCESS_EXPIRE_MINUTES: Final[int] = 30
REFRESH_EXPIRE_DAYS: Final[int] = 14
REAUTH_EXPIRE_MINUTES: Final[int] = 10
PASSWORD_RESET_EXPIRE_MINUTES: Final[int] = 30


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

    async def issue_tokens(
        self,
        user: User,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> TokenBundle:
        """
        إصدار رموز الوصول والتحديث مع تدوير آمن.
        """

        roles = await self.rbac.user_roles(user.id)
        permissions = await self.rbac.user_permissions(user.id)
        access_token = self._encode_access_token(user, roles, permissions)
        refresh_value = await self._create_refresh_token(
            user, ip=ip, user_agent=user_agent, family_id=None
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_value,
            "token_type": "Bearer",
        }

    async def update_profile(
        self,
        *,
        user: User,
        full_name: str | None,
        email: str | None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        """
        تحديث بيانات الحساب الذاتي مع التحقق من التفرد والأثر التدقيقي.
        """

        await self.rbac.ensure_seed()
        changed_fields: list[str] = []

        if full_name and full_name.strip() and full_name != user.full_name:
            user.full_name = full_name.strip()
            changed_fields.append("full_name")

        if email:
            normalized_email = email.lower().strip()
            if normalized_email != user.email:
                conflict = await self.session.execute(
                    select(User).where(User.email == normalized_email, User.id != user.id)
                )
                if conflict.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use"
                    )
                user.email = normalized_email
                changed_fields.append("email")

        if not changed_fields:
            return user

        await self.session.commit()
        await self.session.refresh(user)
        await self.audit.record(
            actor_user_id=user.id,
            action="PROFILE_UPDATED",
            target_type="user",
            target_id=str(user.id),
            metadata={"fields": changed_fields},
            ip=ip,
            user_agent=user_agent,
        )
        return user

    async def issue_reauth_proof(
        self,
        *,
        user: User,
        password: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, int]:
        """
        إصدار رمز إعادة مصادقة قصير العمر لتلبية متطلبات "كسر الزجاج".

        يتأكد هذا التابع من صحة كلمة المرور الحالية قبل إنشاء رمز JWT
        مخصص لغرض إعادة المصادقة فقط، مع مدة صلاحية مقيدة تقلل خطر
        إعادة الاستخدام في حال تسرب الرمز.
        """

        if not user.check_password(password):
            await self.audit.record(
                actor_user_id=user.id,
                action="REAUTH_REJECTED",
                target_type="user",
                target_id=str(user.id),
                metadata={"reason": "bad_password"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Re-authentication required")

        token, expires_in = self._encode_reauth_token(user)
        await self.audit.record(
            actor_user_id=user.id,
            action="REAUTH_SUCCEEDED",
            target_type="user",
            target_id=str(user.id),
            metadata={"expires_in": expires_in},
            ip=ip,
            user_agent=user_agent,
        )
        return token, expires_in

    async def verify_reauth_proof(
        self,
        token: str,
        *,
        user: User,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        التحقق من رمز إعادة المصادقة وضمان تطابق الهوية والغرض.
        """

        try:
            payload = jwt.decode(token, self.settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.PyJWTError as exc:  # noqa: BLE001
            await self.audit.record(
                actor_user_id=user.id,
                action="REAUTH_REJECTED",
                target_type="user",
                target_id=str(user.id),
                metadata={"reason": "invalid_or_expired"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Re-authentication required") from exc

        if payload.get("purpose") != "reauth" or payload.get("sub") != str(user.id):
            await self.audit.record(
                actor_user_id=user.id,
                action="REAUTH_REJECTED",
                target_type="user",
                target_id=str(user.id),
                metadata={"reason": "subject_mismatch"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Re-authentication required")

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

    def _encode_reauth_token(self, user: User) -> tuple[str, int]:
        expires_delta = timedelta(
            minutes=min(self.settings.REAUTH_TOKEN_EXPIRE_MINUTES, REAUTH_EXPIRE_MINUTES)
        )
        payload = {
            "sub": str(user.id),
            "purpose": "reauth",
            "jti": secrets.token_urlsafe(8),
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + expires_delta,
        }
        token = jwt.encode(payload, self.settings.SECRET_KEY, algorithm="HS256")
        return token, int(expires_delta.total_seconds())

    async def _create_refresh_token(
        self,
        user: User,
        *,
        family_id: str | None,
        ip: str | None,
        user_agent: str | None,
    ) -> str:
        """
        إنشاء رمز تحديث جديد داخل عائلة تدوير واحدة مع تتبع سياق العميل.

        الهدف هو ربط كل رموز التحديث الصادرة لجلسة واحدة بمعرّف عائلة
        family_id لضمان كشف إعادة الاستخدام وإيقاف العائلة بالكامل عند اكتشاف
        أي محاولة اختراق.
        """
        token_id = str(uuid.uuid4())
        raw_secret = secrets.token_urlsafe(32)
        hashed = pwd_context.hash(raw_secret)
        expires_at = utc_now() + timedelta(days=REFRESH_EXPIRE_DAYS)

        record = RefreshToken(
            token_id=token_id,
            family_id=family_id or str(uuid.uuid4()),
            user_id=user.id,
            hashed_token=hashed,
            expires_at=expires_at,
            revoked_at=None,
            created_ip=ip,
            user_agent=user_agent,
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
        if record is None:
            await self.audit.record(
                actor_user_id=None,
                action="REFRESH_REJECTED",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"reason": "missing"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if record.revoked_at is not None or record.replaced_by_token_id is not None:
            await self._revoke_family(record.family_id)
            await self.audit.record(
                actor_user_id=record.user_id,
                action="REFRESH_REPLAY_DETECTED",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"reason": "token_already_rotated"},
                ip=ip,
                user_agent=user_agent,
            )
            await self.audit.record(
                actor_user_id=record.user_id,
                action="REFRESH_REJECTED",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"reason": "replay_reuse", "family_id": record.family_id},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if not record.is_active():
            record.revoke()
            await self.session.commit()
            await self.audit.record(
                actor_user_id=record.user_id,
                action="REFRESH_REJECTED",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"reason": "expired_or_inactive"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        if not pwd_context.verify(secret, record.hashed_token):
            await self._revoke_record(record)
            await self.audit.record(
                actor_user_id=record.user_id,
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

        new_refresh_value = await self._create_refresh_token(
            user,
            family_id=record.family_id,
            ip=ip,
            user_agent=user_agent,
        )
        new_token_id, _ = self._split_refresh_token(new_refresh_value)
        await self._revoke_record(record, replaced_by=new_token_id)
        roles = await self.rbac.user_roles(user.id)
        permissions = await self.rbac.user_permissions(user.id)
        access_token = self._encode_access_token(user, roles, permissions)
        refreshed: TokenBundle = {
            "access_token": access_token,
            "refresh_token": new_refresh_value,
            "token_type": "Bearer",
        }
        await self.audit.record(
            actor_user_id=user.id,
            action="REFRESH_ROTATED",
            target_type="refresh_token",
            target_id=token_id,
            metadata={"status": user.status.value, "family_id": record.family_id},
            ip=ip,
            user_agent=user_agent,
        )
        return refreshed

    async def change_password(
        self,
        *,
        user: User,
        current_password: str,
        new_password: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        تغيير كلمة المرور مع إبطال جلسات التحديث النشطة وتدقيق الحدث.
        """

        if not user.check_password(current_password):
            await self.audit.record(
                actor_user_id=user.id,
                action="PASSWORD_CHANGE_REJECTED",
                target_type="user",
                target_id=str(user.id),
                metadata={"reason": "bad_current_password"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

        user.set_password(new_password)
        await self.session.commit()
        revoked = await self._revoke_user_tokens(user)
        await self.audit.record(
            actor_user_id=user.id,
            action="PASSWORD_CHANGED",
            target_type="user",
            target_id=str(user.id),
            metadata={"revoked_refresh_tokens": revoked},
            ip=ip,
            user_agent=user_agent,
        )

    async def request_password_reset(
        self,
        *,
        email: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str | None, int | None]:
        """
        إنشاء رمز إعادة تعيين قصير العمر مع تدقيق طلب مجهول.

        يعيد الرمز عند توفر المستخدم لتسهيل الاختبار/التكامل، بينما يحافظ على
        رسالة موحدة لتجنب كشف وجود البريد الإلكتروني.
        """

        normalized_email = email.lower().strip()
        result = await self.session.execute(select(User).where(User.email == normalized_email))
        user = result.scalar_one_or_none()
        if not user:
            await self.audit.record(
                actor_user_id=None,
                action="PASSWORD_RESET_REQUESTED",
                target_type="user",
                target_id=None,
                metadata={"email_hash": self._hash_identifier(normalized_email), "status": "unknown_user"},
                ip=ip,
                user_agent=user_agent,
            )
            return None, None

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
        await self.audit.record(
            actor_user_id=user.id,
            action="PASSWORD_RESET_REQUESTED",
            target_type="user",
            target_id=str(user.id),
            metadata={"token_id": record.token_id, "expires_at": expires_at.isoformat()},
            ip=ip,
            user_agent=user_agent,
        )
        return token_value, PASSWORD_RESET_EXPIRE_MINUTES * 60

    async def reset_password(
        self,
        *,
        token: str,
        new_password: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """
        تفعيل إعادة التعيين باستخدام رمز لمرة واحدة مع إبطال الجلسات السابقة.
        """

        hashed = sha256(token.encode()).hexdigest()
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.hashed_token == hashed)
        )
        record = result.scalar_one_or_none()
        if not record or not record.is_active():
            await self.audit.record(
                actor_user_id=None,
                action="PASSWORD_RESET_REJECTED",
                target_type="password_reset",
                target_id=None,
                metadata={"reason": "invalid_or_expired"},
                ip=ip,
                user_agent=user_agent,
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

        user = await self.session.get(User, record.user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User missing for reset")

        user.set_password(new_password)
        record.mark_redeemed()
        await self.session.commit()
        revoked = await self._revoke_user_tokens(user)
        await self.audit.record(
            actor_user_id=user.id,
            action="PASSWORD_RESET_COMPLETED",
            target_type="user",
            target_id=str(user.id),
            metadata={"token_id": record.token_id, "revoked_refresh_tokens": revoked},
            ip=ip,
            user_agent=user_agent,
        )

    async def logout(
        self, *, refresh_token: str, ip: str | None = None, user_agent: str | None = None
    ) -> None:
        token_id, _ = self._split_refresh_token(refresh_token)
        record = await self._get_refresh_record(token_id)
        if record:
            await self._revoke_family(record.family_id)
            await self.audit.record(
                actor_user_id=record.user_id,
                action="LOGOUT",
                target_type="refresh_token",
                target_id=token_id,
                metadata={"status": "family_revoked", "family_id": record.family_id},
                ip=ip,
                user_agent=user_agent,
            )

    async def _revoke_record(self, record: RefreshToken, *, replaced_by: str | None = None) -> None:
        record.revoke(revoked_at=utc_now(), replaced_by=replaced_by)
        await self.session.commit()

    async def _revoke_family(self, family_id: str) -> None:
        """
        إبطال جميع رموز التحديث ضمن نفس العائلة لحماية الجلسة من إعادة التشغيل.
        """

        now = utc_now()
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoke(revoked_at=now)
        await self.session.commit()

    async def _revoke_user_tokens(self, user: User) -> int:
        """إبطال كل رموز التحديث النشطة لمستخدم محدد."""

        now = utc_now()
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoke(revoked_at=now)
        await self.session.commit()
        return len(tokens)

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
