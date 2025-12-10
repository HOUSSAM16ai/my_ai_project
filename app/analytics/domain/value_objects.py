"""Value objects for analytics domain."""

from enum import Enum


class MetricType(Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TimeGranularity(Enum):
    """Time granularity for analytics."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class BehaviorPattern(Enum):
    """User behavior patterns."""

    POWER_USER = "power_user"
    CASUAL_USER = "casual_user"
    CHURNING = "churning"
    GROWING = "growing"
    SEASONAL = "seasonal"
