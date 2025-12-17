# app/services/analytics/application/retention_analyzer.py
"""
Retention Analyzer Service
===========================
Single Responsibility: Analyze user retention and churn.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Any, Protocol



class UserRepository(Protocol):
    """Protocol for user storage"""
    def get_all(self) -> dict[int, dict[str, Any]]: ...
    def get_active_users(self, days: int) -> set[int]: ...


class RetentionAnalyzer:
    """
    User retention analyzer.

    Responsibilities:
    - Calculate retention rates
    - Cohort analysis
    - Churn calculations
    """

    def __init__(self, user_repository: UserRepository):
        self._user_repo = user_repository

    def get_retention_metrics(
        self,
        cohort_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Calculate retention metrics"""
        if cohort_date is None:
            cohort_date = datetime.utcnow() - timedelta(days=30)

        users = self._user_repo.get_all()

        # Get cohort users (joined on cohort_date)
        cohort_users = [
            user_id
            for user_id, data in users.items()
            if data.get("first_seen") and data["first_seen"].date() == cohort_date.date()
        ]

        cohort_size = len(cohort_users)

        if cohort_size == 0:
            return self._empty_metrics()

        # Calculate retention for different periods
        now = datetime.utcnow()
        day_1_active = sum(
            1 for user_id in cohort_users
            if (now - users[user_id].get("last_seen", now)).days <= 1
        )
        day_7_active = sum(
            1 for user_id in cohort_users
            if (now - users[user_id].get("last_seen", now)).days <= 7
        )
        day_30_active = sum(
            1 for user_id in cohort_users
            if (now - users[user_id].get("last_seen", now)).days <= 30
        )

        day_1_retention = day_1_active / cohort_size
        day_7_retention = day_7_active / cohort_size
        day_30_retention = day_30_active / cohort_size

        # Calculate churn rate
        churn_rate = 1.0 - day_30_retention

        # Calculate average lifetime
        lifetimes = [
            (users[user_id].get("last_seen", now) - users[user_id].get("first_seen", now)).days
            for user_id in cohort_users
            if users[user_id].get("first_seen") and users[user_id].get("last_seen")
        ]
        avg_lifetime_days = statistics.mean(lifetimes) if lifetimes else 0.0

        return {
            "day_1_retention": day_1_retention,
            "day_7_retention": day_7_retention,
            "day_30_retention": day_30_retention,
            "cohort_size": cohort_size,
            "churn_rate": churn_rate,
            "avg_lifetime_days": avg_lifetime_days,
        }

    def _empty_metrics(self) -> dict[str, Any]:
        """Return empty metrics"""
        return {
            "day_1_retention": 0.0,
            "day_7_retention": 0.0,
            "day_30_retention": 0.0,
            "cohort_size": 0,
            "churn_rate": 0.0,
            "avg_lifetime_days": 0.0,
        }
