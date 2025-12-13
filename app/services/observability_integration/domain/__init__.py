"""
Observability Integration - Domain Layer
=========================================

Pure business logic and domain models for observability and monitoring.
"""

from .models import (
    Alert,
    AlertSeverity,
    HealthStatus,
    Metric,
    MetricType,
    PerformanceSnapshot,
    Span,
    TraceStatus,
)
from .ports import (
    IAlertRepository,
    IHealthMonitor,
    IMetricsCollector,
    ITraceExporter,
)

__all__ = [
    # Models
    "Alert",
    "AlertSeverity",
    "HealthStatus",
    "Metric",
    "MetricType",
    "PerformanceSnapshot",
    "Span",
    "TraceStatus",
    # Ports
    "IAlertRepository",
    "IHealthMonitor",
    "IMetricsCollector",
    "ITraceExporter",
]
