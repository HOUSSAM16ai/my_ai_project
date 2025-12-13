"""
Domain Models for Observability Integration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class MetricType(Enum):
    """أنواع المقاييس"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """شدة التنبيه"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TraceStatus(Enum):
    """حالة التتبع"""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


@dataclass
class Metric:
    """مقياس"""

    metric_id: str
    name: str
    metric_type: MetricType
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Span:
    """فترة زمنية في التتبع الموزع"""

    span_id: str
    trace_id: str
    parent_span_id: str | None
    operation_name: str
    start_time: datetime
    end_time: datetime | None = None
    status: TraceStatus = TraceStatus.UNSET
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Alert:
    """تنبيه"""

    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    triggered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    resolved: bool = False


@dataclass
class HealthStatus:
    """حالة الصحة الإجمالية"""

    component: str
    healthy: bool
    message: str
    last_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """لقطة من الأداء"""

    snapshot_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    active_deployments: int = 0
    successful_deployments: int = 0
    failed_deployments: int = 0
    avg_deployment_time_seconds: float = 0.0
    total_pods: int = 0
    healthy_pods: int = 0
    total_nodes: int = 0
    ready_nodes: int = 0
    cluster_cpu_usage: float = 0.0
    cluster_memory_usage: float = 0.0
    total_models: int = 0
    serving_models: int = 0
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    open_circuits: int = 0
    half_open_circuits: int = 0
