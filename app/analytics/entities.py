"""Domain entities - Pure business objects."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .value_objects import BehaviorPattern, MetricType, TimeGranularity


@dataclass
class UsageMetric:
    """Usage metric data point."""

    timestamp: datetime
    metric_type: MetricType
    name: str
    value: float
    endpoint: str | None = None
    method: str | None = None
    status_code: int | None = None
    user_id: str | None = None
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class UserJourney:
    """User journey tracking."""

    user_id: str
    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    total_requests: int = 0
    unique_endpoints: int = 0
    total_duration_seconds: float = 0.0
    completed_actions: list[str] = field(default_factory=list)
    errors_encountered: int = 0


@dataclass
class Anomaly:
    """Detected anomaly."""

    type: str
    timestamp: datetime
    severity: str
    details: dict[str, Any]
    description: str = ""


@dataclass
class BehaviorProfile:
    """User behavior profile."""

    user_id: str
    pattern: BehaviorPattern
    avg_requests_per_day: float
    avg_session_duration: float
    favorite_endpoints: list[str]
    peak_usage_hours: list[int]
    churn_probability: float = 0.0
    lifetime_value_estimate: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AnalyticsReport:
    """Analytics report."""

    report_id: str
    name: str
    generated_at: datetime
    time_range: tuple[datetime, datetime]
    granularity: TimeGranularity
    metrics: dict[str, Any] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
