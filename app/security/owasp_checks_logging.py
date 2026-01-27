"""فحوصات التسجيل والمراقبة ضمن OWASP بطريقة نقية ومهيكلة."""

from __future__ import annotations

import re

from app.security.owasp_models import OWASPCategory, SecurityIssue, SecuritySeverity


def check_logging_issues(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من التسجيل والمراقبة ويعيد القضايا المرتبطة بها."""
    issues: list[SecurityIssue] = []
    issues.extend(_check_missing_auth_logging(code, file_path))
    issues.extend(_check_sensitive_logging(code, file_path))
    return issues


def _check_missing_auth_logging(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد غياب تسجيل أحداث المصادقة."""
    if (
        ("login" in code.lower() or "authenticate" in code.lower())
        and "log" not in code.lower()
        and "audit" not in code.lower()
    ):
        return [
            SecurityIssue(
                category=OWASPCategory.A09_LOGGING_FAILURES,
                severity=SecuritySeverity.MEDIUM,
                title="Missing Security Event Logging",
                description="Authentication events should be logged",
                file_path=file_path,
                recommendation="Log all authentication attempts with timestamp, IP, result",
                cwe_id="CWE-778",
            )
        ]
    return []


def _check_sensitive_logging(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد تسجيل البيانات الحساسة."""
    if re.search("log.*password|log.*token|log.*secret", code, re.IGNORECASE):
        return [
            SecurityIssue(
                category=OWASPCategory.A09_LOGGING_FAILURES,
                severity=SecuritySeverity.HIGH,
                title="Sensitive Data in Logs",
                description="Logging potentially sensitive information",
                file_path=file_path,
                recommendation="Never log passwords, tokens, or secrets",
                cwe_id="CWE-532",
            )
        ]
    return []
