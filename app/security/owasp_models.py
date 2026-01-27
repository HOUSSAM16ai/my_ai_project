"""نماذج OWASP الأمنية المهيكلة لتقارير الفحص والتحقق."""

from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


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
