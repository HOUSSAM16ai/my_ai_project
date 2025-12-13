"""
Observability Integration Facade
=================================

Unified interface for observability and monitoring.
Provides backward compatibility with the original service.
"""

from .application import (
    AlertManager,
    HealthMonitor,
    MetricsManager,
    PerformanceTracker,
    TraceManager,
)
from .domain import (
    Alert,
    AlertSeverity,
    HealthStatus,
    Metric,
    MetricType,
    PerformanceSnapshot,
    Span,
    TraceStatus,
)
from .infrastructure import (
    InMemoryAlertRepository,
    InMemoryHealthMonitor,
    InMemoryMetricsCollector,
    InMemoryPerformanceTracker,
    InMemoryTraceExporter,
)


class ObservabilityIntegrationFacade:
    """
    Facade for Observability Integration Service

    Provides a unified interface for all observability operations.
    """

    def __init__(self):
        # Infrastructure
        self._metrics_collector = InMemoryMetricsCollector()
        self._trace_exporter = InMemoryTraceExporter()
        self._alert_repository = InMemoryAlertRepository()
        self._health_monitor = InMemoryHealthMonitor()
        self._performance_tracker = InMemoryPerformanceTracker()

        # Application Services
        self._metrics_manager = MetricsManager(self._metrics_collector)
        self._trace_manager = TraceManager(self._trace_exporter)
        self._alert_manager = AlertManager(self._alert_repository)
        self._health_monitor_service = HealthMonitor(self._health_monitor)
        self._performance_tracker_service = PerformanceTracker(self._performance_tracker)

    # Metrics Operations
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: dict[str, str] | None = None,
    ) -> Metric:
        """Record a metric"""
        return self._metrics_manager.record_metric(name, value, metric_type, labels)

    def get_metrics(
        self,
        name: str | None = None,
        labels: dict[str, str] | None = None,
        limit: int = 100,
    ) -> list[Metric]:
        """Get metrics"""
        return self._metrics_manager.get_metrics(name, labels, limit)

    def get_metric_summary(self, name: str) -> dict[str, float]:
        """Get metric summary"""
        return self._metrics_manager.get_metric_summary(name)

    # Tracing Operations
    def start_span(
        self,
        operation_name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Span:
        """Start a new span"""
        return self._trace_manager.start_span(operation_name, trace_id, parent_span_id)

    def finish_span(self, span: Span, status: TraceStatus = TraceStatus.OK) -> None:
        """Finish a span"""
        self._trace_manager.finish_span(span, status)

    def add_span_tag(self, span: Span, key: str, value: str) -> None:
        """Add tag to span"""
        self._trace_manager.add_span_tag(span, key, value)

    def add_span_log(self, span: Span, message: str, **kwargs) -> None:
        """Add log to span"""
        self._trace_manager.add_span_log(span, message, **kwargs)

    def get_trace(self, trace_id: str) -> list[Span]:
        """Get trace"""
        return self._trace_manager.get_trace(trace_id)

    # Alert Operations
    def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        source: str,
        metadata: dict | None = None,
    ) -> Alert:
        """Trigger an alert"""
        return self._alert_manager.trigger_alert(name, severity, message, source, metadata)

    def resolve_alert(self, alert_id: str) -> None:
        """Resolve an alert"""
        self._alert_manager.resolve_alert(alert_id)

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """Get active alerts"""
        return self._alert_manager.get_active_alerts(severity)

    def get_critical_alerts(self) -> list[Alert]:
        """Get critical alerts"""
        return self._alert_manager.get_critical_alerts()

    # Health Monitoring
    def check_component_health(self, component: str) -> HealthStatus:
        """Check component health"""
        return self._health_monitor_service.check_component_health(component)

    def get_overall_health(self) -> dict:
        """Get overall health"""
        return self._health_monitor_service.get_overall_health()

    def get_unhealthy_components(self) -> list[HealthStatus]:
        """Get unhealthy components"""
        return self._health_monitor_service.get_unhealthy_components()

    # Performance Tracking
    def capture_snapshot(self, **metrics) -> PerformanceSnapshot:
        """Capture performance snapshot"""
        return self._performance_tracker_service.capture_snapshot(**metrics)

    def get_recent_snapshots(self, limit: int = 100) -> list[PerformanceSnapshot]:
        """Get recent snapshots"""
        return self._performance_tracker_service.get_recent_snapshots(limit)

    def get_performance_trends(self) -> dict:
        """Get performance trends"""
        return self._performance_tracker_service.get_performance_trends()

    # Legacy compatibility methods
    def get_all_metrics(self) -> list[Metric]:
        """Get all metrics (legacy)"""
        return self.get_metrics(limit=10000)

    def get_all_traces(self) -> dict[str, list[Span]]:
        """Get all traces (legacy)"""
        return {}

    def get_all_alerts(self) -> list[Alert]:
        """Get all alerts (legacy)"""
        return self.get_active_alerts()

    def get_health_status(self) -> dict:
        """Get health status (legacy)"""
        return self.get_overall_health()

    def get_performance_snapshot(self) -> PerformanceSnapshot | None:
        """Get latest performance snapshot (legacy)"""
        snapshots = self.get_recent_snapshots(limit=1)
        return snapshots[0] if snapshots else None
