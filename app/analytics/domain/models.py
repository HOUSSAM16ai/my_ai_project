"""Analytics domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import EventType


@dataclass
class UserEvent:
    """Single user event"""

    event_id: str
    user_id: int
    session_id: str
    event_type: EventType
    event_name: str
    timestamp: datetime
    properties: dict[str, Any] = field(default_factory=dict)
    page_url: str | None = None
    referrer: str | None = None
    device_type: str | None = None
    browser: str | None = None
    country: str | None = None


@dataclass
class UserSession:
    """User session data"""

    session_id: str
    user_id: int
    start_time: datetime
    end_time: datetime | None
    duration_seconds: float
    page_views: int
    events: int
    conversions: int
    device_type: str
    entry_page: str
    exit_page: str | None


@dataclass
class EngagementMetrics:
    """User engagement metrics"""

    dau: int  # Daily Active Users
    wau: int  # Weekly Active Users
    mau: int  # Monthly Active Users
    avg_session_duration: float
    avg_sessions_per_user: float
    avg_events_per_session: float
    bounce_rate: float
    return_rate: float
    time_window: str


@dataclass
class ConversionMetrics:
    """Conversion and funnel metrics"""

    conversion_rate: float
    total_conversions: int
    total_visitors: int
    avg_time_to_convert: float
    conversion_value: float
    funnel_completion_rate: float
    drop_off_points: dict[str, float]


@dataclass
class RetentionMetrics:
    """User retention metrics"""

    day_1_retention: float
    day_7_retention: float
    day_30_retention: float
    cohort_size: int
    churn_rate: float
    avg_lifetime_days: float


@dataclass
class NPSMetrics:
    """Net Promoter Score metrics"""

    nps_score: float  # -100 to 100
    promoters_percent: float  # 9-10 ratings
    passives_percent: float  # 7-8 ratings
    detractors_percent: float  # 0-6 ratings
    total_responses: int
    avg_score: float


@dataclass
class ABTestResults:
    """A/B test results"""

    test_id: str
    test_name: str
    control_variant: str
    test_variants: list[str]
    control_conversion_rate: float
    variant_conversion_rates: dict[str, float]
    control_sample_size: int
    variant_sample_sizes: dict[str, int]
    statistical_significance: float
    winner: str | None
    improvement_percent: float


@dataclass
class CohortAnalysis:
    """Cohort analysis data"""

    cohort_id: str
    cohort_name: str
    cohort_date: datetime
    cohort_size: int
    retention_by_day: dict[int, float]
    revenue_by_day: dict[int, float]
    ltv: float  # Lifetime Value


@dataclass
class RevenueMetrics:
    """Business revenue metrics"""

    total_revenue: float
    arr: float  # Annual Recurring Revenue
    mrr: float  # Monthly Recurring Revenue
    arpu: float  # Average Revenue Per User
    arppu: float  # Average Revenue Per Paying User
    ltv: float  # Lifetime Value
    cac: float  # Customer Acquisition Cost
    ltv_cac_ratio: float
    paying_users: int
    total_users: int


@dataclass
class UserData:
    """User tracking data"""

    user_id: int
    first_seen: datetime
    last_seen: datetime
    total_events: int
    total_sessions: int
    total_conversions: int
    segment: Any  # UserSegment, but avoiding circular import
