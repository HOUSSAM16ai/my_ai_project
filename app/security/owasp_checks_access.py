"""فحوصات التحكم بالوصول ضمن OWASP بطريقة نقية ومهيكلة."""

from __future__ import annotations

import re

from app.security.owasp_models import OWASPCategory, SecurityIssue, SecuritySeverity


def check_access_control_issues(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من ضوابط التحكم بالوصول ويعيد القضايا المرتبطة بها."""
    issues: list[SecurityIssue] = []
    issues.extend(_check_role_escalation(code, file_path))
    issues.extend(_check_admin_escalation(code, file_path))
    issues.extend(_check_missing_auth_checks(code, file_path))
    return issues


def _check_role_escalation(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد احتمالات رفع الصلاحيات من مدخلات المستخدم."""
    if re.search("role\\s*=\\s*request\\.(json|form|args)", code):
        return [
            SecurityIssue(
                category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
                severity=SecuritySeverity.CRITICAL,
                title="Privilege Escalation Vulnerability",
                description="User role is being set directly from user input",
                file_path=file_path,
                recommendation="Never allow users to set their own roles. Use server-side logic.",
                cwe_id="CWE-269",
            )
        ]
    return []


def _check_admin_escalation(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد احتمالات رفع صلاحيات المدير من مدخلات المستخدم."""
    if re.search("is_admin\\s*=\\s*request\\.(json|form|args)", code):
        return [
            SecurityIssue(
                category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
                severity=SecuritySeverity.CRITICAL,
                title="Admin Privilege Escalation",
                description="Admin flag is being set from user input",
                file_path=file_path,
                recommendation="Admin status must be controlled server-side only",
                cwe_id="CWE-269",
            )
        ]
    return []


def _check_missing_auth_checks(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من غياب التفويض في المسارات الحساسة."""
    if (
        re.search("@app\\.route.*<int:user_id>", code)
        and "@login_required" not in code
        and "@require_auth" not in code
    ):
        return [
            SecurityIssue(
                category=OWASPCategory.A01_BROKEN_ACCESS_CONTROL,
                severity=SecuritySeverity.HIGH,
                title="Missing Authorization Check",
                description="Endpoint with user_id parameter lacks authorization",
                file_path=file_path,
                recommendation="Add @login_required and verify user owns the resource",
                cwe_id="CWE-862",
            )
        ]
    return []
