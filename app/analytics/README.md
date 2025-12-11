# User Analytics & Business Metrics Service

World-class analytics service for tracking user behavior, engagement, conversions, and business metrics.

## Architecture

```
app/analytics/
├── facade.py                      # UserAnalyticsMetricsService (main interface)
├── domain/                        # Business entities and contracts
│   ├── models.py                  # 10 dataclasses (UserEvent, Metrics, etc.)
│   ├── enums.py                   # EventType, UserSegment, ABTestVariant
│   └── ports.py                   # 6 storage protocols
├── application/                   # Use cases
│   ├── event_tracker.py           # Event tracking logic
│   ├── session_manager.py         # Session management
│   ├── metrics_calculator.py      # Metrics calculation
│   ├── ab_test_manager.py         # A/B testing
│   ├── nps_manager.py             # NPS scoring
│   └── user_segmentation.py       # User segmentation
└── infrastructure/                # Storage implementations
    └── in_memory_stores.py        # 6 in-memory stores
```

## Features

✅ **Event Tracking**: Track any user interaction (page views, clicks, conversions)  
✅ **Session Management**: Start/end sessions with duration tracking  
✅ **Engagement Metrics**: DAU, WAU, MAU, bounce rate, return rate  
✅ **Conversion Tracking**: Conversion rate, time to convert, funnel analysis  
✅ **Retention Analysis**: Day 1/7/30 retention, churn rate, lifetime  
✅ **NPS Scoring**: Net Promoter Score with promoters/detractors breakdown  
✅ **A/B Testing**: Create tests, assign variants, track conversions  
✅ **User Segmentation**: NEW, ACTIVE, POWER, AT_RISK, CHURNED  

## Quick Start

```python
from app.analytics import get_user_analytics_service, EventType

# Get service instance
analytics = get_user_analytics_service()

# Track events
session_id = analytics.start_session(user_id=123, device_type="web")
analytics.track_event(
    user_id=123,
    event_type=EventType.PAGE_VIEW,
    event_name="homepage_view",
    session_id=session_id,
    page_url="/",
)

# Get metrics
engagement = analytics.get_engagement_metrics()
print(f"DAU: {engagement.dau}, MAU: {engagement.mau}")

conversion = analytics.get_conversion_metrics()
print(f"Conversion Rate: {conversion.conversion_rate:.2%}")

retention = analytics.get_retention_metrics()
print(f"Day 7 Retention: {retention.day_7_retention:.2%}")
```

## Event Tracking

```python
# Track different event types
analytics.track_event(
    user_id=123,
    event_type=EventType.CLICK,
    event_name="cta_button_click",
    properties={"button_text": "Sign Up", "location": "header"},
)

analytics.track_event(
    user_id=123,
    event_type=EventType.CONVERSION,
    event_name="signup_complete",
    properties={"plan": "premium", "value": 99.99},
)
```

## A/B Testing

```python
# Create A/B test
test_id = analytics.create_ab_test(
    test_name="Homepage CTA Test",
    variants=["control", "variant_a", "variant_b"],
    traffic_split={"control": 0.33, "variant_a": 0.33, "variant_b": 0.34},
)

# Assign user to variant
variant = analytics.assign_variant(test_id, user_id=123)

# Record conversion
analytics.record_ab_conversion(test_id, user_id=123)

# Get results
results = analytics.get_ab_test_results(test_id)
print(f"Winner: {results.winner}, Improvement: {results.improvement_percent:.1f}%")
```

## NPS Tracking

```python
# Record NPS response
analytics.record_nps_response(user_id=123, score=9, comment="Great product!")

# Get NPS metrics
nps = analytics.get_nps_metrics()
print(f"NPS Score: {nps.nps_score:.1f}")
print(f"Promoters: {nps.promoters_percent:.1f}%")
```

## User Segmentation

```python
# Segment users
segments = analytics.segment_users()

print(f"New Users: {len(segments[UserSegment.NEW])}")
print(f"Power Users: {len(segments[UserSegment.POWER])}")
print(f"At Risk: {len(segments[UserSegment.AT_RISK])}")
```

## Export Summary

```python
# Get comprehensive metrics summary
summary = analytics.export_metrics_summary()
print(summary)
```

## Design Patterns

- **Hexagonal Architecture**: Domain, Application, Infrastructure layers
- **Ports & Adapters**: Protocol-based interfaces for storage
- **Facade Pattern**: Simple interface hiding complexity
- **Dependency Injection**: Services receive dependencies
- **Single Responsibility**: Each service has one job

## Benefits

1. **Separation of Concerns**: Each layer has clear responsibility
2. **Testability**: Easy to mock stores and test logic
3. **Extensibility**: Add new metrics without changing existing code
4. **Maintainability**: Small, focused files (50-200 lines each)
5. **Type Safety**: Full type hints throughout

## Migration from Legacy

The facade maintains 100% backward compatibility:

```python
# Old import (still works)
from app.services.user_analytics_metrics_service import (
    UserAnalyticsMetricsService,
    get_user_analytics_service,
)

# New import (recommended)
from app.analytics import UserAnalyticsMetricsService, get_user_analytics_service
```

## Testing

```python
# Easy to test with mock stores
from app.analytics.application import EventTracker
from app.analytics.infrastructure import InMemoryEventStore

event_store = InMemoryEventStore()
session_store = InMemorySessionStore()
user_store = InMemoryUserStore()
active_users_store = InMemoryActiveUsersStore()

tracker = EventTracker(event_store, session_store, user_store, active_users_store)

# Test event tracking
event_id = tracker.track_event(
    user_id=1,
    event_type=EventType.PAGE_VIEW,
    event_name="test_event",
)

assert len(event_store.get_events()) == 1
```

## Performance

- **In-Memory Storage**: Fast access for real-time analytics
- **Thread-Safe**: RLock protection for concurrent access
- **Bounded Buffers**: deque with maxlen prevents memory leaks
- **Efficient Queries**: Optimized for common access patterns

## Future Enhancements

- [ ] Persistent storage adapters (PostgreSQL, Redis)
- [ ] Real-time streaming analytics
- [ ] Advanced funnel analysis
- [ ] Cohort analysis implementation
- [ ] Revenue metrics tracking
- [ ] Custom event definitions
- [ ] Data export to analytics platforms

---

**Refactored from**: `app/services/user_analytics_metrics_service.py` (800 lines)  
**Result**: 13 focused files, ~150 line facade, clean architecture
