"""
In-Memory Implementations of Repositories
"""

import threading
from collections import defaultdict, deque
from datetime import UTC, datetime

from ..domain.models import Alert, HealthStatus, Metric, PerformanceSnapshot, Span


class InMemoryMetricsCollector:
    """In-memory metrics collector"""

    def __init__(self, max_size: int = 100000):
        self._metrics: deque[Metric] = deque(maxlen=max_size)
        self._lock = threading.RLock()

    def collect_metric(self, metric: Metric) -> None:
        """Collect a metric"""
        with self._lock:
            self._metrics.append(metric)

    def get_metrics(
        self,
        name: str | None = None,
        labels: dict[str, str] | None = None,
        limit: int = 100,
    ) -> list[Metric]:
        """Retrieve metrics"""
        with self._lock:
            metrics = list(self._metrics)

        if name:
            metrics = [m for m in metrics if m.name == name]

        if labels:
            metrics = [
                m for m in metrics if all(m.labels.get(k) == v for k, v in labels.items())
            ]

        return metrics[-limit:]


class InMemoryTraceExporter:
    """In-memory trace exporter"""

    def __init__(self):
        self._traces: dict[str, list[Span]] = defaultdict(list)
        self._lock = threading.RLock()

    def export_span(self, span: Span) -> None:
        """Export a span"""
        with self._lock:
            self._traces[span.trace_id].append(span)

    def get_trace(self, trace_id: str) -> list[Span]:
        """Get all spans for a trace"""
        with self._lock:
            return list(self._traces.get(trace_id, []))


class InMemoryAlertRepository:
    """In-memory alert repository"""

    def __init__(self, max_size: int = 10000):
        self._alerts: deque[Alert] = deque(maxlen=max_size)
        self._lock = threading.RLock()

    def store_alert(self, alert: Alert) -> None:
        """Store an alert"""
        with self._lock:
            self._alerts.append(alert)

    def get_active_alerts(self) -> list[Alert]:
        """Get active alerts"""
        with self._lock:
            return [a for a in self._alerts if not a.resolved]

    def resolve_alert(self, alert_id: str) -> None:
        """Resolve an alert"""
        with self._lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now(UTC)
                    break


class InMemoryHealthMonitor:
    """In-memory health monitor"""

    def __init__(self):
        self._health_statuses: dict[str, HealthStatus] = {}
        self._lock = threading.RLock()

    def check_health(self, component: str) -> HealthStatus:
        """Check component health"""
        with self._lock:
            if component not in self._health_statuses:
                self._health_statuses[component] = HealthStatus(
                    component=component,
                    healthy=True,
                    message="Component is healthy",
                )
            return self._health_statuses[component]

    def get_all_health_statuses(self) -> dict[str, HealthStatus]:
        """Get all health statuses"""
        with self._lock:
            return dict(self._health_statuses)

    def update_health_status(self, status: HealthStatus) -> None:
        """Update health status"""
        with self._lock:
            self._health_statuses[status.component] = status


class InMemoryPerformanceTracker:
    """In-memory performance tracker"""

    def __init__(self, max_size: int = 1000):
        self._snapshots: deque[PerformanceSnapshot] = deque(maxlen=max_size)
        self._lock = threading.RLock()

    def record_snapshot(self, snapshot: PerformanceSnapshot) -> None:
        """Record a performance snapshot"""
        with self._lock:
            self._snapshots.append(snapshot)

    def get_snapshots(self, limit: int = 100) -> list[PerformanceSnapshot]:
        """Get performance snapshots"""
        with self._lock:
            snapshots = list(self._snapshots)
        return snapshots[-limit:]
