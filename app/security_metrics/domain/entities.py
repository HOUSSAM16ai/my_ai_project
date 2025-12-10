"""Domain entities - Pure business objects."""

from dataclasses import dataclass, field
from datetime import datetime

from app.security_metrics.domain.value_objects import RiskLevel, Severity, TrendDirection


@dataclass
class SecurityFinding:
    """Security finding entity."""

    id: str
    severity: Severity
    rule_id: str
    file_path: str
    line_number: int
    message: str
    cwe_id: str | None = None
    owasp_category: str | None = None
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    false_positive: bool = False
    fixed: bool = False
    fix_time_hours: float | None = None
    developer_id: str | None = None


@dataclass
class SecurityMetrics:
    """Security metrics entity."""

    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    findings_per_1000_loc: float
    new_findings_last_24h: int
    fixed_findings_last_24h: int
    false_positive_rate: float
    mean_time_to_detect: float
    mean_time_to_fix: float
    overall_risk_score: float
    security_debt_score: float
    trend_direction: TrendDirection
    findings_per_developer: dict[str, int]
    fix_rate_per_developer: dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskScore:
    """Risk assessment score."""

    score: float
    level: RiskLevel
    breakdown: dict[str, float]
    timestamp: datetime


@dataclass
class DeveloperSecurityScore:
    """Developer security performance score."""

    developer_id: str
    score: float
    findings_count: int
    fix_rate: float
    avg_fix_time: float
    timestamp: datetime


@dataclass
class SecurityDebt:
    """Security debt calculation."""

    total_debt_hours: float
    debt_by_severity: dict[str, float]
    estimated_cost: float
    priority_items: list[str]
    timestamp: datetime
