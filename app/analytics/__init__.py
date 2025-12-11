"""User Analytics & Business Metrics Module."""

import threading

from .domain import (
    ABTestResults,
    ABTestVariant,
    CohortAnalysis,
    ConversionMetrics,
    EngagementMetrics,
    EventType,
    NPSMetrics,
    RetentionMetrics,
    RevenueMetrics,
    UserEvent,
    UserSegment,
    UserSession,
)
from .facade import UserAnalyticsMetricsService

__all__ = [
    # Main service
    "UserAnalyticsMetricsService",
    "get_user_analytics_service",
    # Domain exports
    "EventType",
    "UserSegment",
    "ABTestVariant",
    "UserEvent",
    "UserSession",
    "EngagementMetrics",
    "ConversionMetrics",
    "RetentionMetrics",
    "NPSMetrics",
    "ABTestResults",
    "CohortAnalysis",
    "RevenueMetrics",
]

# Singleton instance
_user_analytics_service: UserAnalyticsMetricsService | None = None
_service_lock = threading.Lock()


def get_user_analytics_service() -> UserAnalyticsMetricsService:
    """Get singleton user analytics service instance"""
    global _user_analytics_service
    if _user_analytics_service is None:
        with _service_lock:
            if _user_analytics_service is None:
                _user_analytics_service = UserAnalyticsMetricsService()
    return _user_analytics_service
