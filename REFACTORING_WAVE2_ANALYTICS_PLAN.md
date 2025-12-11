# User Analytics Service Refactoring Plan - Wave 2

## Current State
- **File**: `app/services/user_analytics_metrics_service.py`
- **Size**: 800 lines / 28KB
- **Responsibilities**: 8+ (Event Tracking, Sessions, Metrics, A/B Testing, NPS, Segmentation, Cohorts, Revenue)

## Target Architecture

```
app/analytics/
├── __init__.py                    # Public API
├── facade.py                      # UserAnalyticsService (backward compatible)
├── README.md                      # Documentation
│
├── domain/
│   ├── __init__.py
│   ├── models.py                  # Entities (UserEvent, UserSession, Metrics dataclasses)
│   ├── enums.py                   # EventType, UserSegment, ABTestVariant
│   └── ports.py                   # Protocols (EventStore, MetricsCalculator, etc.)
│
├── application/
│   ├── __init__.py
│   ├── event_tracker.py           # Event tracking use case
│   ├── session_manager.py         # Session management
│   ├── metrics_calculator.py      # Engagement, Conversion, Retention metrics
│   ├── ab_test_manager.py         # A/B testing logic
│   ├── nps_manager.py             # NPS scoring
│   └── user_segmentation.py       # User segmentation logic
│
└── infrastructure/
    ├── __init__.py
    ├── in_memory_event_store.py   # In-memory event storage
    └── in_memory_metrics_store.py # In-memory metrics storage
```

## Responsibilities Breakdown

### Domain Layer (models.py, enums.py, ports.py)
- **Entities**: UserEvent, UserSession, EngagementMetrics, ConversionMetrics, RetentionMetrics, NPSMetrics, ABTestResults, CohortAnalysis, RevenueMetrics
- **Enums**: EventType, UserSegment, ABTestVariant
- **Ports**: EventStorePort, MetricsStorePort, SessionStorePort

### Application Layer
1. **EventTracker** (event_tracker.py)
   - track_event()
   - _generate_event_id()

2. **SessionManager** (session_manager.py)
   - start_session()
   - end_session()
   - _generate_session_id()

3. **MetricsCalculator** (metrics_calculator.py)
   - get_engagement_metrics()
   - get_conversion_metrics()
   - get_retention_metrics()
   - export_metrics_summary()

4. **ABTestManager** (ab_test_manager.py)
   - create_ab_test()
   - assign_variant()
   - record_ab_conversion()
   - get_ab_test_results()

5. **NPSManager** (nps_manager.py)
   - record_nps_response()
   - get_nps_metrics()

6. **UserSegmentation** (user_segmentation.py)
   - segment_users()

### Infrastructure Layer
- **InMemoryEventStore**: Stores events, sessions, users
- **InMemoryMetricsStore**: Stores A/B tests, NPS responses, cohorts

### Facade Layer
- **UserAnalyticsService**: Delegates to application services, maintains backward compatibility

## Migration Strategy
1. Create domain layer (models, enums, ports)
2. Create infrastructure layer (in-memory stores)
3. Create application layer (6 services)
4. Create facade with delegation
5. Update imports in existing code
6. Add comprehensive README.md

## Success Metrics
- Reduce main file from 800 lines to ~150 lines (facade)
- 10+ specialized files
- Each file has single responsibility
- 100% backward compatible
- Full test coverage maintained
