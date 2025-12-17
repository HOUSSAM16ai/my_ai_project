# app/services/analytics/application/engagement_analyzer.py
"""
Engagement Analyzer Service
============================
Application service for analyzing user engagement metrics.

Calculates DAU, WAU, MAU, session metrics, and engagement scores.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.services.analytics.domain.models import EngagementMetrics
from app.services.analytics.domain.ports import EventRepositoryPort, SessionRepositoryPort

_LOG = logging.getLogger(__name__)


# ======================================================================================
# ENGAGEMENT ANALYZER SERVICE
# ======================================================================================


class EngagementAnalyzer:
    """
    Engagement analysis service.

    Responsibilities:
    - Calculate DAU/WAU/MAU metrics
    - Analyze session duration and frequency
    - Calculate bounce rates
    - Measure user stickiness
    """

    def __init__(
        self,
        event_repository: EventRepositoryPort,
        session_repository: SessionRepositoryPort,
    ):
        """
        Initialize engagement analyzer.

        Args:
            event_repository: Event storage repository
            session_repository: Session storage repository
        """
        self._event_repo = event_repository
        self._session_repo = session_repository

    def calculate_engagement_metrics(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> EngagementMetrics:
        """
        Calculate comprehensive engagement metrics.

        Args:
            start_time: Start of analysis period (defaults to 30 days ago)
            end_time: End of analysis period (defaults to now)

        Returns:
            EngagementMetrics value object
        """
        if end_time is None:
            end_time = datetime.utcnow()
        if start_time is None:
            start_time = end_time - timedelta(days=30)

        # Calculate active users
        dau = self._calculate_dau(end_time)
        wau = self._calculate_wau(end_time)
        mau = self._calculate_mau(end_time)

        # Calculate session metrics
        avg_session_duration = self._calculate_avg_session_duration(start_time, end_time)
        avg_events_per_session = self._calculate_avg_events_per_session(start_time, end_time)

        # Calculate rates
        bounce_rate = self._calculate_bounce_rate(start_time, end_time)
        return_rate = self._calculate_return_rate(start_time, end_time)

        return EngagementMetrics(
            dau=dau,
            wau=wau,
            mau=mau,
            avg_session_duration=avg_session_duration,
            avg_events_per_session=avg_events_per_session,
            bounce_rate=bounce_rate,
            return_rate=return_rate,
        )

    def get_active_users_count(self, days: int = 1) -> int:
        """
        Get count of active users in last N days.

        Args:
            days: Number of days to look back

        Returns:
            Number of unique active users
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        events = self._event_repo.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=float('inf'),  # type: ignore
        )

        unique_users = set(event.user_id for event in events)
        return len(unique_users)

    def get_user_engagement_score(
        self,
        user_id: int,
        days: int = 30,
    ) -> float:
        """
        Calculate engagement score for a user.

        Engagement score is a composite metric based on:
        - Visit frequency
        - Session duration
        - Feature usage
        - Recency of activity

        Args:
            user_id: User identifier
            days: Number of days to analyze

        Returns:
            Engagement score (0-100)
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)

        # Get user events
        events = self._event_repo.get_events(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=float('inf'),  # type: ignore
        )

        if not events:
            return 0.0

        # Get user sessions
        sessions = self._session_repo.get_user_sessions(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )

        # Calculate components
        frequency_score = min(len(sessions) / days * 100, 30)  # Max 30 points
        duration_score = min(
            sum(s.duration_seconds for s in sessions) / (days * 3600) * 100,
            30  # Max 30 points
        )
        activity_score = min(len(events) / (days * 10) * 100, 30)  # Max 30 points

        # Recency bonus (last 7 days)
        recent_events = [e for e in events if e.timestamp > end_time - timedelta(days=7)]
        recency_score = min(len(recent_events) / 10 * 10, 10)  # Max 10 points

        total_score = frequency_score + duration_score + activity_score + recency_score
        return min(total_score, 100.0)

    def _calculate_dau(self, date: datetime) -> int:
        """Calculate Daily Active Users."""
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)

        events = self._event_repo.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=float('inf'),  # type: ignore
        )

        return len(set(event.user_id for event in events))

    def _calculate_wau(self, date: datetime) -> int:
        """Calculate Weekly Active Users."""
        end_time = date
        start_time = end_time - timedelta(days=7)

        events = self._event_repo.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=float('inf'),  # type: ignore
        )

        return len(set(event.user_id for event in events))

    def _calculate_mau(self, date: datetime) -> int:
        """Calculate Monthly Active Users."""
        end_time = date
        start_time = end_time - timedelta(days=30)

        events = self._event_repo.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=float('inf'),  # type: ignore
        )

        return len(set(event.user_id for event in events))

    def _calculate_avg_session_duration(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Calculate average session duration in seconds."""
        sessions = self._session_repo.get_active_sessions(since=start_time)

        if not sessions:
            return 0.0

        total_duration = sum(s.duration_seconds for s in sessions)
        return total_duration / len(sessions)

    def _calculate_avg_events_per_session(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Calculate average events per session."""
        sessions = self._session_repo.get_active_sessions(since=start_time)

        if not sessions:
            return 0.0

        total_events = sum(s.events for s in sessions)
        return total_events / len(sessions)

    def _calculate_bounce_rate(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Calculate bounce rate (sessions with 1 or fewer page views)."""
        sessions = self._session_repo.get_active_sessions(since=start_time)

        if not sessions:
            return 0.0

        bounced_sessions = sum(1 for s in sessions if s.is_bounce)
        return bounced_sessions / len(sessions)

    def _calculate_return_rate(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Calculate return rate (users with multiple sessions)."""
        sessions = self._session_repo.get_active_sessions(since=start_time)

        if not sessions:
            return 0.0

        # Count sessions per user
        user_sessions: dict[int, int] = {}
        for session in sessions:
            user_sessions[session.user_id] = user_sessions.get(session.user_id, 0) + 1

        # Count users with multiple sessions
        returning_users = sum(1 for count in user_sessions.values() if count > 1)
        total_users = len(user_sessions)

        return returning_users / total_users if total_users > 0 else 0.0


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = ["EngagementAnalyzer"]
