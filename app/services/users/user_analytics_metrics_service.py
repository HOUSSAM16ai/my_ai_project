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
# We import actual models from app.analytics.models and entities
from app.analytics.enums import (
    ABTestVariant,
    EventType,
    UserSegment,
)
from app.analytics.models import (
    ABTestResults,
    CohortAnalysis,
    ConversionMetrics,
    EngagementMetrics,
    NPSMetrics,
    RetentionMetrics,
    RevenueMetrics,
    UserEvent,
    UserSession,
)
from app.analytics.service import (
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
