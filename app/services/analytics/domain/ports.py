# app/services/analytics/domain/ports.py
"""
Analytics Domain Ports
=======================
Protocol definitions for analytics infrastructure adapters.

Following Hexagonal Architecture / Ports & Adapters pattern.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.services.analytics.domain.models import (
    ABTestVariant,
    EventType,
    UserEvent,
    UserSegment,
    UserSession,
)


# ======================================================================================
# EVENT REPOSITORY PORT
# ======================================================================================


class EventRepositoryPort(Protocol):
    """
    Port for event storage and retrieval.

    Implementations:
    - InMemoryEventRepository
    - PostgreSQLEventRepository
    - ClickHouseEventRepository
    """

    def store_event(self, event: UserEvent) -> None:
        """
        Store a user event.

        Args:
            event: UserEvent to store
        """
        ...

    def get_events(
        self,
        user_id: int | None = None,
        session_id: str | None = None,
        event_type: EventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[UserEvent]:
        """
        Retrieve events matching filters.

        Args:
            user_id: Filter by user ID
            session_id: Filter by session ID
            event_type: Filter by event type
            start_time: Filter events after this time
            end_time: Filter events before this time
            limit: Maximum number of events to return

        Returns:
            List of matching events
        """
        ...

    def count_events(
        self,
        user_id: int | None = None,
        event_type: EventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """
        Count events matching filters.

        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            start_time: Filter events after this time
            end_time: Filter events before this time

        Returns:
            Number of matching events
        """
        ...

    def delete_old_events(self, before: datetime) -> int:
        """
        Delete events older than specified time.

        Args:
            before: Delete events before this time

        Returns:
            Number of deleted events
        """
        ...


# ======================================================================================
# SESSION REPOSITORY PORT
# ======================================================================================


class SessionRepositoryPort(Protocol):
    """
    Port for session storage and retrieval.

    Implementations:
    - InMemorySessionRepository
    - RedisSessionRepository
    - PostgreSQLSessionRepository
    """

    def store_session(self, session: UserSession) -> None:
        """
        Store or update a user session.

        Args:
            session: UserSession to store
        """
        ...

    def get_session(self, session_id: str) -> UserSession | None:
        """
        Retrieve session by ID.

        Args:
            session_id: Session identifier

        Returns:
            UserSession if found, None otherwise
        """
        ...

    def get_user_sessions(
        self,
        user_id: int,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[UserSession]:
        """
        Retrieve all sessions for a user.

        Args:
            user_id: User identifier
            start_time: Filter sessions after this time
            end_time: Filter sessions before this time

        Returns:
            List of user sessions
        """
        ...

    def get_active_sessions(self, since: datetime | None = None) -> list[UserSession]:
        """
        Get all active sessions.

        Args:
            since: Only include sessions active since this time

        Returns:
            List of active sessions
        """
        ...


# ======================================================================================
# ANALYTICS AGGREGATOR PORT
# ======================================================================================


class AnalyticsAggregatorPort(Protocol):
    """
    Port for analytics calculations and aggregations.

    Implementations:
    - InMemoryAggregator
    - SparkAggregator
    - BigQueryAggregator
    """

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
            Dictionary with engagement metrics
        """
        ...

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
            Dictionary with conversion metrics
        """
        ...

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
            Dictionary with retention metrics
        """
        ...


# ======================================================================================
# USER SEGMENTATION PORT
# ======================================================================================


class UserSegmentationPort(Protocol):
    """
    Port for user segmentation and classification.

    Implementations:
    - RuleBasedSegmentation
    - MLSegmentation
    - BehavioralSegmentation
    """

    def classify_user(
        self,
        user_id: int,
        user_data: dict[str, Any],
    ) -> UserSegment:
        """
        Classify user into a segment.

        Args:
            user_id: User identifier
            user_data: User behavior data

        Returns:
            UserSegment classification
        """
        ...

    def get_segment_users(
        self,
        segment: UserSegment,
    ) -> list[int]:
        """
        Get all users in a segment.

        Args:
            segment: User segment

        Returns:
            List of user IDs in segment
        """
        ...

    def update_segmentation(self) -> dict[UserSegment, int]:
        """
        Update all user segments.

        Returns:
            Dictionary mapping segments to user counts
        """
        ...


# ======================================================================================
# AB TEST MANAGER PORT
# ======================================================================================


class ABTestManagerPort(Protocol):
    """
    Port for A/B testing management.

    Implementations:
    - SimpleABTestManager
    - BayesianABTestManager
    - MultivariateTester
    """

    def create_test(
        self,
        test_id: str,
        test_name: str,
        variants: list[ABTestVariant],
    ) -> None:
        """
        Create a new A/B test.

        Args:
            test_id: Test identifier
            test_name: Test name
            variants: List of test variants
        """
        ...

    def assign_variant(
        self,
        test_id: str,
        user_id: int,
    ) -> ABTestVariant:
        """
        Assign user to a test variant.

        Args:
            test_id: Test identifier
            user_id: User identifier

        Returns:
            Assigned variant
        """
        ...

    def record_conversion(
        self,
        test_id: str,
        user_id: int,
        variant: ABTestVariant,
    ) -> None:
        """
        Record conversion for test variant.

        Args:
            test_id: Test identifier
            user_id: User identifier
            variant: Test variant
        """
        ...

    def get_test_results(
        self,
        test_id: str,
    ) -> dict[str, Any]:
        """
        Get A/B test results.

        Args:
            test_id: Test identifier

        Returns:
            Dictionary with test results
        """
        ...


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    "EventRepositoryPort",
    "SessionRepositoryPort",
    "AnalyticsAggregatorPort",
    "UserSegmentationPort",
    "ABTestManagerPort",
]
