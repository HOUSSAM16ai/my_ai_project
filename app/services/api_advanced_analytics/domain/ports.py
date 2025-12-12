"""
API Advanced Analytics - Domain Ports
======================================
Repository and service interfaces (dependency inversion).

Defines contracts without implementations.
"""

from datetime import datetime
from typing import Protocol

from .models import AnalyticsReport, BehaviorProfile, TimeGranularity, UsageMetric, UserJourney


class MetricsRepositoryPort(Protocol):
    """Interface for metrics storage and retrieval."""

    def save_metric(self, metric: UsageMetric) -> None:
        """Save a usage metric."""
        ...

    def get_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        endpoint: str | None = None,
        user_id: str | None = None,
    ) -> list[UsageMetric]:
        """Retrieve metrics within time range with optional filters."""
        ...

    def get_aggregated_metrics(
        self, start_time: datetime, end_time: datetime, granularity: TimeGranularity
    ) -> dict[str, float]:
        """Get aggregated metrics for a time range."""
        ...


class JourneyRepositoryPort(Protocol):
    """Interface for user journey storage."""

    def save_journey(self, journey: UserJourney) -> None:
        """Save a user journey."""
        ...

    def get_journey(self, session_id: str) -> UserJourney | None:
        """Retrieve a journey by session ID."""
        ...

    def get_user_journeys(self, user_id: str, limit: int = 10) -> list[UserJourney]:
        """Get recent journeys for a user."""
        ...


class BehaviorRepositoryPort(Protocol):
    """Interface for behavior profile storage."""

    def save_profile(self, profile: BehaviorProfile) -> None:
        """Save a behavior profile."""
        ...

    def get_profile(self, user_id: str) -> BehaviorProfile | None:
        """Retrieve a user's behavior profile."""
        ...

    def get_all_profiles(self) -> list[BehaviorProfile]:
        """Get all behavior profiles."""
        ...


class ReportRepositoryPort(Protocol):
    """Interface for analytics report storage."""

    def save_report(self, report: AnalyticsReport) -> None:
        """Save an analytics report."""
        ...

    def get_report(self, report_id: str) -> AnalyticsReport | None:
        """Retrieve a report by ID."""
        ...

    def get_recent_reports(self, limit: int = 10) -> list[AnalyticsReport]:
        """Get recently generated reports."""
        ...
