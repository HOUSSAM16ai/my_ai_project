"""
وحدة التشفير والتعامل مع الرموز (Crypto/Token Logic).
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Final

import jwt
from fastapi import HTTPException, status

from app.core.config import AppSettings
from app.core.domain.user import User

ACCESS_EXPIRE_MINUTES: Final[int] = 30
REAUTH_EXPIRE_MINUTES: Final[int] = 10


class AuthCrypto:
    """
    مسؤول عن العمليات الحسابية والتشفيرية البحتة:
    - توليد الرموز (JWT)
    - تجزئة المعرفات (Hashing)
    - تقسيم رموز التحديث
    """

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def hash_identifier(self, value: str) -> str:
        """توليد بصمة نصية لحماية الهوية في سجلات التدقيق."""
        digest = sha256(value.encode()).hexdigest()
        return digest[:16]

    def encode_access_token(self, user: User, roles: list[str], permissions: set[str]) -> str:
        """تشفير رمز الوصول (Access Token) باستخدام إعدادات التطبيق."""
        expires_delta = timedelta(
            minutes=min(self.settings.ACCESS_TOKEN_EXPIRE_MINUTES, ACCESS_EXPIRE_MINUTES)
        )
        payload = {
            "sub": str(user.id),
            "roles": roles,
            "permissions": sorted(permissions),
            "jti": secrets.token_urlsafe(8),
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + expires_delta,
        }
        return jwt.encode(payload, self.settings.SECRET_KEY, algorithm="HS256")

    def encode_reauth_token(self, user: User) -> tuple[str, int]:
        """تشفير رمز إعادة المصادقة (Re-auth Token)."""
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

    def split_refresh_token(self, token: str) -> tuple[str, str]:
        """فصل معرف الرمز عن السر الخاص به."""
        try:
            token_id_part, secret_part = token.split(":", maxsplit=1)
            return token_id_part, secret_part
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token format"
            ) from exc

    def verify_jwt(self, token: str) -> dict[str, object]:
        """التحقق من صحة توقيع JWT."""
        try:
            # Note: The original code casts the result of jwt.decode (which is Any) to dict.
            return jwt.decode(token, self.settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            ) from exc
