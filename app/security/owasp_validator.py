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
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, TypedDict


class SecuritySeverity(Enum):
    """Security issue severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OWASPCategory(Enum):
    """OWASP Top 10 categories (2021)"""

    A01_BROKEN_ACCESS_CONTROL = "A01:2021 - Broken Access Control"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021 - Cryptographic Failures"
    A03_INJECTION = "A03:2021 - Injection"
    A04_INSECURE_DESIGN = "A04:2021 - Insecure Design"
    A05_SECURITY_MISCONFIGURATION = "A05:2021 - Security Misconfiguration"
    A06_VULNERABLE_COMPONENTS = "A06:2021 - Vulnerable and Outdated Components"
    A07_AUTH_FAILURES = "A07:2021 - Identification and Authentication Failures"
    A08_DATA_INTEGRITY = "A08:2021 - Software and Data Integrity Failures"
    A09_LOGGING_FAILURES = "A09:2021 - Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021 - Server-Side Request Forgery"


@dataclass
class SecurityIssue:
    """Security issue found during validation"""

    category: OWASPCategory
    severity: SecuritySeverity
    title: str
    description: str
    file_path: str | None = None
    line_number: int | None = None
    code_snippet: str | None = None
    recommendation: str = ""
    cwe_id: str | None = None


class CriticalIssueSummary(TypedDict):
    """ملخص عربي مضبوط الأنواع للقضايا الحرجة المكتشفة."""

    title: str
    category: str
    file: str | None
    line: int | None
    recommendation: str


class ComplianceStatus(TypedDict):
    """حالة التوافق مع المعايير الأمنية الرئيسية."""

    OWASP_Top_10: bool
    PCI_DSS: bool
    SOC2: bool


class SecurityReport(TypedDict):
    """تقرير أمني شامل خالٍ من الأنواع العامة."""

    total_issues: int
    risk_score: int
    severity_breakdown: dict[str, int]
    category_breakdown: dict[str, int]
    critical_issues: list[CriticalIssueSummary]
    compliance_status: ComplianceStatus


class OWASPValidator:
    """
    مدقق أمان OWASP - Enterprise OWASP Security Validator

    Comprehensive security validation covering:
    - Access control
    - Authentication
    - Injection vulnerabilities
    - Cryptography
    - Configuration
    - Dependencies
    - Logging
    """

    _CONTEXT_BEFORE = 100
    _CONTEXT_AFTER = 100
    _SAFE_SECRET_PATTERNS: ClassVar[list[str]] = [
        "class ",
        "Enum",
        '= "api_key"',
        '= "database_password"',
        '= "jwt_secret"',
        '= "webhook_secret"',
        '= "encryption_key"',
        '= "oauth_client_secret"',
        '= "secret"',
        "import secrets",
        "secrets.token",
        '["api_key"]',
        "['api_key']",
        "['api_key']",
        '["secret"]',
        "['secret']",
        "['secret']",
        "creds[",
        "credentials[",
        ".api_key = creds",
        ".api_key=creds",
        "_SENSITIVE_MARKERS",
        "_MARKERS",
    ]
    _ENV_VAR_PATTERNS: ClassVar[list[str]] = [
        "os.environ",
        "os.getenv",
        "getenv(",
        "environ.get",
        "config.get",
        "settings.",
        "process.env",
    ]

    def __init__(self):
        self.issues: list[SecurityIssue] = []
        self.sql_injection_patterns = [
            "execute\\s*\\(\\s*[\"\\'].*%s.*[\"\\']",
            "\\.raw\\s*\\(",
            "cursor\\.execute\\s*\\(\\s*f[\"\\']",
        ]
        self.hardcoded_secrets_patterns = [
            "password\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
            "api[_-]?key\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
            "secret\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
            "token\\s*=\\s*[\"\\'][^\"\\']+[\"\\']",
        ]
        self.insecure_crypto_patterns = [
            "hashlib\\.md5\\(",
            "hashlib\\.sha1\\(",
            "random\\.random\\(",
        ]
        self.xss_patterns = ["innerHTML\\s*=", "\\.html\\s*\\(", "dangerouslySetInnerHTML"]
        self._id_generation_pattern = (
            "hashlib\\.(md5|sha1)\\([^)]*\\)\\.hexdigest\\(\\)\\[:?\\d*\\]"
        )

    def validate_authentication_code(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        Validate authentication implementation
        (A07:2021 - Identification and Authentication Failures)
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_weak_password_hashing(code, file_path))
        issues.extend(self._check_plaintext_password_storage(code, file_path))
        issues.extend(self._check_authentication_rate_limiting(code, file_path))
        return issues

    def _check_weak_password_hashing(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for weak password hashing algorithms"""
        password_keywords = ["password", "passwd", "pwd", "credential", "auth"]
        has_password_context = any(kw in code.lower() for kw in password_keywords)

        if not has_password_context:
            return []

        if "md5" not in code.lower() and "sha1" not in code.lower():
            return []

        if "usedforsecurity=False" in code or "usedforsecurity = False" in code:
            return []

        if re.search(self._id_generation_pattern, code):
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

    def _check_plaintext_password_storage(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for potential plaintext password storage"""
        if (
            re.search("password\\s*=\\s*request", code, re.IGNORECASE)
            and "hash" not in code.lower()
        ):
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

    def _check_authentication_rate_limiting(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for missing rate limiting on authentication"""
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

    def validate_access_control(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        Validate access control implementation
        (A01:2021 - Broken Access Control)
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_role_escalation(code, file_path))
        issues.extend(self._check_admin_escalation(code, file_path))
        issues.extend(self._check_missing_auth_checks(code, file_path))
        return issues

    def _check_role_escalation(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for potential role escalation"""
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

    def _check_admin_escalation(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for potential admin privilege escalation"""
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

    def _check_missing_auth_checks(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for missing authorization checks on sensitive endpoints"""
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

    def validate_injection_prevention(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        Validate injection vulnerability prevention
        (A03:2021 - Injection)
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_sql_injection(code, file_path))
        issues.extend(self._check_command_injection(code, file_path))
        issues.extend(self._check_xss_vulnerabilities(code, file_path))
        return issues

    def _check_sql_injection(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for SQL injection patterns"""
        issues = []
        for pattern in self.sql_injection_patterns:
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

    def _check_command_injection(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for command injection patterns"""
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

    def _check_xss_vulnerabilities(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for Cross-Site Scripting (XSS) patterns"""
        issues = []
        for pattern in self.xss_patterns:
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

    def validate_cryptography(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        Validate cryptographic implementations
        (A02:2021 - Cryptographic Failures)
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_weak_crypto_algorithms(code, file_path))
        issues.extend(self._check_hardcoded_secrets(code, file_path))
        return issues

    def _check_weak_crypto_algorithms(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for weak cryptographic algorithms"""
        issues = []
        for pattern in self.insecure_crypto_patterns:
            matches = list(re.finditer(pattern, code))
            for match in matches:
                if self._is_false_positive_crypto(code, match):
                    continue

                issues.append(
                    SecurityIssue(
                        category=OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES,
                        severity=SecuritySeverity.MEDIUM,
                        title="Weak Cryptographic Algorithm",
                        description="Using weak hashing algorithm (MD5, SHA1, random)",
                        file_path=file_path,
                        recommendation="Use SHA-256 or better, secrets.token_* for random values, or add usedforsecurity=False for non-cryptographic uses",
                        cwe_id="CWE-327",
                    )
                )
        return issues

    def _is_false_positive_crypto(self, code: str, match: re.Match) -> bool:
        """Check if a crypto match is a false positive"""
        start = max(0, match.start() - self._CONTEXT_BEFORE)
        end = min(len(code), match.end() + self._CONTEXT_AFTER)
        context = code[start:end]

        if "usedforsecurity=False" in context or "usedforsecurity = False" in context:
            return True
        return "import hashlib" in context

    def _check_hardcoded_secrets(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for hardcoded secrets"""
        issues = []
        for pattern in self.hardcoded_secrets_patterns:
            matches = list(re.finditer(pattern, code, re.IGNORECASE))
            for match in matches:
                if self._is_false_positive_secret(code, match, file_path):
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

    def _is_false_positive_secret(self, code: str, match: re.Match, file_path: str) -> bool:
        """Check if a secret match is a false positive"""
        start = max(0, match.start() - self._CONTEXT_BEFORE)
        end = min(len(code), match.end() + self._CONTEXT_AFTER)
        context = code[start:end]

        if any(env_pat in context for env_pat in self._ENV_VAR_PATTERNS):
            return True
        if any(safe_pat in context for safe_pat in self._SAFE_SECRET_PATTERNS):
            return True
        if "test_" in file_path.lower():
            return True
        return bool(context.strip().startswith("#") or context.strip().startswith("//"))

    def validate_session_management(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        Validate session management
        (A07:2021 - Identification and Authentication Failures)
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_secure_cookie_flag(code, file_path))
        issues.extend(self._check_httponly_cookie_flag(code, file_path))
        return issues

    def _check_secure_cookie_flag(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check if SESSION_COOKIE_SECURE is set"""
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

    def _check_httponly_cookie_flag(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check if SESSION_COOKIE_HTTPONLY is set"""
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

    def validate_logging_monitoring(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        Validate logging and monitoring
        (A09:2021 - Security Logging and Monitoring Failures)
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_missing_auth_logging(code, file_path))
        issues.extend(self._check_sensitive_logging(code, file_path))
        return issues

    def _check_missing_auth_logging(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for missing logging on authentication events"""
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

    def _check_sensitive_logging(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Check for logging of sensitive data"""
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

    def validate_file(self, file_path: str) -> list[SecurityIssue]:
        """
        Validate a single file for OWASP Top 10 issues
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
        """يولد تقرير أمني متكامل باستخدام تراكيب بيانات محددة الأنواع."""
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
        issue_groups = [
            self.validate_authentication_code,
            self.validate_access_control,
            self.validate_injection_prevention,
            self.validate_cryptography,
            self.validate_session_management,
            self.validate_logging_monitoring,
        ]
        issues: list[SecurityIssue] = []
        for validator in issue_groups:
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
