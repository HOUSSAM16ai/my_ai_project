"""Domain interfaces - Contracts for implementations."""

from abc import ABC, abstractmethod
from typing import Any, Protocol

from app.analytics.domain.entities import Anomaly, UsageMetric


class MetricsRepository(Protocol):
    """Repository for storing and retrieving metrics."""

    def save(self, metric: UsageMetric) -> None:
        """Save a metric."""
        ...

    def get_recent(self, hours: int) -> list[UsageMetric]:
        """Get metrics from the last N hours."""
        ...

    def get_by_user(self, user_id: str) -> list[UsageMetric]:
        """Get all metrics for a specific user."""
        ...

    def get_range(self, start_time: Any, end_time: Any) -> list[UsageMetric]:
        """Get metrics within a time range."""
        ...


class AnomalyDetector(ABC):
    """Interface for anomaly detection - Open/Closed Principle."""

    @abstractmethod
    def detect(self, metrics: list[UsageMetric]) -> list[Anomaly]:
        """Detect anomalies in metrics."""
        pass


class ReportGenerator(ABC):
    """Interface for report generation - Open/Closed Principle."""

    @abstractmethod
    def generate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate a report from data."""
        pass
