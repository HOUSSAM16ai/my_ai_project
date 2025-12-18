# Analytics Service

This module provides a unified interface for analytics, including:

*   **User Analytics:** Event tracking, sessions, user behavior analysis.
*   **Business Analytics:** A/B testing, NPS surveys, engagement metrics.
*   **System Analytics:** API latency, error rates, anomaly detection.

## Structure

The module follows a flattened Hexagonal Architecture to avoid circular imports:

*   `models.py` & `entities.py`: Domain data structures.
*   `ports.py` & `interfaces.py`: Abstract interfaces for dependencies.
*   `service.py`: The main facade (`UserAnalyticsMetricsService`) and factory.
*   `event_tracker.py`, `session_manager.py`, etc.: Application logic components.
*   `in_memory_stores.py`: Default persistence implementations.

## Usage

Use the factory function to get the singleton instance:

```python
from app.analytics import get_user_analytics_service

analytics = get_user_analytics_service()

# Track an event
analytics.track_event(
    user_id=123,
    event_type=EventType.CLICK,
    event_name="button_clicked",
    properties={"button_id": "signup"}
)

# A/B Testing
variant = analytics.assign_variant(test_id="landing_page_v1", user_id=123)

# NPS
analytics.submit_nps(user_id=123, score=9, feedback="Great service!")
```
