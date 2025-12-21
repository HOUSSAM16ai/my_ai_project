"""
Analytics Module - Unified Analytics Service.
Consolidated from app/analytics, app/services/analytics, and app/services/api_advanced_analytics.
"""

# 1. Enums & Value Objects
from .enums import (
    EventType,
    UserSegment,
    ABTestVariant,
)
from .value_objects import (
    MetricType,
    BehaviorPattern,
    TimeGranularity,
)

# 2. Domain Models & Entities
from .models import (
    UserEvent,
    UserSession,
    EngagementMetrics,
    ConversionMetrics,
    RetentionMetrics,
    NPSMetrics,
    ABTestResults,
    CohortAnalysis,
    RevenueMetrics,
    UserData,
)
from .entities import (
    UsageMetric,
    UserJourney,
    Anomaly,
    BehaviorProfile,
    AnalyticsReport,
)

# 3. Ports (Interfaces)
from .ports import (
    EventStorePort,
    SessionStorePort,
    UserStorePort,
    ActiveUsersStorePort,
    ABTestStorePort,
    NPSStorePort,
)
from .interfaces import (
    AnomalyDetector,
    MetricsRepository,
    ReportGenerator,
)

# 4. Stores (Implementations)
from .in_memory_stores import (
    InMemoryABTestStore,
    InMemoryNPSStore,
    InMemorySessionStore,
    InMemoryUserStore,
    InMemoryActiveUsersStore,
    InMemoryEventStore,
    InMemoryCohortStore,
    InMemoryRevenueStore
)
from .in_memory_repository import InMemoryMetricsRepository

# 5. Services & Facades
from .service import (
    UserAnalyticsMetricsService,
    SystemAnalyticsService,
    get_user_analytics_service,
    reset_analytics_service,
    AnalyticsFacade,
    get_analytics_facade,
    get_analytics_service
)

# Export all symbols
__all__ = [
    # Enums & Value Objects
    "EventType",
    "UserSegment",
    "ABTestVariant",
    "MetricType",
    "BehaviorPattern",
    "TimeGranularity",

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
    "UserData",
    "UsageMetric",
    "UserJourney",
    "Anomaly",
    "BehaviorProfile",
    "AnalyticsReport",

    # Ports
    "EventStorePort",
    "SessionStorePort",
    "UserStorePort",
    "ActiveUsersStorePort",
    "ABTestStorePort",
    "NPSStorePort",
    "AnomalyDetector",
    "MetricsRepository",
    "ReportGenerator",

    # Stores
    "InMemoryABTestStore",
    "InMemoryNPSStore",
    "InMemorySessionStore",
    "InMemoryUserStore",
    "InMemoryActiveUsersStore",
    "InMemoryEventStore",
    "InMemoryCohortStore",
    "InMemoryRevenueStore",
    "InMemoryMetricsRepository",

    # Services
    "UserAnalyticsMetricsService",
    "SystemAnalyticsService",
    "get_user_analytics_service",
    "reset_analytics_service",
    "AnalyticsFacade",
    "get_analytics_facade",
    "get_analytics_service",
]
