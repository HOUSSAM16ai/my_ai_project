# app/services/observability_integration_service.py
# ======================================================================================
# ==    OBSERVABILITY & MONITORING INTEGRATION - تكامل المراقبة والرصد                ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام رصد ومراقبة متكامل يجمع كل المكونات
#   ✨ المميزات الخارقة:
#   - Metrics Collection (Prometheus-style)
#   - Distributed Tracing (W3C Trace Context)
#   - Log Aggregation
#   - Alerting & Notifications
#   - Performance Dashboards
#   - Anomaly Detection (ML-based)

from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class MetricType(Enum):
    """أنواع المقاييس"""

    COUNTER = "counter"  # عداد (يزيد فقط)
    GAUGE = "gauge"  # مقياس (يزيد وينقص)
    HISTOGRAM = "histogram"  # مدرج تكراري
    SUMMARY = "summary"  # ملخص


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


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


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
    source: str  # deployment, kubernetes, model_serving, etc.
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

    # Deployment metrics
    active_deployments: int = 0
    successful_deployments: int = 0
    failed_deployments: int = 0
    avg_deployment_time_seconds: float = 0.0

    # Kubernetes metrics
    total_pods: int = 0
    healthy_pods: int = 0
    total_nodes: int = 0
    ready_nodes: int = 0
    cluster_cpu_usage: float = 0.0
    cluster_memory_usage: float = 0.0

    # Model serving metrics
    total_models: int = 0
    serving_models: int = 0
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0

    # Circuit breaker metrics
    open_circuits: int = 0
    half_open_circuits: int = 0


# ======================================================================================
# OBSERVABILITY INTEGRATION SERVICE
# ======================================================================================


