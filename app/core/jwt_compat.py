"""
طبقة توافق JWT (JWT Compatibility Layer).

توفر هذه الوحدة وظائف ترميز وفك ترميز رموز JWT بخوارزمية HS256
بصورة مستقلة عن مكتبات الطرف الثالث، مع واجهة مشابهة لـ PyJWT.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import datetime


class PyJWTError(Exception):
    """الاستثناء الأساسي المتوافق مع PyJWT."""


class InvalidTokenError(PyJWTError):
    """يُطلق عند وجود خطأ في التوقيع أو بنية الرمز."""


class ExpiredSignatureError(PyJWTError):
    """يُطلق عند انتهاء صلاحية الرمز."""


def _b64url_encode(data: bytes) -> str:
    """يحّول البيانات إلى Base64 URL-safe بدون padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    """يفك ترميز Base64 URL-safe مع معالجة padding."""
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")


def _normalize_payload(payload: dict[str, object]) -> dict[str, object]:
    """يحوّل القيم الزمنية في الحمولة إلى timestamps عددية."""
    normalized: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, datetime):
            normalized[key] = int(value.timestamp())
        else:
            normalized[key] = value
    return normalized


def encode(payload: dict[str, object], key: str, algorithm: str = "HS256") -> str:
    """يرمز حمولة JWT باستخدام HS256."""
    if algorithm != "HS256":
        raise InvalidTokenError("Unsupported algorithm.")
    header = {"alg": algorithm, "typ": "JWT"}
    normalized = _normalize_payload(payload)
    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(normalized, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    signature = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_segment = _b64url_encode(signature)
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def decode(token: str, key: str, algorithms: list[str] | None = None) -> dict[str, object]:
    """يفك ترميز JWT مع التحقق من التوقيع والصلاحية."""
    if algorithms and "HS256" not in algorithms:
        raise InvalidTokenError("Unsupported algorithm.")
    parts = token.split(".")
    if len(parts) != 3:
        raise InvalidTokenError("Invalid token format.")
    header_segment, payload_segment, signature_segment = parts
    signing_input = f"{header_segment}.{payload_segment}".encode("utf-8")
    expected_sig = hmac.new(key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    provided_sig = _b64url_decode(signature_segment)
    if not hmac.compare_digest(expected_sig, provided_sig):
        raise InvalidTokenError("Signature verification failed.")
    payload_bytes = _b64url_decode(payload_segment)
    payload = json.loads(payload_bytes.decode("utf-8"))
    exp = payload.get("exp")
    if exp is not None:
        now = int(time.time())
        try:
            exp_value = int(exp)
        except (TypeError, ValueError) as exc:
            raise InvalidTokenError("Invalid exp claim.") from exc
        if now > exp_value:
            raise ExpiredSignatureError("Token has expired.")
    return payload


class _JwtModule:
    """واجهة تتوافق مع استخدام jwt.encode/jwt.decode في النظام."""

    PyJWTError = PyJWTError
    InvalidTokenError = InvalidTokenError
    ExpiredSignatureError = ExpiredSignatureError

    def encode(self, payload: dict[str, object], key: str, algorithm: str = "HS256") -> str:
        """يرمز حمولة JWT باستخدام HS256."""
        return encode(payload, key, algorithm=algorithm)

    def decode(self, token: str, key: str, algorithms: list[str] | None = None) -> dict[str, object]:
        """يفك ترميز JWT مع التحقق من التوقيع والصلاحية."""
        return decode(token, key, algorithms=algorithms)


jwt = _JwtModule()

__all__ = [
    "ExpiredSignatureError",
    "InvalidTokenError",
    "PyJWTError",
    "decode",
    "encode",
    "jwt",
]
