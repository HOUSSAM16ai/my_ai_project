"""
API Advanced Analytics - Infrastructure Repositories
====================================================
Repository implementations for data persistence.

In-memory implementations that can be easily replaced with
database-backed implementations.
"""

from collections import defaultdict
from datetime import datetime

from ..domain import (
    AnalyticsReport,
    BehaviorProfile,
    TimeGranularity,
    UsageMetric,
    UserJourney,
)


class InMemoryMetricsRepository:
    """In-memory metrics storage implementation."""

    def __init__(self):
        self._metrics: list[UsageMetric] = []

    def save_metric(self, metric: UsageMetric) -> None:
        """Save a usage metric."""
        self._metrics.append(metric)

    def get_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        endpoint: str | None = None,
        user_id: str | None = None,
    ) -> list[UsageMetric]:
        """Retrieve metrics within time range with optional filters."""
        filtered = [
            m
            for m in self._metrics
            if start_time <= m.timestamp <= end_time
        ]

        if endpoint:
            filtered = [m for m in filtered if m.endpoint == endpoint]

        if user_id:
            filtered = [m for m in filtered if m.user_id == user_id]

        return filtered

    def get_aggregated_metrics(
        self, start_time: datetime, end_time: datetime, granularity: TimeGranularity
    ) -> dict[str, float]:
        """Get aggregated metrics for a time range."""
        metrics = self.get_metrics(start_time, end_time)

        return {
            "total_count": float(len(metrics)),
            "request_count": float(len([m for m in metrics if m.name == "api_request"])),
            "unique_endpoints": float(len(set(m.endpoint for m in metrics if m.endpoint))),
        }


class InMemoryJourneyRepository:
    """In-memory user journey storage implementation."""

    def __init__(self):
        self._journeys: dict[str, UserJourney] = {}
        self._user_journeys: dict[str, list[str]] = defaultdict(list)

    def save_journey(self, journey: UserJourney) -> None:
        """Save a user journey."""
        self._journeys[journey.session_id] = journey

        if journey.session_id not in self._user_journeys[journey.user_id]:
            self._user_journeys[journey.user_id].append(journey.session_id)

    def get_journey(self, session_id: str) -> UserJourney | None:
        """Retrieve a journey by session ID."""
        return self._journeys.get(session_id)

    def get_user_journeys(self, user_id: str, limit: int = 10) -> list[UserJourney]:
        """Get recent journeys for a user."""
        session_ids = self._user_journeys.get(user_id, [])
        journeys = [
            self._journeys[sid]
            for sid in session_ids[-limit:]
            if sid in self._journeys
        ]
        return list(reversed(journeys))  # Most recent first


class InMemoryBehaviorRepository:
    """In-memory behavior profile storage implementation."""

    def __init__(self):
        self._profiles: dict[str, BehaviorProfile] = {}

    def save_profile(self, profile: BehaviorProfile) -> None:
        """Save a behavior profile."""
        self._profiles[profile.user_id] = profile

    def get_profile(self, user_id: str) -> BehaviorProfile | None:
        """Retrieve a user's behavior profile."""
        return self._profiles.get(user_id)

    def get_all_profiles(self) -> list[BehaviorProfile]:
        """Get all behavior profiles."""
        return list(self._profiles.values())


class InMemoryReportRepository:
    """In-memory analytics report storage implementation."""

    def __init__(self):
        self._reports: dict[str, AnalyticsReport] = {}
        self._report_order: list[str] = []

    def save_report(self, report: AnalyticsReport) -> None:
        """Save an analytics report."""
        if report.report_id not in self._reports:
            self._report_order.append(report.report_id)
        self._reports[report.report_id] = report

    def get_report(self, report_id: str) -> AnalyticsReport | None:
        """Retrieve a report by ID."""
        return self._reports.get(report_id)

    def get_recent_reports(self, limit: int = 10) -> list[AnalyticsReport]:
        """Get recently generated reports."""
        recent_ids = self._report_order[-limit:]
        return [
            self._reports[rid]
            for rid in reversed(recent_ids)
            if rid in self._reports
        ]
