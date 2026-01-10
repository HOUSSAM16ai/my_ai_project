import statistics
import threading
import time
import uuid
from collections import deque
from dataclasses import asdict
from datetime import UTC, datetime

from app.telemetry.metrics import MetricsManager
from app.telemetry.models import AlertSeverity, AnomalyAlert, UnifiedTrace
from app.telemetry.tracing import TracingManager


class TelemetryAnalyzer:
    """
    مححل البيانات التشخيصية.
    مسؤول عن تحليل الأنماط، حساب الإشارات الذهبية (Golden Signals)، واكتشاف الشذوذ.

    Telemetry Analyzer.
    Responsible for pattern analysis, calculating Golden Signals, and anomaly detection.
    """

    def __init__(
        self,
        tracing_manager: TracingManager,
        metrics_manager: MetricsManager,
        latency_p99_target: float = 100.0,
        error_rate_target: float = 1.0
    ):
        self.tracing = tracing_manager
        self.metrics = metrics_manager

        self.latency_p99_target = latency_p99_target
        self.error_rate_target = error_rate_target

        self.baselines: dict[str, float] = {}
        self.anomaly_alerts: deque[AnomalyAlert] = deque(maxlen=1000)
        self.lock = threading.RLock()
        self.anomalies_detected_count = 0

    def get_golden_signals(self, time_window_seconds: int = 300) -> dict[str, object]:
        """
        حساب الإشارات الذهبية الأربعة (Latency, Traffic, Errors, Saturation).

        Calculate the four Golden Signals (Latency, Traffic, Errors, Saturation).

        Args:
            time_window_seconds: النافذة الزمنية للتحليل بالثواني (افتراضي: 300)

        Returns:
            قاموس يحتوي على الإشارات الذهبية وحالة الامتثال لاتفاقية مستوى الخدمة (SLA).
        """
        cutoff = time.time() - time_window_seconds

        with self.tracing.lock:
            recent_traces = [t for t in self.tracing.completed_traces if t.start_time >= cutoff]

        if not recent_traces:
            return self._get_empty_signals()

        latency = self._calculate_latency(recent_traces)
        traffic = self._calculate_traffic(recent_traces, time_window_seconds)
        errors = self._calculate_errors(recent_traces, traffic['total_requests'])
        saturation = self._calculate_saturation()

        return {
            'latency': latency,
            'traffic': traffic,
            'errors': errors,
            'saturation': saturation,
            'timestamp': datetime.now(UTC).isoformat(),
            'sla_compliance': self._check_sla_compliance(latency, errors)
        }

    def detect_anomalies(self) -> list[dict[str, object]]:
        """
        اكتشاف الشذوذ في البيانات التشخيصية بناءً على خط الأساس التاريخي.

        Detect anomalies in telemetry data based on historical baselines.

        Returns:
            قائمة بالتنبيهات المكتشفة.
        """
        signals = self.get_golden_signals(time_window_seconds=300)
        anomalies = []

        # 1. تحليل الكمون (Latency Analysis)
        p99 = signals['latency']['p99']
        self._check_latency_anomaly(p99, anomalies)
        self._update_baseline('latency_p99', p99)

        # 2. تحليل الأخطاء (Error Analysis)
        error_rate = signals['errors']['error_rate']
        self._check_error_anomaly(error_rate, anomalies)
        self._update_baseline('error_rate', error_rate)

        return anomalies

    # --- Helper Methods (Private) ---

    def _get_empty_signals(self) -> dict[str, object]:
        return {
            'latency': {'p50': 0, 'p95': 0, 'p99': 0, 'p99.9': 0, 'avg': 0},
            'traffic': {'requests_per_second': 0, 'total_requests': 0},
            'errors': {'error_rate': 0, 'error_count': 0},
            'saturation': {'active_requests': 0, 'queue_depth': 0}
        }

    def _calculate_latency(self, traces: list[UnifiedTrace]) -> dict[str, float]:
        durations = [t.total_duration_ms for t in traces if t.total_duration_ms]
        sorted_durations = sorted(durations) if durations else []

        if not sorted_durations:
            return {'p50': 0, 'p95': 0, 'p99': 0, 'p99.9': 0, 'avg': 0}

        return {
            'p50': self.metrics._percentile(sorted_durations, 50),
            'p95': self.metrics._percentile(sorted_durations, 95),
            'p99': self.metrics._percentile(sorted_durations, 99),
            'p99.9': self.metrics._percentile(sorted_durations, 99.9),
            'avg': statistics.mean(durations)
        }

    def _calculate_traffic(self, traces: list[UnifiedTrace], window: int) -> dict[str, object]:
        total = len(traces)
        rps = total / window if window > 0 else 0
        return {
            'requests_per_second': rps,
            'total_requests': total,
            'time_window_seconds': window
        }

    def _calculate_errors(self, traces: list[UnifiedTrace], total: int) -> dict[str, object]:
        error_count = sum(1 for t in traces if t.error_count > 0)
        error_rate = (error_count / total * 100) if total > 0 else 0
        return {
            'error_rate': error_rate,
            'error_count': error_count,
            'success_count': total - error_count
        }

    def _calculate_saturation(self) -> dict[str, int]:
        with self.tracing.lock:
            active_spans = len(self.tracing.active_spans)
            active_traces = len(self.tracing.active_traces)

        return {
            'active_requests': active_traces,
            'active_spans': active_spans,
            'queue_depth': 0,
            'resource_utilization': 0
        }

    def _check_sla_compliance(self, latency: dict[str, float], errors: dict[str, float]) -> dict[str, object]:
        """التحقق من الامتثال لاتفاقية مستوى الخدمة"""
        p99_compliant = latency['p99'] <= self.latency_p99_target
        error_rate_compliant = errors['error_rate'] <= self.error_rate_target

        return {
            'p99_latency_compliant': p99_compliant,
            'p99_latency_target_ms': self.latency_p99_target,
            'p99_latency_actual_ms': latency['p99'],
            'error_rate_compliant': error_rate_compliant,
            'error_rate_target_percent': self.error_rate_target,
            'error_rate_actual_percent': errors['error_rate'],
            'overall_compliant': p99_compliant and error_rate_compliant
        }

    def _check_latency_anomaly(self, current_p99: float, anomalies: list) -> None:
        if 'latency_p99' not in self.baselines:
            return

        baseline = self.baselines['latency_p99']
        if current_p99 > baseline * 3:
            anomaly = self._create_anomaly_alert(
                severity=AlertSeverity.HIGH,
                anomaly_type='latency_spike',
                description=f"P99 latency {current_p99:.2f}ms is 3x baseline ({baseline:.2f}ms)",
                metrics={'p99': current_p99, 'baseline': baseline}
            )
            anomalies.append(asdict(anomaly))

    def _check_error_anomaly(self, current_rate: float, anomalies: list) -> None:
        if 'error_rate' not in self.baselines:
            return

        baseline = self.baselines['error_rate']
        if current_rate > baseline * 2 and current_rate > 1.0:
            anomaly = self._create_anomaly_alert(
                severity=AlertSeverity.CRITICAL,
                anomaly_type='error_spike',
                description=f"Error rate {current_rate:.2f}% is 2x baseline ({baseline:.2f}%)",
                metrics={'error_rate': current_rate, 'baseline': baseline}
            )
            anomalies.append(asdict(anomaly))

    def _update_baseline(self, key: str, value: float, alpha: float = 0.1) -> None:
        """Exponential Moving Average (EMA) تحديث"""
        current = self.baselines.get(key, value)
        self.baselines[key] = alpha * value + (1 - alpha) * current

    def _create_anomaly_alert(self, severity: AlertSeverity, anomaly_type: str, description: str, metrics: dict[str, object]) -> AnomalyAlert:
        alert = AnomalyAlert(
            alert_id=str(uuid.uuid4())[:12],
            timestamp=time.time(),
            severity=severity,
            anomaly_type=anomaly_type,
            description=description,
            metrics=metrics,
            recommended_action=self._get_recommended_action(anomaly_type)
        )
        with self.lock:
            self.anomaly_alerts.append(alert)
            self.anomalies_detected_count += 1
        return alert

    def _get_recommended_action(self, anomaly_type: str) -> str:
        recommendations = {
            'latency_spike': 'Check database query performance, review recent code changes, consider scaling',
            'error_spike': 'Check error logs, review recent deployments, validate dependencies',
            'traffic_spike': 'Verify load balancer health, check for DDoS, review caching'
        }
        return recommendations.get(anomaly_type, 'Investigate immediately')
