"""
أداة فحص OWASP Top 10 - مطابقة لمعايير الشركات العملاقة
OWASP Top 10 Security Validation Tool

Validates code and configurations against:
✅ OWASP Top 10 (2021 edition)
✅ CWE Top 25
✅ SANS Top 25
✅ PCI DSS requirements
✅ NIST guidelines

Similar to tools used by:
- Google (Security Command Center)
- Microsoft (Security DevOps)
- AWS (Inspector)
- Stripe (Security Scanning)
"""

import re

from app.security import (
    owasp_checks_access,
    owasp_checks_auth,
    owasp_checks_crypto,
    owasp_checks_injection,
    owasp_checks_logging,
    owasp_checks_session,
)
from app.security.owasp_checks import (
    CHECK_PIPELINE,
    check_access_control_issues,
    check_authentication_issues,
    check_cryptography_issues,
    check_injection_issues,
    check_logging_issues,
    check_session_issues,
)
from app.security.owasp_models import (
    ComplianceStatus,
    CriticalIssueSummary,
    OWASPCategory,
    SecurityIssue,
    SecurityReport,
    SecuritySeverity,
)
from app.security.owasp_utils import (
    HARDCODED_SECRETS_PATTERNS,
    INSECURE_CRYPTO_PATTERNS,
    is_false_positive_crypto,
    is_false_positive_secret,
)


