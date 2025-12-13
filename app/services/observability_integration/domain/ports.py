"""
Domain Ports (Interfaces) for Observability Integration
"""

from abc import ABC, abstractmethod
from typing import Protocol

from .models import Alert, HealthStatus, Metric, PerformanceSnapshot, Span


class IMetricsCollector(Protocol):
    """Interface for metrics collection"""

    def collect_metric(self, metric: Metric) -> None:
        """Collect a metric"""
        ...

    def get_metrics(
        self,
        name: str | None = None,
        labels: dict[str, str] | None = None,
        limit: int = 100,
    ) -> list[Metric]:
        """Retrieve metrics"""
        ...


class ITraceExporter(Protocol):
    """Interface for trace export"""

    def export_span(self, span: Span) -> None:
        """Export a span"""
        ...

    def get_trace(self, trace_id: str) -> list[Span]:
        """Get all spans for a trace"""
        ...


class IAlertRepository(Protocol):
    """Interface for alert management"""

    def store_alert(self, alert: Alert) -> None:
        """Store an alert"""
        ...

    def get_active_alerts(self) -> list[Alert]:
        """Get active alerts"""
        ...

    def resolve_alert(self, alert_id: str) -> None:
        """Resolve an alert"""
        ...


class IHealthMonitor(Protocol):
    """Interface for health monitoring"""

    def check_health(self, component: str) -> HealthStatus:
        """Check component health"""
        ...

    def get_all_health_statuses(self) -> dict[str, HealthStatus]:
        """Get all health statuses"""
        ...


class IAnomalyDetector(ABC):
    """Interface for anomaly detection"""

    @abstractmethod
    def detect_anomalies(self, metrics: list[Metric]) -> list[Alert]:
        """Detect anomalies in metrics"""
        pass


class IPerformanceTracker(Protocol):
    """Interface for performance tracking"""

    def record_snapshot(self, snapshot: PerformanceSnapshot) -> None:
        """Record a performance snapshot"""
        ...

    def get_snapshots(self, limit: int = 100) -> list[PerformanceSnapshot]:
        """Get performance snapshots"""
        ...
