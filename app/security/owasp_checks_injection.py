"""فحوصات الحقن ضمن OWASP بطريقة نقية ومهيكلة."""

from __future__ import annotations

import re

from app.security.owasp_models import OWASPCategory, SecurityIssue, SecuritySeverity
from app.security.owasp_utils import SQL_INJECTION_PATTERNS, XSS_PATTERNS


def check_injection_issues(code: str, file_path: str) -> list[SecurityIssue]:
    """يتحقق من ثغرات الحقن ويعيد القضايا المرتبطة بها."""
    issues: list[SecurityIssue] = []
    issues.extend(_check_sql_injection(code, file_path))
    issues.extend(_check_command_injection(code, file_path))
    issues.extend(_check_xss_vulnerabilities(code, file_path))
    return issues


def _check_sql_injection(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد مؤشرات حقن SQL في الشيفرة."""
    issues: list[SecurityIssue] = []
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, code):
            issues.append(
                SecurityIssue(
                    category=OWASPCategory.A03_INJECTION,
                    severity=SecuritySeverity.CRITICAL,
                    title="Potential SQL Injection",
                    description="SQL query uses string formatting or concatenation",
                    file_path=file_path,
                    recommendation="Use parameterized queries or ORM methods",
                    cwe_id="CWE-89",
                )
            )
    return issues


def _check_command_injection(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد مؤشرات حقن الأوامر عبر النظام."""
    if re.search("os\\.system\\(|subprocess\\.call\\(.*shell=True", code):
        return [
            SecurityIssue(
                category=OWASPCategory.A03_INJECTION,
                severity=SecuritySeverity.CRITICAL,
                title="Potential Command Injection",
                description="Command execution with shell=True or os.system",
                file_path=file_path,
                recommendation="Use subprocess with shell=False and validate all inputs",
                cwe_id="CWE-78",
            )
        ]
    return []


def _check_xss_vulnerabilities(code: str, file_path: str) -> list[SecurityIssue]:
    """يرصد مؤشرات XSS في التعامل مع HTML."""
    issues: list[SecurityIssue] = []
    for pattern in XSS_PATTERNS:
        if re.search(pattern, code):
            issues.append(
                SecurityIssue(
                    category=OWASPCategory.A03_INJECTION,
                    severity=SecuritySeverity.HIGH,
                    title="Potential Cross-Site Scripting (XSS)",
                    description="Direct HTML manipulation detected",
                    file_path=file_path,
                    recommendation="Use proper escaping and sanitization",
                    cwe_id="CWE-79",
                )
            )
    return issues
