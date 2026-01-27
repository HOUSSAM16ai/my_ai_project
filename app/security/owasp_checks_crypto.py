"""فحوصات التشفير وإدارة الأسرار ضمن OWASP بطريقة نقية ومهيكلة."""

from __future__ import annotations

import re

from app.security.owasp_models import OWASPCategory, SecurityIssue, SecuritySeverity
from app.security.owasp_utils import (
    HARDCODED_SECRETS_PATTERNS,
    INSECURE_CRYPTO_PATTERNS,
    is_false_positive_crypto,
    is_false_positive_secret,
)


def check_cryptography_issues(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من سلامة التشفير وإدارة الأسرار ويعيد القضايا المرتبطة بها."""
    issues: list[SecurityIssue] = []
    issues.extend(_check_weak_crypto_algorithms(code, file_path))
    issues.extend(_check_hardcoded_secrets(code, file_path))
    return issues


def _check_weak_crypto_algorithms(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد الخوارزميات التشفيرية الضعيفة."""
    issues: list[SecurityIssue] = []
    for pattern in INSECURE_CRYPTO_PATTERNS:
        matches = list(re.finditer(pattern, code))
        for match in matches:
            if is_false_positive_crypto(code, match):
                continue

            issues.append(
                SecurityIssue(
                    category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
                    severity=SecuritySeverity.MEDIUM,
                    title="Weak Cryptographic Algorithm",
                    description="Using weak hashing algorithm (MD5, SHA1, random)",
                    file_path=file_path,
                    recommendation=(
                        "Use SHA-256 or better, secrets.token_* for random values, "
                        "or add usedforsecurity=False for non-cryptographic uses"
                    ),
                    cwe_id="CWE-327",
                )
            )
    return issues


def _check_hardcoded_secrets(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد الأسرار الصلبة داخل الشيفرة."""
    issues: list[SecurityIssue] = []
    for pattern in HARDCODED_SECRETS_PATTERNS:
        matches = list(re.finditer(pattern, code, re.IGNORECASE))
        for match in matches:
            if is_false_positive_secret(code, match, file_path):
                continue

            issues.append(
                SecurityIssue(
                    category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
                    severity=SecuritySeverity.CRITICAL,
                    title="Hardcoded Secret",
                    description="Secret or credential appears to be hardcoded",
                    file_path=file_path,
                    recommendation="Use environment variables or secret management",
                    cwe_id="CWE-798",
                )
            )
    return issues
