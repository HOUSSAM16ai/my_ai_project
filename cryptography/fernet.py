"""
تنفيذ مبسط لـ Fernet لتوافق اختبارات التشفير المحلية.

هذا التنفيذ غير آمن للاستخدام الإنتاجي، ويستخدم XOR لغرض الاختبارات فقط.
"""

from __future__ import annotations

import base64
import os


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """ينفذ XOR بسيط بين البيانات والمفتاح."""
    repeated_key = (key * ((len(data) // len(key)) + 1))[: len(data)]
    return bytes(a ^ b for a, b in zip(data, repeated_key))


class Fernet:
    """تنفيذ مبسط يدعم generate_key/encrypt/decrypt."""

    def __init__(self, key: bytes) -> None:
        self._key = key if len(key) == 32 else base64.urlsafe_b64decode(key)

    @staticmethod
    def generate_key() -> bytes:
        """ينشئ مفتاحاً مشفراً بتنسيق urlsafe base64."""
        return base64.urlsafe_b64encode(os.urandom(32))

    def encrypt(self, data: bytes) -> bytes:
        """يشفر البيانات باستخدام XOR ويعيدها كـ base64."""
        encrypted = _xor_bytes(data, self._key)
        return base64.urlsafe_b64encode(encrypted)

    def decrypt(self, token: bytes) -> bytes:
        """يفك التشفير الناتج عن encrypt."""
        raw = base64.urlsafe_b64decode(token)
        return _xor_bytes(raw, self._key)


__all__ = ["Fernet"]