class OWASPValidator:
    """
    مدقق أمان OWASP بمعايير مؤسسية شاملة.

    يغطي الفحص:
    - التحكم بالوصول
    - المصادقة
    - الحقن والثغرات الشائعة
    - التشفير وإدارة الأسرار
    - الضبط والإعدادات
    - التبعيات
    - التسجيل والمراقبة
    """

    def __init__(self):
        self.issues: list[SecurityIssue] = []
        self.insecure_crypto_patterns = INSECURE_CRYPTO_PATTERNS
        self.hardcoded_secrets_patterns = HARDCODED_SECRETS_PATTERNS

    def validate_authentication_code(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من سلامة المصادقة (A07:2021).
        """
        return check_authentication_issues(code, file_path)

    def _check_weak_password_hashing(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يتحقق من استخدام خوارزميات تجزئة ضعيفة لكلمات المرور."""
        return owasp_checks_auth._check_weak_password_hashing(code, file_path)

    def _check_plaintext_password_storage(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يتحقق من احتمال تخزين كلمات المرور بنص صريح."""
        return owasp_checks_auth._check_plaintext_password_storage(code, file_path)

    def _check_authentication_rate_limiting(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يتحقق من غياب تحديد المعدل في مسارات تسجيل الدخول."""
        return owasp_checks_auth._check_authentication_rate_limiting(code, file_path)

    def validate_access_control(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من ضوابط التحكم بالوصول (A01:2021).
        """
        return check_access_control_issues(code, file_path)

    def _check_role_escalation(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد احتمالات رفع الصلاحيات من مدخلات المستخدم."""
        return owasp_checks_access._check_role_escalation(code, file_path)

    def _check_admin_escalation(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد احتمالات رفع صلاحيات المدير من مدخلات المستخدم."""
        return owasp_checks_access._check_admin_escalation(code, file_path)

    def _check_missing_auth_checks(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يتحقق من غياب التفويض في المسارات الحساسة."""
        return owasp_checks_access._check_missing_auth_checks(code, file_path)

    def validate_injection_prevention(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من ثغرات الحقن (A03:2021).
        """
        return check_injection_issues(code, file_path)

    def _check_sql_injection(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد مؤشرات حقن SQL في الشيفرة."""
        return owasp_checks_injection._check_sql_injection(code, file_path)

    def _check_command_injection(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد مؤشرات حقن الأوامر عبر النظام."""
        return owasp_checks_injection._check_command_injection(code, file_path)

    def _check_xss_vulnerabilities(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد مؤشرات XSS في التعامل مع HTML."""
        return owasp_checks_injection._check_xss_vulnerabilities(code, file_path)

    def validate_cryptography(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من سلامة التشفير وإدارة الأسرار (A02:2021).
        """
        return check_cryptography_issues(code, file_path)

    def _check_weak_crypto_algorithms(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد الخوارزميات التشفيرية الضعيفة."""
        return owasp_checks_crypto._check_weak_crypto_algorithms(code, file_path)

    def _check_hardcoded_secrets(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد الأسرار الصلبة داخل الشيفرة."""
        return owasp_checks_crypto._check_hardcoded_secrets(code, file_path)

    def _is_false_positive_crypto(self, code: str, match: re.Match[str]) -> bool:
        """يتحقق مما إذا كانت مطابقة التشفير إنذارًا كاذبًا."""
        return is_false_positive_crypto(code, match)

    def _is_false_positive_secret(self, code: str, match: re.Match[str], file_path: str) -> bool:
        """يتحقق من استثناءات الأسرار لتقليل الإنذارات الكاذبة."""
        return is_false_positive_secret(code, match, file_path)

    def validate_session_management(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من إدارة الجلسات (A07:2021).
        """
        return check_session_issues(code, file_path)

    def _check_secure_cookie_flag(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد إعدادات Cookie الآمنة."""
        return owasp_checks_session._check_secure_cookie_flag(code, file_path)

    def _check_httponly_cookie_flag(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد إعدادات Cookie المقيّدة من JavaScript."""
        return owasp_checks_session._check_httponly_cookie_flag(code, file_path)

    def validate_logging_monitoring(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من التسجيل والمراقبة (A09:2021).
        """
        return check_logging_issues(code, file_path)

    def _check_missing_auth_logging(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد غياب تسجيل أحداث المصادقة."""
        return owasp_checks_logging._check_missing_auth_logging(code, file_path)

    def _check_sensitive_logging(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد تسجيل البيانات الحساسة."""
        return owasp_checks_logging._check_sensitive_logging(code, file_path)

    def validate_file(self, file_path: str) -> list[SecurityIssue]:
        """
        يفحص ملفًا واحدًا وفق OWASP Top 10.
        """
        try:
            code = self._read_code(file_path)
            return self._collect_issues(code, file_path)
        except Exception as e:
            return [
                SecurityIssue(
                    category=OWASPCategory.A05_SECURITY_MISCONFIGURATION,
                    severity=SecuritySeverity.INFO,
                    title="File Validation Error",
                    description=f"Could not validate file: {e!s}",
                    file_path=file_path,
                )
            ]

    def generate_report(self, issues: list[SecurityIssue]) -> SecurityReport:
        """يولد تقريرًا أمنيًا متكاملًا باستخدام تراكيب بيانات محددة الأنواع."""
        severity_counts = self._count_severities(issues)
        category_counts = self._count_categories(issues)
        risk_score = self._calculate_risk_score(severity_counts)
        return {
            "total_issues": len(issues),
            "risk_score": risk_score,
            "severity_breakdown": {
                severity.value: count for severity, count in severity_counts.items()
            },
            "category_breakdown": {
                category.value: count for category, count in category_counts.items()
            },
            "critical_issues": self._build_critical_summaries(issues),
            "compliance_status": self._build_compliance_status(risk_score),
        }

    def _read_code(self, file_path: str) -> str:
        """يقرأ محتوى الملف النصي بطريقة واضحة ومباشرة."""
        with open(file_path, encoding="utf-8") as handle:
            return handle.read()

    def _collect_issues(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يجمع نتائج جميع وحدات الفحص في قائمة واحدة."""
        issues: list[SecurityIssue] = []
        for validator in CHECK_PIPELINE:
            issues.extend(validator(code, file_path))
        return issues

    def _count_severities(self, issues: list[SecurityIssue]) -> dict[SecuritySeverity, int]:
        """يحصر عدد القضايا حسب درجة الخطورة."""
        severity_counts: dict[SecuritySeverity, int] = dict.fromkeys(SecuritySeverity, 0)
        for issue in issues:
            severity_counts[issue.severity] += 1
        return severity_counts

    def _count_categories(self, issues: list[SecurityIssue]) -> dict[OWASPCategory, int]:
        """يحصر عدد القضايا حسب تصنيف OWASP."""
        category_counts: dict[OWASPCategory, int] = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        return category_counts

    def _calculate_risk_score(self, severity_counts: dict[SecuritySeverity, int]) -> int:
        """يحسب درجة المخاطر بناءً على عدد القضايا الحرجة والعالية والمتوسطة."""
        score = (
            severity_counts[SecuritySeverity.CRITICAL] * 20
            + severity_counts[SecuritySeverity.HIGH] * 10
            + severity_counts[SecuritySeverity.MEDIUM] * 5
            + severity_counts[SecuritySeverity.LOW] * 2
        )
        return min(100, score)

    def _build_critical_summaries(self, issues: list[SecurityIssue]) -> list[CriticalIssueSummary]:
        """يبني قائمة مبسطة للقضايا الحرجة فقط."""
        critical: list[CriticalIssueSummary] = []
        for issue in issues:
            if issue.severity != SecuritySeverity.CRITICAL:
                continue
            critical.append(
                {
                    "title": issue.title,
                    "category": issue.category.value,
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "recommendation": issue.recommendation,
                }
            )
        return critical

    def _build_compliance_status(self, risk_score: int) -> ComplianceStatus:
        """يبني حالة الامتثال للمعايير وفق درجة المخاطر."""
        return {
            "OWASP_Top_10": risk_score < 20,
            "PCI_DSS": risk_score < 10,
            "SOC2": risk_score < 15,
        }
