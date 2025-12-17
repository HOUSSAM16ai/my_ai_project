# app/services/analytics/application/conversion_analyzer.py
"""
Conversion Analyzer Service
============================
Single Responsibility: Analyze conversion metrics and funnels.
"""

from __future__ import annotations

import statistics
from typing import Any, Protocol

from app.services.analytics.domain.models import EventType, UserEvent


class EventRepository(Protocol):
    """Protocol for event storage"""
    def get_recent(self, days: int) -> list[UserEvent]: ...
    def get_by_type(self, event_type: EventType) -> list[UserEvent]: ...
    def get_by_user(self, user_id: int, days: int) -> list[UserEvent]: ...


class ConversionAnalyzer:
    """
    Conversion metrics analyzer.

    Responsibilities:
    - Calculate conversion rates
    - Funnel analysis
    - Time to convert
    """

    def __init__(self, event_repository: EventRepository):
        self._event_repo = event_repository

    def get_conversion_metrics(
        self,
        conversion_event: str = "conversion",
        days: int = 30,
    ) -> dict[str, Any]:
        """Calculate conversion metrics"""
        recent_events = self._event_repo.get_recent(days)

        if not recent_events:
            return self._empty_metrics()

        # Filter conversion events
        conversions = [e for e in recent_events if e.event_name == conversion_event]

        # Calculate unique visitors and converters
        unique_visitors = len({e.user_id for e in recent_events})
        unique_converters = len({e.user_id for e in conversions})

        conversion_rate = unique_converters / unique_visitors if unique_visitors > 0 else 0.0

        # Calculate average time to convert
        avg_time_to_convert = self._calculate_time_to_convert(recent_events, conversion_event)

        # Calculate conversion value
        conversion_value = sum(e.properties.get("value", 0.0) for e in conversions)

        return {
            "conversion_rate": conversion_rate,
            "total_conversions": len(conversions),
            "total_visitors": unique_visitors,
            "unique_converters": unique_converters,
            "avg_time_to_convert": avg_time_to_convert,
            "conversion_value": conversion_value,
            "funnel_completion_rate": conversion_rate,
            "drop_off_points": {},  # Placeholder for funnel analysis
        }

    def _calculate_time_to_convert(
        self,
        events: list[UserEvent],
        conversion_event: str,
    ) -> float:
        """Calculate average time to convert"""
        user_first_event = {}
        user_conversion_time = {}

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        for event in sorted_events:
            # Track first event per user
            if event.user_id not in user_first_event:
                user_first_event[event.user_id] = event.timestamp

            # Track conversion time
            if event.event_name == conversion_event and event.user_id not in user_conversion_time:
                user_conversion_time[event.user_id] = event.timestamp

        # Calculate time differences
        conversion_times = []
        for user_id, conversion_time in user_conversion_time.items():
            if user_id in user_first_event:
                time_diff = (conversion_time - user_first_event[user_id]).total_seconds()
                conversion_times.append(time_diff)

        return statistics.mean(conversion_times) if conversion_times else 0.0

    def _empty_metrics(self) -> dict[str, Any]:
        """Return empty metrics"""
        return {
            "conversion_rate": 0.0,
            "total_conversions": 0,
            "total_visitors": 0,
            "unique_converters": 0,
            "avg_time_to_convert": 0.0,
            "conversion_value": 0.0,
            "funnel_completion_rate": 0.0,
            "drop_off_points": {},
        }
