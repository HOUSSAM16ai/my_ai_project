# Analytics Module - Layered Architecture

## Overview

The Analytics module provides comprehensive user analytics and metrics tracking capabilities. It has been refactored from a monolithic 800-line `user_analytics_metrics_service.py` into a clean, layered architecture following Hexagonal Architecture / Ports & Adapters pattern.

## Architecture

```
app/services/analytics/
│
├── __init__.py                    # Public API exports
├── facade.py                      # Backward-compatible facade
├── README.md                      # This file
│
├── domain/                        # Domain Layer (Business Logic)
│   ├── __init__.py
│   ├── models.py                  # Domain entities and value objects
│   └── ports.py                   # Port interfaces (protocols)
│
├── application/                   # Application Layer (Use Cases)
│   ├── __init__.py
│   ├── event_tracker.py           # Event tracking service
│   ├── session_manager.py         # Session management service
│   ├── engagement_analyzer.py     # Engagement metrics service
│   ├── conversion_analyzer.py     # Conversion funnel service
│   ├── retention_analyzer.py      # Retention analysis service
│   ├── nps_manager.py             # NPS scoring service
│   ├── ab_test_manager.py         # A/B testing service
│   └── report_generator.py        # Report generation service
│
└── infrastructure/                # Infrastructure Layer (Adapters)
    ├── __init__.py
    ├── in_memory_repository.py    # In-memory event/session storage
    ├── analytics_aggregator.py    # Metrics calculation engine
    ├── user_segmentation.py       # User classification engine
    └── ab_test_repository.py      # A/B test storage
```

## Refactoring Achievement

### Before
- **Single file**: `user_analytics_metrics_service.py`
- **Size**: 800 lines / 28KB
- **Responsibilities**: 8+ (Event Tracking, Sessions, Metrics, A/B Testing, NPS, Segmentation, Cohorts, Revenue)
- **Complexity**: High coupling, difficult to test, hard to maintain

### After
- **Files**: 18 specialized files
- **Total size**: ~3,300 lines across all files
- **Responsibilities**: Single responsibility per file
- **Architecture**: Clean separation of concerns with Hexagonal Architecture
- **Maintainability**: Each component is independently testable and replaceable

## Key Benefits

### 1. Single Responsibility Principle (SRP)
Each service has one clear responsibility:
- `EventTracker`: Only tracks user events
- `SessionManager`: Only manages user sessions
- `EngagementAnalyzer`: Only calculates engagement metrics
- And so on...

### 2. Dependency Inversion
- Application layer depends on abstractions (Ports), not concrete implementations
- Infrastructure implementations can be swapped without changing business logic
- Easy to replace in-memory storage with PostgreSQL, Redis, ClickHouse, etc.

### 3. Testability
- Each component can be tested in isolation
- Mock dependencies via port interfaces
- Clear boundaries enable focused unit tests

### 4. Backward Compatibility
- The `facade.py` maintains 100% backward compatibility
- Existing code using `UserAnalyticsMetricsService` works without changes
- Gradual migration path available

## Domain Layer

### Models (`domain/models.py`)

**Entities:**
- `UserEvent`: Individual user action/event
- `UserSession`: User session with start/end times
- `EngagementMetrics`: Engagement statistics (DAU, WAU, MAU, etc.)
- `ConversionMetrics`: Conversion funnel statistics
- `RetentionMetrics`: User retention statistics
- `NPSMetrics`: Net Promoter Score metrics
- `ABTestResults`: A/B test results and statistics
- `CohortAnalysis`: Cohort behavior analysis

**Enums:**
- `EventType`: Event type classifications (PAGE_VIEW, CLICK, CONVERSION, etc.)
- `UserSegment`: User segmentation categories (NEW_USER, ACTIVE_USER, POWER_USER, etc.)
- `ABTestVariant`: A/B test variants (CONTROL, VARIANT_A, VARIANT_B, etc.)

### Ports (`domain/ports.py`)

**Repository Ports:**
- `EventRepositoryPort`: Event storage and retrieval
- `SessionRepositoryPort`: Session storage and retrieval

**Service Ports:**
- `AnalyticsAggregatorPort`: Metrics calculation engine
- `UserSegmentationPort`: User classification
- `ABTestManagerPort`: A/B test management

## Application Layer

### EventTracker (`application/event_tracker.py`)
Tracks user events and stores them in the event repository.

**Key Methods:**
- `track_event()`: Track a user event
- `get_user_events()`: Retrieve events for a user
- `get_session_events()`: Retrieve events for a session

### SessionManager (`application/session_manager.py`)
Manages user session lifecycle.

**Key Methods:**
- `start_session()`: Start a new user session
- `end_session()`: End an active session
- `get_active_session()`: Get current active session

### EngagementAnalyzer (`application/engagement_analyzer.py`)
Calculates user engagement metrics.

**Key Methods:**
- `calculate_engagement_metrics()`: Get comprehensive engagement metrics
- `calculate_dau()`: Daily Active Users
- `calculate_wau()`: Weekly Active Users
- `calculate_mau()`: Monthly Active Users

### ConversionAnalyzer (`application/conversion_analyzer.py`)
Analyzes conversion funnels.

**Key Methods:**
- `calculate_funnel_metrics()`: Analyze conversion funnel
- `get_conversion_rate()`: Calculate conversion rate

### RetentionAnalyzer (`application/retention_analyzer.py`)
Analyzes user retention.

**Key Methods:**
- `calculate_retention_metrics()`: Calculate retention rates
- `analyze_cohort()`: Cohort retention analysis

### NPSManager (`application/nps_manager.py`)
Manages Net Promoter Score.

