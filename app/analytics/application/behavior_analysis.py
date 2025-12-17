"""User behavior analysis use case - Single Responsibility Principle."""

import statistics
from collections import Counter

from app.analytics.domain.entities import BehaviorProfile, UsageMetric
from app.analytics.domain.interfaces import MetricsRepository
from app.analytics.domain.value_objects import BehaviorPattern


class UserBehaviorAnalyzer:
    """User behavior analyzer - SRP: Only analyzes user behavior."""

    def __init__(self, repository: MetricsRepository):
        self.repository = repository

    def analyze(self, user_id: str) -> BehaviorProfile:
        """Analyze user behavior."""
        metrics = self.repository.get_by_user(user_id)

        if not metrics:
            return self._create_empty_profile(user_id)

        return BehaviorProfile(
            user_id=user_id,
            pattern=self._identify_pattern(metrics),
            avg_requests_per_day=self._calculate_avg_requests_per_day(metrics),
            avg_session_duration=self._calculate_avg_session_duration(metrics),
            favorite_endpoints=self._extract_favorite_endpoints(metrics),
            peak_usage_hours=self._extract_peak_hours(metrics),
            churn_probability=self._calculate_churn_probability(metrics),
        )

    def _identify_pattern(self, metrics: list[UsageMetric]) -> BehaviorPattern:
        """Identify behavior pattern - Complexity < 10."""
        if not metrics:
            return BehaviorPattern.CASUAL_USER

        avg_per_day = self._calculate_avg_requests_per_day(metrics)

        if avg_per_day > 20:
            return BehaviorPattern.POWER_USER
        elif avg_per_day > 10:
            return BehaviorPattern.GROWING
        elif avg_per_day < 2:
            return BehaviorPattern.CHURNING
        else:
            return BehaviorPattern.CASUAL_USER

    def _calculate_avg_requests_per_day(self, metrics: list[UsageMetric]) -> float:
        """Calculate average requests per day - Complexity < 10."""
        if not metrics:
            return 0.0

        first_date = min(m.timestamp for m in metrics)
        last_date = max(m.timestamp for m in metrics)
        days = max((last_date - first_date).days, 1)

        return len(metrics) / days

    def _calculate_avg_session_duration(self, metrics: list[UsageMetric]) -> float:
        """Calculate average session duration - Complexity < 10."""
        if len(metrics) < 2:
            return 0.0

        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        durations = []

        for i in range(len(sorted_metrics) - 1):
            time_diff = (sorted_metrics[i + 1].timestamp - sorted_metrics[i].timestamp).total_seconds()
            if time_diff < 3600:
                durations.append(time_diff)

        return statistics.mean(durations) if durations else 0.0

    def _extract_favorite_endpoints(self, metrics: list[UsageMetric], limit: int = 5) -> list[str]:
        """Extract favorite endpoints - Complexity < 10."""
        endpoint_counts = Counter(m.endpoint for m in metrics if m.endpoint)
        return [endpoint for endpoint, _ in endpoint_counts.most_common(limit)]

    def _extract_peak_hours(self, metrics: list[UsageMetric]) -> list[int]:
        """Extract peak usage hours - Complexity < 10."""
        hour_counts = Counter(m.timestamp.hour for m in metrics)
        avg_count = statistics.mean(hour_counts.values()) if hour_counts else 0

        return sorted([hour for hour, count in hour_counts.items() if count > avg_count])

    def _calculate_churn_probability(self, metrics: list[UsageMetric]) -> float:
        """Calculate churn probability - Complexity < 10."""
        if not metrics:
            return 1.0

        last_activity = max(m.timestamp for m in metrics)
        days_since_last = (last_activity.now(last_activity.tzinfo) - last_activity).days

        if days_since_last > 30:
            return 0.9
        elif days_since_last > 14:
            return 0.6
        elif days_since_last > 7:
            return 0.3
        else:
            return 0.1

    def _create_empty_profile(self, user_id: str) -> BehaviorProfile:
        """Create empty profile for new users."""
        return BehaviorProfile(
            user_id=user_id,
            pattern=BehaviorPattern.CASUAL_USER,
            avg_requests_per_day=0.0,
            avg_session_duration=0.0,
            favorite_endpoints=[],
            peak_usage_hours=[],
            churn_probability=0.5,
        )
