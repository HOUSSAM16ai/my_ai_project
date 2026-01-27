"""فحوصات إدارة الجلسات ضمن OWASP بطريقة نقية ومهيكلة."""

from __future__ import annotations

from app.security.owasp_models import OWASPCategory, SecurityIssue, SecuritySeverity


def check_session_issues(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من إدارة الجلسات ويعيد القضايا المرتبطة بها."""
    issues: list[SecurityIssue] = []
    issues.extend(_check_secure_cookie_flag(code, file_path))
    issues.extend(_check_httponly_cookie_flag(code, file_path))
    return issues


def _check_secure_cookie_flag(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد إعدادات Cookie الآمنة."""
    if "SESSION_COOKIE_SECURE = False" in code:
        return [
            SecurityIssue(
                category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
                severity=SecuritySeverity.HIGH,
                title="Insecure Session Cookie",
                description="Session cookies not marked as secure",
                file_path=file_path,
                recommendation="Set SESSION_COOKIE_SECURE = True for HTTPS",
                cwe_id="CWE-614",
            )
        ]
    return []


def _check_httponly_cookie_flag(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد إعدادات Cookie المقيّدة من JavaScript."""
    if "SESSION_COOKIE_HTTPONLY = False" in code:
        return [
            SecurityIssue(
                category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
                severity=SecuritySeverity.HIGH,
                title="Session Cookie Accessible to JavaScript",
                description="Session cookies not marked as HttpOnly",
                file_path=file_path,
                recommendation="Set SESSION_COOKIE_HTTPONLY = True",
                cwe_id="CWE-1004",
            )
        ]
    return []
