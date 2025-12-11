# app/services/user_analytics_metrics_service.py
"""
User Analytics & Metrics Service - LEGACY COMPATIBILITY
========================================================
This file now imports from the refactored analytics module.

Original file: 800+ lines
Refactored: Delegates to analytics/ module following Hexagonal Architecture

For new code, import from: app.services.analytics
"""

# Legacy imports for backward compatibility
from app.services.analytics.domain.models import (
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
from app.services.analytics.facade import (
    UserAnalyticsMetricsService,
    get_user_analytics_service,
    reset_analytics_service,
)

# Re-export everything for backward compatibility
__all__ = [
    # Enums
    "EventType",
    "UserSegment",
    "ABTestVariant",
    # Models
    "UserEvent",
    "UserSession",
    "EngagementMetrics",
    "ConversionMetrics",
    "RetentionMetrics",
    "NPSMetrics",
    "ABTestResults",
    "CohortAnalysis",
    "RevenueMetrics",
    # Service
    "UserAnalyticsMetricsService",
    "get_user_analytics_service",
    "reset_analytics_service",
]
