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
