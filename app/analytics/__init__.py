"""
Analytics Module - Unified Analytics Service.
Consolidated from app/analytics, app/services/analytics, and app/services/api_advanced_analytics.
"""

# 1. Enums & Value Objects
from .entities import (
    AnalyticsReport,
    Anomaly,
    BehaviorProfile,
    UsageMetric,
    UserJourney,
)
from .enums import (
    ABTestVariant,
    EventType,
    UserSegment,
)
from .in_memory_repository import InMemoryMetricsRepository

# 4. Stores (Implementations)
from .in_memory_stores import (
    InMemoryABTestStore,
    InMemoryActiveUsersStore,
    InMemoryCohortStore,
    InMemoryEventStore,
    InMemoryNPSStore,
    InMemoryRevenueStore,
    InMemorySessionStore,
    InMemoryUserStore,
)
from .interfaces import (
    AnomalyDetector,
    MetricsRepository,
    ReportGenerator,
)

# 2. Domain Models & Entities
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

# 3. Ports (Interfaces)
from .ports import (
    ABTestStorePort,
    ActiveUsersStorePort,
    EventStorePort,
    NPSStorePort,
    SessionStorePort,
    UserStorePort,
)

# 5. Services & Facades
from .service import (
    AnalyticsFacade,
    SystemAnalyticsService,
    UserAnalyticsMetricsService,
    get_analytics_facade,
    get_analytics_service,
    get_user_analytics_service,
    reset_analytics_service,
)
from .value_objects import (
    BehaviorPattern,
    MetricType,
    TimeGranularity,
)

# Export all symbols
__all__ = [
    "ABTestResults",
    "ABTestStorePort",
    "ABTestVariant",
    "ActiveUsersStorePort",
    "AnalyticsFacade",
    "AnalyticsReport",
    "Anomaly",
    "AnomalyDetector",
    "BehaviorPattern",
    "BehaviorProfile",
    "CohortAnalysis",
    "ConversionMetrics",
    "EngagementMetrics",
    # Ports
    "EventStorePort",
    # Enums & Value Objects
    "EventType",
    # Stores
    "InMemoryABTestStore",
    "InMemoryActiveUsersStore",
    "InMemoryCohortStore",
    "InMemoryEventStore",
    "InMemoryMetricsRepository",
    "InMemoryNPSStore",
    "InMemoryRevenueStore",
    "InMemorySessionStore",
    "InMemoryUserStore",
    "MetricType",
    "MetricsRepository",
    "NPSMetrics",
    "NPSStorePort",
    "ReportGenerator",
    "RetentionMetrics",
    "RevenueMetrics",
    "SessionStorePort",
    "SystemAnalyticsService",
    "TimeGranularity",
    "UsageMetric",
    # Services
    "UserAnalyticsMetricsService",
    "UserData",
    # Models
    "UserEvent",
    "UserJourney",
    "UserSegment",
    "UserSession",
    "UserStorePort",
    "get_analytics_facade",
    "get_analytics_service",
    "get_user_analytics_service",
    "reset_analytics_service",
]
