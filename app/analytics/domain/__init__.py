"""Analytics domain layer."""

from .enums import ABTestVariant, EventType, UserSegment
from .models import (
    ABTestResults,
    CohortAnalysis,
    ConversionMetrics,
    EngagementMetrics,
    NPSMetrics,
    RetentionMetrics,
    RevenueMetrics,
    UserData,
    UserEvent,
    UserSession,
)
from .ports import (
    ABTestStorePort,
    ActiveUsersStorePort,
    EventStorePort,
    NPSStorePort,
    SessionStorePort,
    UserStorePort,
)

__all__ = [
    # Enums
    "EventType",
    "UserSegment",
    "ABTestVariant",
    # Models
    "UserEvent",
    "UserSession",
    "UserData",
    "EngagementMetrics",
    "ConversionMetrics",
    "RetentionMetrics",
    "NPSMetrics",
    "ABTestResults",
    "CohortAnalysis",
    "RevenueMetrics",
    # Ports
    "EventStorePort",
    "SessionStorePort",
    "UserStorePort",
    "ActiveUsersStorePort",
    "ABTestStorePort",
    "NPSStorePort",
]
