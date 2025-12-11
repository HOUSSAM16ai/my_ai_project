# app/services/analytics/facade.py
"""
Analytics Service Facade
=========================
Backward-compatible facade for user analytics service.

Maintains 100% API compatibility with original UserAnalyticsMetricsService
while delegating to new layered architecture.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any

from app.services.analytics.application.engagement_analyzer import EngagementAnalyzer
from app.services.analytics.application.event_tracker import EventTracker
from app.services.analytics.domain.models import EventType, UserSegment
from app.services.analytics.infrastructure.in_memory_repository import (
    InMemoryEventRepository,
    InMemorySessionRepository,
)

_LOG = logging.getLogger(__name__)


# ======================================================================================
# FACADE CLASS
# ======================================================================================


class UserAnalyticsMetricsService:
    """
    User analytics & metrics service facade.
    
    Backward-compatible interface that delegates to layered architecture:
    - EventTracker for event tracking
    - EngagementAnalyzer for engagement metrics
    - ConversionAnalyzer for conversion metrics (to be added)
    - RetentionAnalyzer for retention metrics (to be added)
    """

    def __init__(self):
        """Initialize analytics service with layered components."""
        # Infrastructure layer
        self._event_repo = InMemoryEventRepository(max_events=100000)
        self._session_repo = InMemorySessionRepository()
        
        # Application layer
        self._event_tracker = EventTracker(
            event_repository=self._event_repo,
            session_repository=self._session_repo,
        )
        self._engagement_analyzer = EngagementAnalyzer(
            event_repository=self._event_repo,
            session_repository=self._session_repo,
        )
        
        # Legacy compatibility - maintain original structure
        self.lock = threading.RLock()
        self.active_users_1d: set[int] = set()
        self.active_users_7d: set[int] = set()
        self.active_users_30d: set[int] = set()

    def track_event(
        self,
        user_id: int,
        event_type: EventType,
        event_name: str,
        session_id: str | None = None,
        properties: dict[str, Any] | None = None,
        page_url: str | None = None,
        device_type: str | None = None,
    ) -> str:
        """
        Track a user event.
        
        Delegates to EventTracker and updates legacy tracking sets.
        """
        # Update legacy active user sets
        with self.lock:
            self.active_users_1d.add(user_id)
            self.active_users_7d.add(user_id)
            self.active_users_30d.add(user_id)
        
        # Delegate to event tracker
        return self._event_tracker.track_event(
            user_id=user_id,
            event_type=event_type,
            event_name=event_name,
            session_id=session_id,
            properties=properties,
            page_url=page_url,
            device_type=device_type,
        )

    def track_page_view(
        self,
        user_id: int,
        page_url: str,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Track page view event."""
        return self._event_tracker.track_page_view(
            user_id=user_id,
            page_url=page_url,
            session_id=session_id,
            **kwargs,
        )

    def track_conversion(
        self,
        user_id: int,
        conversion_name: str,
        session_id: str | None = None,
        value: float | None = None,
        **kwargs: Any,
    ) -> str:
        """Track conversion event."""
        return self._event_tracker.track_conversion(
            user_id=user_id,
            conversion_name=conversion_name,
            session_id=session_id,
            value=value,
            **kwargs,
        )

    def get_engagement_metrics(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get engagement metrics.
        
        Returns dictionary for backward compatibility.
        """
        metrics = self._engagement_analyzer.calculate_engagement_metrics(
            start_time=start_time,
            end_time=end_time,
        )
        
        return {
            "dau": metrics.dau,
            "wau": metrics.wau,
            "mau": metrics.mau,
            "stickiness": metrics.stickiness,
            "avg_session_duration": metrics.avg_session_duration,
            "avg_events_per_session": metrics.avg_events_per_session,
            "bounce_rate": metrics.bounce_rate,
            "return_rate": metrics.return_rate,
        }

    def get_active_users_count(self, period: str = "1d") -> int:
        """
        Get active users count for period.
        
        Args:
            period: Time period ("1d", "7d", "30d")
            
        Returns:
            Number of active users
        """
        days_map = {
            "1d": 1,
            "7d": 7,
            "30d": 30,
        }
        days = days_map.get(period, 1)
        
        return self._engagement_analyzer.get_active_users_count(days=days)

    def get_user_engagement_score(
        self,
        user_id: int,
        days: int = 30,
    ) -> float:
        """Get engagement score for a user."""
        return self._engagement_analyzer.get_user_engagement_score(
            user_id=user_id,
            days=days,
        )

    # Legacy compatibility methods
    def segment_user(self, user_id: int) -> UserSegment:
        """
        Segment a user based on their behavior.
        
        Simple rule-based segmentation for now.
        """
        score = self.get_user_engagement_score(user_id, days=30)
        
        if score >= 80:
            return UserSegment.POWER
        elif score >= 50:
            return UserSegment.ACTIVE
        elif score >= 20:
            return UserSegment.AT_RISK
        elif score > 0:
            return UserSegment.CHURNED
        else:
            return UserSegment.NEW

    def get_health_status(self) -> dict[str, Any]:
        """Get service health status."""
        try:
            metrics = self.get_engagement_metrics()
            
            return {
                "status": "healthy",
                "dau": metrics["dau"],
                "mau": metrics["mau"],
                "stickiness": metrics["stickiness"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            _LOG.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# ======================================================================================
# SINGLETON FACTORY
# ======================================================================================

_SERVICE_INSTANCE: UserAnalyticsMetricsService | None = None
_SERVICE_LOCK = threading.Lock()


def get_user_analytics_service() -> UserAnalyticsMetricsService:
    """
    Get or create analytics service singleton.
    
    Returns:
        UserAnalyticsMetricsService instance
    """
    global _SERVICE_INSTANCE
    
    if _SERVICE_INSTANCE is not None:
        return _SERVICE_INSTANCE
    
    with _SERVICE_LOCK:
        if _SERVICE_INSTANCE is not None:
            return _SERVICE_INSTANCE
        
        _SERVICE_INSTANCE = UserAnalyticsMetricsService()
        _LOG.info("Analytics service initialized with layered architecture")
        return _SERVICE_INSTANCE


def reset_analytics_service() -> None:
    """Reset service singleton (for testing)."""
    global _SERVICE_INSTANCE
    with _SERVICE_LOCK:
        _SERVICE_INSTANCE = None


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    "UserAnalyticsMetricsService",
    "get_user_analytics_service",
    "reset_analytics_service",
]
