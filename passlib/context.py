"""
سياق مبسط للتوافق مع passlib أثناء الاختبارات.

هذا التنفيذ ليس بديلاً أمنياً، بل يهدف لتوفير واجهة مطابقة للاختبارات.
"""

from __future__ import annotations

import os
import secrets
from hashlib import pbkdf2_hmac, sha256


class CryptContext:
    """سياق تشفير مبسط يدعم واجهات hash/verify/needs_update."""

    def __init__(self, schemes: list[str], deprecated: str | None = None) -> None:
        self._schemes = schemes
        self._deprecated = deprecated

    def schemes(self) -> list[str]:
        """يعيد قائمة الخوارزميات المدعومة."""
        return list(self._schemes)

    def hash(self, password: str) -> str:
        """ينشئ تجزئة مع تضمين اسم الخوارزمية والملح."""
        scheme = self._schemes[0] if self._schemes else "sha256_crypt"
        salt = secrets.token_hex(8)
        digest = self._digest_for_scheme(scheme, password, salt)
        return f"${scheme}${salt}${digest}"

    def verify(self, password: str, hashed: str) -> bool:
        """يتحقق من مطابقة كلمة المرور للتجزئة."""
        try:
            scheme, salt, digest = self._split_hash(hashed)
        except ValueError:
            return False
        expected = self._digest_for_scheme(scheme, password, salt)
        return expected == digest

    def needs_update(self, hashed: str) -> bool:
        """يتحقق مما إذا كانت التجزئة تحتاج إلى تحديث بناءً على الأولوية."""
        try:
            scheme, _, _ = self._split_hash(hashed)
        except ValueError:
            return True
        if not self._schemes:
            return True
        return scheme != self._schemes[0]

    def _split_hash(self, hashed: str) -> tuple[str, str, str]:
        """يفكك التجزئة إلى مكوناتها الأساسية."""
        cleaned = hashed.lstrip("$")
        scheme, salt, digest = cleaned.split("$", maxsplit=2)
        return scheme, salt, digest

    def _digest_for_scheme(self, scheme: str, password: str, salt: str) -> str:
        """ينفذ تجزئة مبسطة بناءً على الخوارزمية المطلوبة."""
        if scheme in {"pbkdf2_sha256"}:
            digest = pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
            )
            return digest.hex()
        if scheme in {"bcrypt", "argon2", "sha256_crypt"}:
            payload = f"{salt}{password}".encode("utf-8")
            return sha256(payload).hexdigest()
        payload = f"{salt}{password}".encode("utf-8")
        return sha256(payload).hexdigest()


__all__ = ["CryptContext"]
