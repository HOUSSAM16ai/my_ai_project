# app/services/analytics/domain/__init__.py
"""
Analytics Domain Layer
=======================
Pure domain logic for user analytics.

Following DDD principles:
- Rich domain models
- Clear boundaries
- Business logic encapsulation
"""

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

__all__ = [
    # Enums
    "EventType",
    "UserSegment",
    "ABTestVariant",
    # Value Objects
    "UserEvent",
    "EngagementMetrics",
    "ConversionMetrics",
    "RetentionMetrics",
    "NPSMetrics",
    # Entities
    "UserSession",
    "ABTestResults",
    "CohortAnalysis",
    "RevenueMetrics",
]
