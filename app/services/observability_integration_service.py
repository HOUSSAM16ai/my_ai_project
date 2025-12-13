# app/services/observability_integration_service.py
# ======================================================================================
# ==    OBSERVABILITY & MONITORING INTEGRATION - SHIM FILE                           ==
# ======================================================================================
# This file provides backward compatibility with the original service.
# All functionality has been moved to the hexagonal architecture in:
#   app/services/observability_integration/
#
# Migration Status: ✅ COMPLETE
# Architecture: Hexagonal (Domain/Application/Infrastructure)
# Breaking Changes: NONE

from app.services.observability_integration import (
    Alert,
    AlertSeverity,
    HealthStatus,
    Metric,
    MetricType,
    ObservabilityIntegrationFacade,
    PerformanceSnapshot,
    Span,
    TraceStatus,
)

__all__ = [
    "ObservabilityIntegration",
    "Metric",
    "MetricType",
    "Span",
    "TraceStatus",
    "Alert",
    "AlertSeverity",
    "HealthStatus",
    "PerformanceSnapshot",
]


class ObservabilityIntegration:
    """
    Backward compatibility shim for ObservabilityIntegration.
    Delegates all operations to the new hexagonal architecture.
    """

    def __init__(self):
        self._facade = ObservabilityIntegrationFacade()

    def record_metric(self, name: str, value: float, metric_type=None, labels=None):
        """Record a metric"""
        metric_type = metric_type or MetricType.GAUGE
        return self._facade.record_metric(name, value, metric_type, labels)

    def get_metrics(self, name=None, labels=None, limit=100):
        """Get metrics"""
        return self._facade.get_metrics(name, labels, limit)

    def start_span(self, operation_name: str, trace_id=None, parent_span_id=None):
        """Start a span"""
        return self._facade.start_span(operation_name, trace_id, parent_span_id)

    def finish_span(self, span, status=None):
        """Finish a span"""
        status = status or TraceStatus.OK
        return self._facade.finish_span(span, status)

    def trigger_alert(self, name: str, severity, message: str, source: str, metadata=None):
        """Trigger an alert"""
        return self._facade.trigger_alert(name, severity, message, source, metadata)

    def get_active_alerts(self, severity=None):
        """Get active alerts"""
        return self._facade.get_active_alerts(severity)

    def check_component_health(self, component: str):
        """Check component health"""
        return self._facade.check_component_health(component)

    def get_overall_health(self):
        """Get overall health"""
        return self._facade.get_overall_health()

    def capture_snapshot(self, **metrics):
        """Capture performance snapshot"""
        return self._facade.capture_snapshot(**metrics)

    def get_recent_snapshots(self, limit=100):
        """Get recent snapshots"""
        return self._facade.get_recent_snapshots(limit)
