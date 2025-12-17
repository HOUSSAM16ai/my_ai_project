"""
API Advanced Analytics - Backward Compatible Facade
===================================================
Thin facade that maintains 100% backward compatibility
while delegating to the new hexagonal architecture.

This allows existing code to continue working without changes.
"""

from datetime import datetime
from typing import Any

from .application import AnalyticsManager
from .domain import BehaviorProfile, TimeGranularity
from .infrastructure import (
    InMemoryBehaviorRepository,
    InMemoryJourneyRepository,
    InMemoryMetricsRepository,
    InMemoryReportRepository,
)


class AdvancedAnalyticsService:
    """
    Backward-compatible facade for Advanced Analytics Service.

    Maintains the same API as the original monolithic service
    but delegates to the new hexagonal architecture.

    This is a thin shim (facade pattern) that ensures zero breaking changes.
    """

    def __init__(self):
        # Initialize repositories
        metrics_repo = InMemoryMetricsRepository()
        journey_repo = InMemoryJourneyRepository()
        behavior_repo = InMemoryBehaviorRepository()
        report_repo = InMemoryReportRepository()

        # Initialize manager with dependencies
        self._manager = AnalyticsManager(
            metrics_repo=metrics_repo,
            journey_repo=journey_repo,
            behavior_repo=behavior_repo,
            report_repo=report_repo,
        )

    def track_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Track API request - delegates to manager."""
        return self._manager.track_request(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata,
        )

    def get_realtime_dashboard(self) -> dict[str, Any]:
        """Get real-time dashboard data - delegates to manager."""
        return self._manager.get_realtime_dashboard()

    def analyze_user_behavior(self, user_id: str) -> BehaviorProfile:
        """Analyze user behavior - delegates to manager."""
        return self._manager.analyze_user_behavior(user_id)

    def generate_usage_report(
        self,
        name: str,
        start_time: datetime,
        end_time: datetime,
        granularity: TimeGranularity = TimeGranularity.HOUR,
    ):
        """Generate usage report - delegates to manager."""
        return self._manager.generate_usage_report(
            name=name,
            start_time=start_time,
            end_time=end_time,
            granularity=granularity,
        )

    def detect_anomalies(self, window_hours: int = 24) -> list[dict[str, Any]]:
        """Detect anomalies - delegates to manager."""
        return self._manager.detect_anomalies(window_hours=window_hours)

    def get_cost_optimization_insights(self) -> dict[str, Any]:
        """Get cost optimization insights - delegates to manager."""
        return self._manager.get_cost_optimization_insights()


# Singleton instance for backward compatibility
_service_instance: AdvancedAnalyticsService | None = None


def get_advanced_analytics_service() -> AdvancedAnalyticsService:
    """
    Get singleton instance of Advanced Analytics Service.

    Maintains backward compatibility with the original factory function.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = AdvancedAnalyticsService()
    return _service_instance
