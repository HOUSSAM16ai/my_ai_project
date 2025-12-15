"""
API Advanced Analytics - Domain Models
======================================
Pure business logic models with zero external dependencies.

Contains:
- Enumerations (MetricType, TimeGranularity, BehaviorPattern)
- Value Objects (UsageMetric, UserJourney, AnalyticsReport, BehaviorProfile)
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MetricType(Enum):
    """Types of metrics tracked in the analytics system."""
    COUNTER = 'counter'
    GAUGE = 'gauge'
    HISTOGRAM = 'histogram'
    SUMMARY = 'summary'


class TimeGranularity(Enum):
    """Time granularity for aggregating analytics data."""
    MINUTE = 'minute'
    HOUR = 'hour'
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'


class BehaviorPattern(Enum):
    """User behavior classification patterns."""
    POWER_USER = 'power_user'
    CASUAL_USER = 'casual_user'
    CHURNING = 'churning'
    GROWING = 'growing'
    SEASONAL = 'seasonal'


@dataclass
class UsageMetric:
    """
    Immutable usage metric data point.
    
    Represents a single measurement at a specific point in time.
    """
    timestamp: datetime
    metric_type: MetricType
    name: str
    value: float
    endpoint: str | None = None
    method: str | None = None
    status_code: int | None = None
    user_id: str | None = None
    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate metric data."""
        if not self.name:
            raise ValueError('Metric name cannot be empty')
        if self.value < 0:
            raise ValueError('Metric value cannot be negative')


@dataclass
class UserJourney:
    """
    Tracks a user's journey through the system.
    
    Represents a session with all events and interactions.
    """
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

    def add_event(self, event: dict[str, Any]) ->None:
        """Add an event to the journey."""
        self.events.append(event)
        self.total_requests += 1

    @property
    def is_active(self) ->bool:
        """Check if journey is still active."""
        return self.end_time is None

    @property
    def duration_seconds(self) ->float:
        """Calculate journey duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now(UTC) - self.start_time).total_seconds()


@dataclass
class AnalyticsReport:
    """
    Generated analytics report with insights.
    
    Aggregates metrics over a time range with actionable insights.
    """
    report_id: str
    name: str
    generated_at: datetime
    time_range: tuple[datetime, datetime]
    granularity: TimeGranularity
    metrics: dict[str, Any] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def add_metric(self, key: str, value: Any) ->None:
        """Add a metric to the report."""
        self.metrics[key] = value

    def add_insight(self, insight: str) ->None:
        """Add a business insight."""
        self.insights.append(insight)

    def add_recommendation(self, recommendation: str) ->None:
        """Add an actionable recommendation."""
        self.recommendations.append(recommendation)


@dataclass
class BehaviorProfile:
    """
    User behavior analysis profile.
    
    Machine learning-derived insights about user patterns.
    """
    user_id: str
    pattern: BehaviorPattern
    avg_requests_per_day: float
    avg_session_duration: float
    favorite_endpoints: list[str]
    peak_usage_hours: list[int]
    churn_probability: float = 0.0
    lifetime_value_estimate: float = 0.0
    last_updated: datetime = field(default_factory=lambda : datetime.now(UTC))
