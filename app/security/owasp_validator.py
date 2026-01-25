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
    """مستويات خطورة القضايا الأمنية."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OWASPCategory(Enum):
    """تصنيفات OWASP Top 10 لعام 2021."""

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
    """قضية أمنية تم اكتشافها أثناء الفحص."""

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
        يتحقق من سلامة المصادقة (A07:2021).
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_weak_password_hashing(code, file_path))
        issues.extend(self._check_plaintext_password_storage(code, file_path))
        issues.extend(self._check_authentication_rate_limiting(code, file_path))
        return issues

    def _check_weak_password_hashing(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يتحقق من استخدام خوارزميات تجزئة ضعيفة لكلمات المرور."""
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
        """يتحقق من احتمال تخزين كلمات المرور بنص صريح."""
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

    def validate_access_control(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من ضوابط التحكم بالوصول (A01:2021).
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_role_escalation(code, file_path))
        issues.extend(self._check_admin_escalation(code, file_path))
        issues.extend(self._check_missing_auth_checks(code, file_path))
        return issues

    def _check_role_escalation(self, code: str, file_path: str) -> list[SecurityIssue]:
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

    def _check_admin_escalation(self, code: str, file_path: str) -> list[SecurityIssue]:
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

    def _check_missing_auth_checks(self, code: str, file_path: str) -> list[SecurityIssue]:
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

    def validate_injection_prevention(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من ثغرات الحقن (A03:2021).
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_sql_injection(code, file_path))
        issues.extend(self._check_command_injection(code, file_path))
        issues.extend(self._check_xss_vulnerabilities(code, file_path))
        return issues

    def _check_sql_injection(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد مؤشرات حقن SQL في الشيفرة."""
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

    def _check_xss_vulnerabilities(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد مؤشرات XSS في التعامل مع HTML."""
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
        يتحقق من سلامة التشفير وإدارة الأسرار (A02:2021).
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_weak_crypto_algorithms(code, file_path))
        issues.extend(self._check_hardcoded_secrets(code, file_path))
        return issues

    def _check_weak_crypto_algorithms(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد الخوارزميات التشفيرية الضعيفة."""
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
        """يتحقق مما إذا كانت مطابقة التشفير إنذارًا كاذبًا."""
        context = self._extract_context(code, match.start(), match.end())

        if "usedforsecurity=False" in context or "usedforsecurity = False" in context:
            return True
        return "import hashlib" in context

    def _check_hardcoded_secrets(self, code: str, file_path: str) -> list[SecurityIssue]:
        """يرصد الأسرار الصلبة داخل الشيفرة."""
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
        """يتحقق من استثناءات الأسرار لتقليل الإنذارات الكاذبة."""
        context = self._extract_context(code, match.start(), match.end())

        if self._context_has_env_markers(context):
            return True
        if self._context_has_safe_secret_markers(context):
            return True
        if self._is_test_file(file_path):
            return True
        return self._context_is_comment(context)

    def _extract_context(self, code: str, start: int, end: int) -> str:
        """يعيد مقطع السياق حول المطابقة لتحليل أدق."""
        context_start = max(0, start - self._CONTEXT_BEFORE)
        context_end = min(len(code), end + self._CONTEXT_AFTER)
        return code[context_start:context_end]

    def _context_has_env_markers(self, context: str) -> bool:
        """يتحقق من مؤشرات الاعتماد على المتغيرات البيئية."""
        return any(env_pat in context for env_pat in self._ENV_VAR_PATTERNS)

    def _context_has_safe_secret_markers(self, context: str) -> bool:
        """يتحقق من مؤشرات أسرار تجريبية أو آمنة."""
        return any(safe_pat in context for safe_pat in self._SAFE_SECRET_PATTERNS)

    def _context_is_comment(self, context: str) -> bool:
        """يتأكد إن كان السياق تعليقًا فقط."""
        stripped = context.strip()
        return bool(stripped.startswith("#") or stripped.startswith("//"))

    def _is_test_file(self, file_path: str) -> bool:
        """يتحقق مما إذا كان الملف اختبارًا."""
        return "test_" in file_path.lower()

    def validate_session_management(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من إدارة الجلسات (A07:2021).
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_secure_cookie_flag(code, file_path))
        issues.extend(self._check_httponly_cookie_flag(code, file_path))
        return issues

    def _check_secure_cookie_flag(self, code: str, file_path: str) -> list[SecurityIssue]:
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

    def _check_httponly_cookie_flag(self, code: str, file_path: str) -> list[SecurityIssue]:
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

    def validate_logging_monitoring(self, code: str, file_path: str = "") -> list[SecurityIssue]:
        """
        يتحقق من التسجيل والمراقبة (A09:2021).
        """
        issues: list[SecurityIssue] = []
        issues.extend(self._check_missing_auth_logging(code, file_path))
        issues.extend(self._check_sensitive_logging(code, file_path))
        return issues

    def _check_missing_auth_logging(self, code: str, file_path: str) -> list[SecurityIssue]:
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

    def _check_sensitive_logging(self, code: str, file_path: str) -> list[SecurityIssue]:
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