**Key Methods:**
- `record_nps_response()`: Record NPS survey response
- `calculate_nps()`: Calculate overall NPS score

### ABTestManager (`application/ab_test_manager.py`)
Manages A/B testing experiments.

**Key Methods:**
- `create_test()`: Create new A/B test
- `assign_variant()`: Assign user to variant
- `record_conversion()`: Record test conversion
- `get_results()`: Get test results

### ReportGenerator (`application/report_generator.py`)
Generates analytics reports.

**Key Methods:**
- `generate_summary_report()`: Generate comprehensive summary
- `generate_engagement_report()`: Engagement-focused report
- `generate_conversion_report()`: Conversion-focused report

## Infrastructure Layer

### InMemoryEventRepository
Event storage using in-memory data structures.
- Thread-safe operations
- Bounded deque for memory management
- Fast filtering by user, session, event type, time range

### InMemorySessionRepository
Session storage using in-memory data structures.
- Thread-safe operations
- Fast lookups by session ID and user ID
- Session lifecycle management

### InMemoryUserRepository
User metadata storage.
- User activity tracking
- Active user calculations
- User profile management

### InMemoryAnalyticsAggregator
Metrics calculation engine.
- Real-time metric calculations
- Time-series aggregations
- Funnel analysis
- Cohort analytics

### InMemoryUserSegmentation
Rule-based user classification.
- Automatic user segmentation
- Segment tracking and analytics
- Customizable segmentation rules

### InMemoryABTestRepository
A/B test management.
- Deterministic variant assignment
- Conversion tracking
- Statistical analysis
- Test lifecycle management

## Usage Examples

### Basic Usage (via Facade)

```python
from app.services.analytics import UserAnalyticsMetricsService

analytics = UserAnalyticsMetricsService()

# Track an event
event_id = analytics.track_event(
    user_id=123,
    event_type="page_view",
    event_name="HomePage Visit",
    properties={"page": "/home"}
)

# Get engagement metrics
metrics = analytics.get_engagement_metrics()
print(f"DAU: {metrics['dau']}")
print(f"MAU: {metrics['mau']}")
```

### Advanced Usage (Direct Service Access)

```python
from app.services.analytics.application import (
    EventTracker,
    EngagementAnalyzer,
)
from app.services.analytics.infrastructure import (
    InMemoryEventRepository,
    InMemorySessionRepository,
)

# Create repositories
event_repo = InMemoryEventRepository()
session_repo = InMemorySessionRepository()

# Create services
event_tracker = EventTracker(
    event_repository=event_repo,
    session_repository=session_repo,
)

engagement_analyzer = EngagementAnalyzer(
    event_repository=event_repo,
    session_repository=session_repo,
)

# Use services directly
event_tracker.track_event(...)
metrics = engagement_analyzer.calculate_engagement_metrics()
```

## Migration Guide

### Replacing In-Memory Storage with PostgreSQL

1. **Implement PostgreSQL repositories:**
```python
# app/services/analytics/infrastructure/postgresql_repository.py
class PostgreSQLEventRepository(EventRepositoryPort):
    def __init__(self, db_session):
        self.db = db_session
    
    def store_event(self, event: UserEvent) -> None:
        # Store in PostgreSQL
        ...
```

2. **Update facade initialization:**
```python
class UserAnalyticsMetricsService:
    def __init__(self, db_session):
        # Use PostgreSQL instead of in-memory
        self._event_repo = PostgreSQLEventRepository(db_session)
        ...
```

3. **No changes needed in application layer!**
The application services work with the port interface, not the concrete implementation.

## Testing

Each component can be tested independently:

```python
# Test EventTracker in isolation
from app.services.analytics.application import EventTracker
from unittest.mock import Mock

def test_event_tracking():
    # Mock the repositories
    event_repo_mock = Mock()
    session_repo_mock = Mock()
    
    # Create service with mocks
    tracker = EventTracker(
        event_repository=event_repo_mock,
        session_repository=session_repo_mock,
    )
    
    # Test the service
    tracker.track_event(...)
    
    # Verify interactions
    event_repo_mock.store_event.assert_called_once()
```

## Performance Considerations

### In-Memory Repositories
- **Pros**: Fast, no external dependencies, great for development/testing
- **Cons**: Limited capacity, not distributed, data lost on restart
- **Use for**: Development, testing, low-volume applications

### Production Recommendations
- **Events**: ClickHouse, BigQuery, or time-series database
- **Sessions**: Redis or PostgreSQL
- **Metrics**: Pre-aggregated in PostgreSQL or data warehouse
- **A/B Tests**: PostgreSQL with proper indexing

## Future Enhancements

### Planned Infrastructure Implementations
- [ ] PostgreSQL repositories
- [ ] Redis session management
- [ ] ClickHouse event storage
- [ ] BigQuery analytics aggregator
- [ ] ML-based user segmentation
- [ ] Bayesian A/B testing

### Planned Application Services
- [ ] Anomaly detection service
- [ ] Predictive analytics service
- [ ] Real-time alerting service
- [ ] Dashboard data service

## Contributing

When adding new features:

1. **Domain First**: Define entities and ports in domain layer
2. **Application Logic**: Implement use cases in application layer
3. **Infrastructure**: Provide concrete implementations
4. **Maintain SRP**: Each file should have one clear responsibility
5. **Update Facade**: Maintain backward compatibility

## References

- **Hexagonal Architecture**: https://alistair.cockburn.us/hexagonal-architecture/
- **Domain-Driven Design**: Eric Evans
- **Clean Architecture**: Robert C. Martin

---

**Refactored with ❤️ following Clean Architecture principles**

**Achievement**: Reduced from 1 monolithic 800-line file to 18 focused, maintainable components!