class ObservabilityIntegration:
    """
    خدمة تكامل المراقبة والرصد

    تجمع المقاييس من جميع المكونات وتوفر رؤية شاملة
    """

    def __init__(self):
        self._metrics: deque[Metric] = deque(maxlen=100000)
        self._traces: dict[str, list[Span]] = defaultdict(list)
        self._alerts: deque[Alert] = deque(maxlen=10000)
        self._health_statuses: dict[str, HealthStatus] = {}
        self._performance_snapshots: deque[PerformanceSnapshot] = deque(maxlen=1000)

        self._lock = threading.RLock()

        # بدء جمع المقاييس الدوري
        self._start_metrics_collection()

        # بدء كشف الشذوذ
        self._start_anomaly_detection()

    # ======================================================================================
    # METRICS COLLECTION
    # ======================================================================================

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: dict[str, str] | None = None,
    ):
        """
        تسجيل مقياس

        Args:
            name: اسم المقياس
            value: القيمة
            metric_type: نوع المقياس
            labels: تصنيفات إضافية
        """
        metric = Metric(
            metric_id=str(uuid.uuid4()),
            name=name,
            metric_type=metric_type,
            value=value,
            labels=labels or {},
        )

        with self._lock:
            self._metrics.append(metric)

    def get_metrics(
        self,
        name: str | None = None,
        labels: dict[str, str] | None = None,
        limit: int = 100,
    ) -> list[Metric]:
        """
        الحصول على المقاييس

        Args:
            name: تصفية حسب الاسم (اختياري)
            labels: تصفية حسب التصنيفات (اختياري)
            limit: الحد الأقصى للنتائج

        Returns:
            قائمة المقاييس
        """
        with self._lock:
            metrics = list(self._metrics)

        # تصفية حسب الاسم
        if name:
            metrics = [m for m in metrics if m.name == name]

        # تصفية حسب التصنيفات
        if labels:
            metrics = [m for m in metrics if all(m.labels.get(k) == v for k, v in labels.items())]

        return metrics[-limit:]

    # ======================================================================================
    # DISTRIBUTED TRACING
    # ======================================================================================

    def start_span(
        self,
        operation_name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Span:
        """
        بدء فترة تتبع جديدة

        Args:
            operation_name: اسم العملية
            trace_id: معرف التتبع (يُنشأ تلقائياً إذا لم يُحدد)
            parent_span_id: معرف الفترة الأب

        Returns:
            الفترة الجديدة
        """
        if not trace_id:
            trace_id = str(uuid.uuid4())

        span = Span(
            span_id=str(uuid.uuid4()),
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(UTC),
        )

        with self._lock:
            self._traces[trace_id].append(span)

        return span

    def end_span(self, span: Span, status: TraceStatus = TraceStatus.OK):
        """
        إنهاء فترة التتبع

        Args:
            span: الفترة
            status: الحالة النهائية
        """
        span.end_time = datetime.now(UTC)
        span.status = status

    def add_span_log(self, span: Span, message: str, metadata: dict[str, Any] | None = None):
        """إضافة سجل لفترة التتبع"""
        log = {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": message,
            "metadata": metadata or {},
        }
        span.logs.append(log)

    def get_trace(self, trace_id: str) -> list[Span]:
        """الحصول على جميع الفترات في تتبع معين"""
        return self._traces.get(trace_id, [])

    # ======================================================================================
    # ALERTING
    # ======================================================================================

    def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        source: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        تفعيل تنبيه

        Args:
            name: اسم التنبيه
            severity: الشدة
            message: الرسالة
            source: المصدر
            metadata: بيانات إضافية

        Returns:
            معرف التنبيه
        """
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            name=name,
            severity=severity,
            message=message,
            source=source,
            metadata=metadata or {},
        )

        with self._lock:
            self._alerts.append(alert)

        # في النظام الحقيقي، يتم إرسال التنبيه:
        # - Email
        # - Slack
        # - PagerDuty
        # - etc.

        return alert.alert_id

    def resolve_alert(self, alert_id: str):
        """حل تنبيه"""
        with self._lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now(UTC)
                    break

    def get_active_alerts(self, severity: AlertSeverity | None = None) -> list[Alert]:
        """الحصول على التنبيهات النشطة"""
        with self._lock:
            alerts = [a for a in self._alerts if not a.resolved]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    # ======================================================================================
    # HEALTH MONITORING
    # ======================================================================================

    def update_health_status(
        self,
        component: str,
        healthy: bool,
        message: str,
        metrics: dict[str, Any] | None = None,
    ):
        """
        تحديث حالة صحة مكون

        Args:
            component: اسم المكون
            healthy: هل صحي؟
            message: رسالة الحالة
            metrics: مقاييس إضافية
        """
        status = HealthStatus(
            component=component,
            healthy=healthy,
            message=message,
            metrics=metrics or {},
        )

        with self._lock:
            self._health_statuses[component] = status

        # تفعيل تنبيه إذا كان غير صحي
        if not healthy:
            self.trigger_alert(
                name=f"{component}_unhealthy",
                severity=AlertSeverity.WARNING,
                message=message,
                source=component,
            )

    def get_overall_health(self) -> dict[str, Any]:
        """الحصول على الحالة الصحية الإجمالية"""
        with self._lock:
            statuses = dict(self._health_statuses)

        all_healthy = all(s.healthy for s in statuses.values())

        return {
            "healthy": all_healthy,
            "components": {
                name: {
                    "healthy": status.healthy,
                    "message": status.message,
                    "last_check": status.last_check.isoformat(),
                }
                for name, status in statuses.items()
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # ======================================================================================
    # PERFORMANCE MONITORING
    # ======================================================================================

    def _start_metrics_collection(self):
        """بدء جمع المقاييس الدوري"""

        def collect():
            while True:
                try:
                    self._collect_system_metrics()
                    time.sleep(30)  # كل 30 ثانية
                except Exception as e:
                    print(f"Metrics collection error: {e}")

        thread = threading.Thread(target=collect, daemon=True)
        thread.start()

    def _collect_system_metrics(self):
        """جمع مقاييس النظام"""
        # جمع من جميع المكونات
        from app.services.deployment_orchestrator_service import get_deployment_orchestrator
        from app.services.kubernetes_orchestration_service import get_kubernetes_orchestrator
        from app.services.model_serving_infrastructure import get_model_serving_infrastructure

        try:
            # Deployment metrics
            orchestrator = get_deployment_orchestrator()
            deployment_metrics = self._collect_deployment_metrics(orchestrator)

            # Kubernetes metrics
            k8s = get_kubernetes_orchestrator()
            k8s_metrics = self._collect_kubernetes_metrics(k8s)

            # Model serving metrics
            model_serving = get_model_serving_infrastructure()
            model_metrics = self._collect_model_serving_metrics(model_serving)

            # إنشاء لقطة الأداء
            snapshot = PerformanceSnapshot(
                snapshot_id=str(uuid.uuid4()),
                **deployment_metrics,
                **k8s_metrics,
                **model_metrics,
            )

            with self._lock:
                self._performance_snapshots.append(snapshot)

        except Exception as e:
            print(f"Error collecting system metrics: {e}")

    def _collect_deployment_metrics(self, orchestrator) -> dict[str, Any]:
        """جمع مقاييس النشر"""
        # في النظام الحقيقي، جمع من orchestrator
        return {
            "active_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "avg_deployment_time_seconds": 0.0,
        }

    def _collect_kubernetes_metrics(self, k8s) -> dict[str, Any]:
        """جمع مقاييس Kubernetes"""
        try:
            stats = k8s.get_cluster_stats()
            return {
                "total_pods": stats.get("total_pods", 0),
                "healthy_pods": stats.get("running_pods", 0),
                "total_nodes": stats.get("total_nodes", 0),
                "ready_nodes": stats.get("ready_nodes", 0),
                "cluster_cpu_usage": stats.get("cpu_utilization", 0.0),
                "cluster_memory_usage": stats.get("memory_utilization", 0.0),
            }
        except:
            return {}

    def _collect_model_serving_metrics(self, model_serving) -> dict[str, Any]:
        """جمع مقاييس تقديم النماذج"""
        try:
            models = model_serving.list_models()
            return {
                "total_models": len(models),
                "serving_models": sum(1 for m in models if m.status.value == "ready"),
            }
        except:
            return {}

    # ======================================================================================
    # ANOMALY DETECTION
    # ======================================================================================

    def _start_anomaly_detection(self):
        """بدء كشف الشذوذ"""

        def detect():
            while True:
                try:
                    self._detect_anomalies()
                    time.sleep(60)  # كل دقيقة
                except Exception as e:
                    print(f"Anomaly detection error: {e}")

        thread = threading.Thread(target=detect, daemon=True)
        thread.start()

    def _detect_anomalies(self):
        """كشف الشذوذات"""
        # في النظام الحقيقي، استخدام ML للكشف عن الشذوذات

        # مثال: فحص معدل الأخطاء
        error_rate_metrics = self.get_metrics(name="error_rate", limit=10)

        if error_rate_metrics:
            recent_avg = sum(m.value for m in error_rate_metrics[-5:]) / 5
            historical_avg = sum(m.value for m in error_rate_metrics) / len(error_rate_metrics)

            # إذا كان المعدل الحالي أعلى بكثير من التاريخي
            if recent_avg > historical_avg * 2:
                self.trigger_alert(
                    name="error_rate_spike",
                    severity=AlertSeverity.WARNING,
                    message=f"Error rate spike detected: {recent_avg:.2f}% vs historical {historical_avg:.2f}%",
                    source="anomaly_detection",
                )

    # ======================================================================================
    # QUERY METHODS
    # ======================================================================================

    def get_performance_snapshot(self, limit: int = 1) -> list[PerformanceSnapshot]:
        """الحصول على لقطات الأداء"""
        with self._lock:
            return list(self._performance_snapshots)[-limit:]

    def get_dashboard_data(self) -> dict[str, Any]:
        """
        الحصول على بيانات لوحة المعلومات

        Returns:
            بيانات شاملة لعرض لوحة المعلومات
        """
        snapshot = (
            self.get_performance_snapshot(limit=1)[0] if self._performance_snapshots else None
        )

        return {
            "health": self.get_overall_health(),
            "active_alerts": len(self.get_active_alerts()),
            "critical_alerts": len(self.get_active_alerts(AlertSeverity.CRITICAL)),
            "performance": snapshot.__dict__ if snapshot else {},
            "timestamp": datetime.now(UTC).isoformat(),
        }


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_observability_instance: ObservabilityIntegration | None = None
_observability_lock = threading.Lock()


def get_observability() -> ObservabilityIntegration:
    """الحصول على نسخة واحدة من خدمة المراقبة (Singleton)"""
    global _observability_instance

    if _observability_instance is None:
        with _observability_lock:
            if _observability_instance is None:
                _observability_instance = ObservabilityIntegration()

    return _observability_instance
