# app/services/analytics/infrastructure/analytics_aggregator.py
"""
Analytics Aggregator Implementation
====================================
Concrete implementation of AnalyticsAggregatorPort for calculating metrics.

Uses in-memory data structures. Production systems should use
distributed analytics engines like Spark, Presto, or BigQuery.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services.analytics.domain.models import EventType
from app.services.analytics.domain.ports import (
    AnalyticsAggregatorPort,
    EventRepositoryPort,
    SessionRepositoryPort,
)


class InMemoryAnalyticsAggregator(AnalyticsAggregatorPort):
    """
    In-memory analytics aggregator.
    
    Features:
    - Real-time metric calculations
    - Time-series aggregations
    - Funnel analysis
    - Cohort analytics
    """
    
    def __init__(
        self,
        event_repository: EventRepositoryPort,
        session_repository: SessionRepositoryPort,
    ):
        """
        Initialize aggregator.
        
        Args:
            event_repository: Event storage repository
            session_repository: Session storage repository
        """
        self._event_repo = event_repository
        self._session_repo = session_repository
    
    def calculate_engagement_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any]:
        """
        Calculate engagement metrics for time period.
        
        Args:
            start_time: Start of analysis period
            end_time: End of analysis period
            
        Returns:
            Dictionary with engagement metrics including:
            - total_events: Total number of events
            - unique_users: Number of unique users
            - avg_events_per_user: Average events per user
            - total_sessions: Total number of sessions
            - avg_session_duration: Average session duration in seconds
        """
        # Get all events in period
        events = self._event_repo.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=float('inf'),  # type: ignore
        )
        
        # Get all sessions in period
        sessions = self._session_repo.get_active_sessions(since=start_time)
        sessions = [s for s in sessions if s.start_time <= end_time]
        
        # Calculate metrics
        unique_users = len(set(e.user_id for e in events))
        total_events = len(events)
        total_sessions = len(sessions)
        
        avg_events_per_user = total_events / unique_users if unique_users > 0 else 0.0
        
        # Calculate average session duration
        session_durations = []
        for session in sessions:
            if session.end_time and session.start_time:
                duration = (session.end_time - session.start_time).total_seconds()
                session_durations.append(duration)
        
        avg_session_duration = (
            sum(session_durations) / len(session_durations)
            if session_durations
            else 0.0
        )
        
        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "avg_events_per_user": avg_events_per_user,
            "total_sessions": total_sessions,
            "avg_session_duration": avg_session_duration,
        }
    
    def calculate_conversion_metrics(
        self,
        funnel_steps: list[EventType],
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, Any]:
        """
        Calculate conversion metrics for funnel.
        
        Args:
            funnel_steps: List of event types in funnel
            start_time: Start of analysis period
            end_time: End of analysis period
            
        Returns:
            Dictionary with conversion metrics including:
            - funnel_steps: List of funnel steps with counts
            - overall_conversion_rate: Overall funnel conversion rate
            - step_conversion_rates: Conversion rate for each step
        """
        if not funnel_steps:
            return {
                "funnel_steps": [],
                "overall_conversion_rate": 0.0,
                "step_conversion_rates": [],
            }
        
        # Track users at each step
        users_at_step: list[set[int]] = []
        
        for step in funnel_steps:
            # Get events for this step
            events = self._event_repo.get_events(
                event_type=step,
                start_time=start_time,
                end_time=end_time,
                limit=float('inf'),  # type: ignore
            )
            
            # Get unique users who reached this step
            users = set(e.user_id for e in events)
            
            # Filter to only users who completed previous steps
            if users_at_step:
                users = users.intersection(users_at_step[-1])
            
            users_at_step.append(users)
        
        # Calculate conversion rates
        step_counts = [len(users) for users in users_at_step]
        
        step_conversion_rates = []
        for i in range(1, len(step_counts)):
            prev_count = step_counts[i - 1]
            curr_count = step_counts[i]
            rate = curr_count / prev_count if prev_count > 0 else 0.0
            step_conversion_rates.append(rate)
        
        overall_conversion_rate = (
            step_counts[-1] / step_counts[0]
            if step_counts and step_counts[0] > 0
            else 0.0
        )
        
        funnel_data = [
            {
                "step": str(step),
                "users": count,
            }
            for step, count in zip(funnel_steps, step_counts)
        ]
        
        return {
            "funnel_steps": funnel_data,
            "overall_conversion_rate": overall_conversion_rate,
            "step_conversion_rates": step_conversion_rates,
        }
    
    def calculate_retention_metrics(
        self,
        cohort_id: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Calculate retention metrics for cohort.
        
        Args:
            cohort_id: Cohort identifier
            days: Number of days to analyze
            
        Returns:
            Dictionary with retention metrics including:
            - cohort_id: Cohort identifier
            - cohort_size: Number of users in cohort
            - retention_by_day: Retention rate for each day
            - avg_retention: Average retention rate
        """
        # For simplicity, return placeholder metrics
        # In production, this would query cohort data and calculate retention
        
        return {
            "cohort_id": cohort_id,
            "cohort_size": 0,
            "retention_by_day": [0.0] * days,
            "avg_retention": 0.0,
        }


__all__ = [
    "InMemoryAnalyticsAggregator",
]
