"""Analytics Facade - Unified interface following Facade Pattern."""

from datetime import UTC, datetime
from typing import Any

from app.analytics.application.anomaly_detection import StatisticalAnomalyDetector
from app.analytics.application.behavior_analysis import UserBehaviorAnalyzer
from app.analytics.application.report_generation import UsageReportGenerator
from app.analytics.domain.entities import Anomaly, BehaviorProfile, UsageMetric
from app.analytics.domain.interfaces import AnomalyDetector, MetricsRepository, ReportGenerator
from app.analytics.domain.value_objects import MetricType
from app.analytics.infrastructure.in_memory_repository import InMemoryMetricsRepository


class AnalyticsFacade:
    """
    Analytics Facade - Unified interface for all analytics operations.

    This class follows the Facade Pattern and Dependency Inversion Principle.
    All dependencies are injected through the constructor.
    """

    def __init__(
        self,
        repository: MetricsRepository,
        anomaly_detector: AnomalyDetector,
        report_generator: ReportGenerator,
        behavior_analyzer: UserBehaviorAnalyzer,
    ):
        self.repository = repository
        self.anomaly_detector = anomaly_detector
        self.report_generator = report_generator
        self.behavior_analyzer = behavior_analyzer

    def track_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        user_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Track an API request."""
        metric = UsageMetric(
            timestamp=datetime.now(UTC),
            metric_type=MetricType.COUNTER,
            name="api_request",
            value=1.0,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            user_id=user_id,
            tags=tags or {},
        )
        self.repository.save(metric)

    def get_anomalies(self, window_hours: int = 24) -> list[Anomaly]:
        """Get detected anomalies in the specified time window."""
        metrics = self.repository.get_recent(window_hours)
        return self.anomaly_detector.detect(metrics)

    def generate_report(self, start_time: datetime, end_time: datetime) -> dict[str, Any]:
        """Generate usage report for the specified time range."""
        return self.report_generator.generate({"start_time": start_time, "end_time": end_time})

    def analyze_user(self, user_id: str) -> BehaviorProfile:
        """Analyze user behavior and return profile."""
        return self.behavior_analyzer.analyze(user_id)

    def get_realtime_dashboard(self) -> dict[str, Any]:
        """Get real-time dashboard data."""
        recent_metrics = self.repository.get_recent(hours=1)

        total_requests = len([m for m in recent_metrics if m.name == "api_request"])
        errors = len([m for m in recent_metrics if m.status_code and m.status_code >= 400])
        error_rate = (errors / total_requests * 100) if total_requests > 0 else 0

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "last_hour": {
                "total_requests": total_requests,
                "error_rate": round(error_rate, 2),
                "total_errors": errors,
            },
        }


def get_analytics_facade() -> AnalyticsFacade:
    """
    Factory function to create AnalyticsFacade with default dependencies.

    This demonstrates Dependency Injection and makes testing easier.
    """
    repository = InMemoryMetricsRepository()
    anomaly_detector = StatisticalAnomalyDetector()
    report_generator = UsageReportGenerator(repository)
    behavior_analyzer = UserBehaviorAnalyzer(repository)

    return AnalyticsFacade(
        repository=repository,
        anomaly_detector=anomaly_detector,
        report_generator=report_generator,
        behavior_analyzer=behavior_analyzer,
    )


# Singleton instance for backward compatibility
_analytics_facade_instance: AnalyticsFacade | None = None


def get_analytics_service() -> AnalyticsFacade:
    """Get singleton instance of analytics facade."""
    global _analytics_facade_instance
    if _analytics_facade_instance is None:
        _analytics_facade_instance = get_analytics_facade()
    return _analytics_facade_instance
