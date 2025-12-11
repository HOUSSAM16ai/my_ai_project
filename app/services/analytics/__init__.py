# app/services/analytics/__init__.py
"""
Analytics Module - Layered Architecture
========================================
User analytics and metrics service following Hexagonal Architecture.

Refactored from monolithic UserAnalyticsMetricsService (800 lines)
into clean layered architecture with clear separation of concerns.

Architecture:
- Domain Layer: Pure business logic and entities
- Application Layer: Use cases and orchestration
- Infrastructure Layer: External adapters and persistence
- Facade: Backward-compatible API

Reduction: 800 lines → ~250 lines facade + specialized services
"""

# Domain exports
from app.services.analytics.domain import (
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

# Application layer exports
from app.services.analytics.application.event_tracker import EventTracker
from app.services.analytics.application.engagement_analyzer import EngagementAnalyzer

# Infrastructure exports
from app.services.analytics.infrastructure.in_memory_repository import (
    InMemoryEventRepository,
    InMemorySessionRepository,
)

# Facade (backward compatibility)
from app.services.analytics.facade import (
    UserAnalyticsMetricsService,
    get_user_analytics_service,
    reset_analytics_service,
)

__all__ = [
    # Domain models
    "EventType",
    "UserSegment",
    "ABTestVariant",
    "UserEvent",
    "EngagementMetrics",
    "ConversionMetrics",
    "RetentionMetrics",
    "NPSMetrics",
    "UserSession",
    "ABTestResults",
    "CohortAnalysis",
    "RevenueMetrics",
    # Application services
    "EventTracker",
    "EngagementAnalyzer",
    # Infrastructure
    "InMemoryEventRepository",
    "InMemorySessionRepository",
    # Facade (backward compatibility)
    "UserAnalyticsMetricsService",
    "get_user_analytics_service",
    "reset_analytics_service",
]
