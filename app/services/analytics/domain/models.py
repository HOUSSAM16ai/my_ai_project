"""
Analytics Domain Models
========================
Pure domain entities and value objects for user analytics.

Following DDD principles:
- Rich domain models
- Immutable value objects
- Clear business rules
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(Enum):
    """User event types"""
    PAGE_VIEW = 'page_view'
    CLICK = 'click'
    FORM_SUBMIT = 'form_submit'
    CONVERSION = 'conversion'
    PURCHASE = 'purchase'
    SIGNUP = 'signup'
    LOGIN = 'login'
    LOGOUT = 'logout'
    FEATURE_USE = 'feature_use'
    ERROR = 'error'
    CUSTOM = 'custom'


class UserSegment(Enum):
    """User segment types"""
    NEW = 'new'
    ACTIVE = 'active'
    POWER = 'power'
    AT_RISK = 'at_risk'
    CHURNED = 'churned'
    RESURRECTED = 'resurrected'


class ABTestVariant(Enum):
    """A/B test variant types"""
    CONTROL = 'control'
    VARIANT_A = 'variant_a'
    VARIANT_B = 'variant_b'
    VARIANT_C = 'variant_c'


@dataclass(frozen=True)
class UserEvent:
    """
    Immutable user event value object.

    Represents a single user interaction with the system.
    """
    event_id: str
    user_id: int
    session_id: str
    event_type: EventType
    event_name: str
    timestamp: datetime
    properties: dict[str, Any] = field(default_factory=dict)
    page_url: str | None = None
    device_type: str | None = None

    def to_dict(self) ->dict[str, Any]:
        """Convert to dictionary"""
        return {'event_id': self.event_id, 'user_id': self.user_id,
            'session_id': self.session_id, 'event_type': self.event_type.
            value, 'event_name': self.event_name, 'timestamp': self.
            timestamp.isoformat(), 'properties': self.properties,
            'page_url': self.page_url, 'device_type': self.device_type}


@dataclass(frozen=True)
class EngagementMetrics:
    """
    Engagement metrics value object.

    Calculated metrics for user engagement analysis.
    """
    dau: int
    wau: int
    mau: int
    avg_session_duration: float
    avg_events_per_session: float
    bounce_rate: float
    return_rate: float


@dataclass(frozen=True)
class ConversionMetrics:
    """
    Conversion metrics value object.

    Tracks conversion rates and funnel performance.
    """
    total_sessions: int
    conversions: int
    conversion_rate: float
    avg_time_to_convert: float
    drop_off_rate: float

    def to_dict(self) ->dict[str, Any]:
        """Convert to dictionary"""
        return {'total_sessions': self.total_sessions, 'conversions': self.
            conversions, 'conversion_rate': self.conversion_rate,
            'avg_time_to_convert': self.avg_time_to_convert,
            'drop_off_rate': self.drop_off_rate}


@dataclass(frozen=True)
class RetentionMetrics:
    """
    User retention metrics value object.

    Tracks user retention and churn.
    """
    retention_rate_7d: float
    retention_rate_30d: float
    churn_rate: float
    avg_user_lifetime: float

    def to_dict(self) ->dict[str, Any]:
        """Convert to dictionary"""
        return {'retention_rate_7d': self.retention_rate_7d,
            'retention_rate_30d': self.retention_rate_30d, 'churn_rate':
            self.churn_rate, 'avg_user_lifetime': self.avg_user_lifetime}


@dataclass(frozen=True)
class NPSMetrics:
    """
    Net Promoter Score metrics value object.

    Customer satisfaction and loyalty metrics.
    """
    nps_score: float
    promoters: int
    passives: int
    detractors: int
    total_responses: int


@dataclass
class UserSession:
    """
    User session entity.

    Mutable entity representing an active user session.
    Tracks interactions and state changes over time.
    """
    session_id: str
    user_id: int
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float = 0.0
    page_views: int = 0
    events: int = 0
    conversions: int = 0
    device_type: str = 'unknown'
    entry_page: str = '/'
    exit_page: str | None = None

    def update_activity(self, event_type: EventType, page_url: (str | None)
        =None, timestamp: (datetime | None)=None) ->None:
        """Update session with new activity"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.events += 1
        if event_type == EventType.PAGE_VIEW:
            self.page_views += 1
        if event_type == EventType.CONVERSION:
            self.conversions += 1
        self.end_time = timestamp
        self.duration_seconds = (self.end_time - self.start_time
            ).total_seconds()
        if page_url:
            self.exit_page = page_url

    @property
    def is_bounce(self) ->bool:
        """Check if session is a bounce (single page view)"""
        return self.page_views <= 1


@dataclass
class ABTestResults:
    """
    A/B test results entity.

    Mutable entity for tracking A/B test performance.
    """
    test_id: str
    test_name: str
    variants: dict[ABTestVariant, int] = field(default_factory=dict)
    conversions: dict[ABTestVariant, int] = field(default_factory=dict)
    start_date: datetime = field(default_factory=datetime.utcnow)
    end_date: datetime | None = None
    is_active: bool = True

    def record_conversion(self, variant: ABTestVariant) ->None:
        """Record a conversion for variant"""
        if variant not in self.conversions:
            self.conversions[variant] = 0
        self.conversions[variant] += 1

    def get_conversion_rate(self, variant: ABTestVariant) ->float:
        """Calculate conversion rate for variant"""
        views = self.variants.get(variant, 0)
        conversions = self.conversions.get(variant, 0)
        return conversions / views if views > 0 else 0.0

    def get_winner(self) ->(ABTestVariant | None):
        """Determine winning variant based on conversion rate"""
        if not self.variants:
            return None
        best_variant = None
        best_rate = 0.0
        for variant in self.variants:
            rate = self.get_conversion_rate(variant)
            if rate > best_rate:
                best_rate = rate
                best_variant = variant
        return best_variant


@dataclass
class CohortAnalysis:
    """
    Cohort analysis entity.

    Tracks behavior of user cohorts over time.
    """
    cohort_id: str
    cohort_name: str
    creation_date: datetime
    users: set[int] = field(default_factory=set)
    retention_data: dict[int, float] = field(default_factory=dict)

    def add_user(self, user_id: int) ->None:
        """Add user to cohort"""
        self.users.add(user_id)

    def get_retention_curve(self) ->list[tuple[int, float]]:
        """Get retention curve data"""
        return sorted(self.retention_data.items())


@dataclass
class RevenueMetrics:
    """
    Revenue metrics entity.

    Tracks financial performance metrics.
    """
    total_revenue: float = 0.0
    total_transactions: int = 0
    unique_paying_users: set[int] = field(default_factory=set)
    revenue_by_segment: dict[UserSegment, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


__all__ = ['EventType', 'UserSegment', 'ABTestVariant', 'UserEvent',
    'EngagementMetrics', 'ConversionMetrics', 'RetentionMetrics',
    'NPSMetrics', 'UserSession', 'ABTestResults', 'CohortAnalysis',
    'RevenueMetrics']
