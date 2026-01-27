"""فحوصات المصادقة ضمن OWASP بطريقة نقية ومهيكلة."""

from __future__ import annotations

import re

from app.security.owasp_models import OWASPCategory, SecurityIssue, SecuritySeverity
from app.security.owasp_utils import ID_GENERATION_PATTERN


def check_authentication_issues(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من سلامة المصادقة ويعيد القضايا المرتبطة بها."""
    issues: list[SecurityIssue] = []
    issues.extend(_check_weak_password_hashing(code, file_path))
    issues.extend(_check_plaintext_password_storage(code, file_path))
    issues.extend(_check_authentication_rate_limiting(code, file_path))
    return issues


def _check_weak_password_hashing(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من استخدام خوارزميات تجزئة ضعيفة لكلمات المرور."""
    password_keywords = ["password", "passwd", "pwd", "credential", "auth"]
    has_password_context = any(kw in code.lower() for kw in password_keywords)

    if not has_password_context:
        return []

    if "md5" not in code.lower() and "sha1" not in code.lower():
        return []

    if "usedforsecurity=False" in code or "usedforsecurity = False" in code:
        return []

    if re.search(ID_GENERATION_PATTERN, code):
        return []

    return [
        SecurityIssue(
            category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
            severity=SecuritySeverity.CRITICAL,
            title="Weak Password Hashing Algorithm",
            description="Using MD5 or SHA1 for password hashing is insecure",
            file_path=file_path,
            recommendation="Use bcrypt, scrypt, or Argon2 for password hashing",
            cwe_id="CWE-327",
        )
    ]


def _check_plaintext_password_storage(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من احتمال تخزين كلمات المرور بنص صريح."""
    if re.search("password\\s*=\\s*request", code, re.IGNORECASE) and "hash" not in code.lower():
        return [
            SecurityIssue(
                category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
                severity=SecuritySeverity.CRITICAL,
                title="Potential Plain Text Password Storage",
                description="Password appears to be stored without hashing",
                file_path=file_path,
                recommendation="Always hash passwords before storing",
                cwe_id="CWE-256",
            )
        ]
    return []


def _check_authentication_rate_limiting(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من غياب تحديد المعدل في مسارات تسجيل الدخول."""
    if "login" in code.lower() and "rate_limit" not in code.lower():
        return [
            SecurityIssue(
                category=OWASPCategory.A07_AUTH_FAILURES,
                severity=SecuritySeverity.HIGH,
                title="Missing Rate Limiting on Authentication",
                description="Login endpoint should implement rate limiting",
                file_path=file_path,
                recommendation="Add rate limiting to prevent brute force attacks",
                cwe_id="CWE-307",
            )
        ]
    return []
