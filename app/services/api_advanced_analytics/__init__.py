"""
API Advanced Analytics Service - Hexagonal Architecture
=======================================================
Clean, modular analytics service following SOLID principles.

Architecture:
- domain/: Pure business logic (models, enums, ports)
- application/: Use cases and orchestration
- infrastructure/: External adapters (repositories)
- facade.py: Backward-compatible interface

Usage:
    from app.services.api_advanced_analytics import AdvancedAnalyticsService
    
    service = AdvancedAnalyticsService()
    service.track_request(endpoint="/api/users", method="GET", ...)
"""

# Public API exports (for new code)
from .application import AnalyticsManager
from .domain import (
    AnalyticsReport,
    BehaviorPattern,
    BehaviorProfile,
    MetricType,
    TimeGranularity,
    UsageMetric,
    UserJourney,
)
from .facade import AdvancedAnalyticsService, get_advanced_analytics_service
from .infrastructure import (
    InMemoryBehaviorRepository,
    InMemoryJourneyRepository,
    InMemoryMetricsRepository,
    InMemoryReportRepository,
)

__all__ = [
    # Facade (backward compatible)
    "AdvancedAnalyticsService",
    "get_advanced_analytics_service",
    # Application
    "AnalyticsManager",
    # Domain Models
    "AnalyticsReport",
    "BehaviorPattern",
    "BehaviorProfile",
    "MetricType",
    "TimeGranularity",
    "UsageMetric",
    "UserJourney",
    # Infrastructure
    "InMemoryBehaviorRepository",
    "InMemoryJourneyRepository",
    "InMemoryMetricsRepository",
    "InMemoryReportRepository",
]
