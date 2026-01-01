from typing import Any

import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict
from datetime import UTC, datetime

from fastapi import Request

from app.telemetry.metrics import MetricsManager

# Import from new modules
from app.telemetry.models import (
    AlertSeverity,
    AnomalyAlert,
    CorrelatedLog,
    MetricSample,
    TraceContext,
    UnifiedSpan,
    UnifiedTrace,
)
from app.telemetry.structured_logging import LoggingManager
from app.telemetry.tracing import TracingManager

class UnifiedObservabilityService:
    def __init__(self, service_name: str = 'cogniforge', sample_rate: float = 1.0, sla_target_ms: float = 100.0):
        # Composition of managers
        self.tracing = TracingManager(service_name, sample_rate, sla_target_ms)
        self.metrics = MetricsManager()
        self.logging = LoggingManager()

        self.service_name = service_name
        self.sample_rate = sample_rate
        self.sla_target_ms = sla_target_ms

        # State kept here for aggregation/anomaly detection (high-level logic)
        self.latency_p99_target = 100.0
        self.error_rate_target = 1.0
        self.saturation_target = 80.0
        self.anomaly_alerts: deque[AnomalyAlert] = deque(maxlen=1000)
        self.baselines: dict[str, float] = {}
        self.tail_sampling_buffer: dict[str, dict] = {}

        # Lock for aggregating stats
        self.lock = threading.RLock()

        # Initialize stats dict (composite of inner managers)
        self.stats = {
            'anomalies_detected': 0
        }

    # Delegate Tracing Methods
    @property
    def active_traces(self) -> dict[str, UnifiedTrace]:
        return self.tracing.active_traces

    @property
    def active_spans(self) -> dict[str, UnifiedSpan]:
        return self.tracing.active_spans

    @property
    def completed_traces(self) -> deque[UnifiedTrace]:
        return self.tracing.completed_traces

    def start_trace(self, operation_name: str, parent_context: TraceContext | None = None,
                    tags: dict[str, Any] | None = None, request: Request | None = None) -> TraceContext:
        return self.tracing.start_trace(operation_name, parent_context, tags, request)

    def end_span(self, span_id: str, status: str = 'OK', error_message: str | None = None,
                 metrics: dict[str, float] | None = None) -> None:
        completed_trace = self.tracing.end_span(span_id, status, error_message, metrics)
        if completed_trace:
            self._correlate_trace(completed_trace)

    def add_span_event(self, span_id: str, event_name: str, attributes: dict[str, Any] | None = None) -> None:
        self.tracing.add_span_event(span_id, event_name, attributes)

    # Delegate Metrics Methods
    @property
    def metrics_buffer(self) -> deque[MetricSample]:
        return self.metrics.metrics_buffer

    @property
    def counters(self) -> dict[str, float]:
        return self.metrics.counters

    @property
    def gauges(self) -> dict[str, float]:
        return self.metrics.gauges

    @property
    def histograms(self) -> dict[str, deque[float]]:
        return self.metrics.histograms

    @property
    def trace_metrics(self) -> dict[str, list[MetricSample]]:
        return self.metrics.trace_metrics

    # TODO: Reduce parameters (6 params) - Use config object
    def record_metric(self, name: str, value: float, labels: dict[str, str] | None = None,
                      trace_id: str | None = None, span_id: str | None = None) -> None:
        self.metrics.record_metric(name, value, labels, trace_id, span_id)

    def increment_counter(self, name: str, amount: float = 1.0, labels: dict[str, str] | None = None) -> None:
        self.metrics.increment_counter(name, amount, labels)

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        self.metrics.set_gauge(name, value, labels)

    def get_percentiles(self, metric_name: str) -> dict[str, float]:
        return self.metrics.get_percentiles(metric_name)

    def export_prometheus_metrics(self) -> str:
        return self.metrics.export_prometheus_metrics()

    # Delegate Logging Methods
    @property
    def logs_buffer(self) -> deque[CorrelatedLog]:
        return self.logging.logs_buffer

    @property
    def trace_logs(self) -> dict[str, list[CorrelatedLog]]:
        return self.logging.trace_logs
# TODO: Reduce parameters (7 params) - Use config object

    def log(self, level: str, message: str, context: dict[str, Any] | None = None,
            exception: Exception | None = None, trace_id: str | None = None,
            span_id: str | None = None) -> None:
        self.logging.log(level, message, context, exception, trace_id, span_id)

    # Aggregated Methods (High Level Logic)

    # TODO: Split this function (50 lines) - KISS principle
    def get_trace_with_correlation(self, trace_id: str) -> dict[str, Any] | None:
        trace = None
        # Access tracing manager lock directly or rely on atomic dict operations where possible,
        # but here we iterate so we need consistency.
        with self.tracing.lock:
            if trace_id in self.tracing.active_traces:
                trace = self.tracing.active_traces[trace_id]
            else:
                for t in self.tracing.completed_traces:
                    if t.trace_id == trace_id:
                        trace = t
                        break

        if not trace:
            return None

        logs = []
        with self.logging.lock:
            for log in self.logging.trace_logs.get(trace_id, []):
                logs.append({
                    'timestamp': datetime.fromtimestamp(log.timestamp, UTC).isoformat(),
                    'level': log.level,
                    'message': log.message,
                    'span_id': log.span_id,
                    'context': log.context,
                    'exception': log.exception
                })

        metrics = []
        with self.metrics.lock:
            for metric in self.metrics.trace_metrics.get(trace_id, []):
                metrics.append({
                    'value': metric.value,
                    'timestamp': datetime.fromtimestamp(metric.timestamp, UTC).isoformat(),
                    'labels': metric.labels
                })

        return {
            'trace_id': trace.trace_id,
            'service_name': self.service_name,
            'start_time': datetime.fromtimestamp(trace.start_time, UTC).isoformat(),
            'end_time': datetime.fromtimestamp(trace.end_time, UTC).isoformat() if trace.end_time else None,
            'total_duration_ms': trace.total_duration_ms,
            'error_count': trace.error_count,
            'span_count': len(trace.spans),
            'critical_path_ms': trace.critical_path_ms,
            'bottleneck_span_id': trace.bottleneck_span_id,
            'spans': [self._span_to_dict(span) for span in trace.spans],
            'correlated_logs': logs,
            'correlated_metrics': metrics
        }

    def find_traces_by_criteria(self, min_duration_ms: float | None = None,
                                has_errors: bool | None = None,
                                operation_name: str | None = None,
                                limit: int = 100) -> list[dict[str, Any]]:
        results = []
        with self.tracing.lock:
            traces = list(self.tracing.completed_traces)

        for trace in traces[-limit:]:
            if min_duration_ms and (not trace.total_duration_ms or trace.total_duration_ms < min_duration_ms):
                continue
            if has_errors is not None and (trace.error_count > 0) != has_errors:
                continue
            if operation_name and trace.root_span.operation_name != operation_name:
                continue

            results.append({
                'trace_id': trace.trace_id,
                'operation': trace.root_span.operation_name,
                'duration_ms': trace.total_duration_ms,
                'error_count': trace.error_count,
                'span_count': len(trace.spans),
                'start_time': datetime.fromtimestamp(trace.start_time, UTC).isoformat()
            })
        return results

    def _correlate_trace(self, trace: UnifiedTrace):
        # Placeholder for complex post-processing correlation logic
        pass
# TODO: Split this function (59 lines) - KISS principle

    def get_golden_signals(self, time_window_seconds: int = 300) -> dict[str, Any]:
        cutoff = time.time() - time_window_seconds

        with self.tracing.lock:
            recent_traces = [t for t in self.tracing.completed_traces if t.start_time >= cutoff]

        if not recent_traces:
            return {
                'latency': {'p50': 0, 'p95': 0, 'p99': 0, 'p99.9': 0},
                'traffic': {'requests_per_second': 0, 'total_requests': 0},
                'errors': {'error_rate': 0, 'error_count': 0},
                'saturation': {'active_requests': 0, 'queue_depth': 0}
            }

        durations = [t.total_duration_ms for t in recent_traces if t.total_duration_ms]
        sorted_durations = sorted(durations) if durations else []

        latency = {
            'p50': self.metrics._percentile(sorted_durations, 50) if sorted_durations else 0,
            'p95': self.metrics._percentile(sorted_durations, 95) if sorted_durations else 0,
            'p99': self.metrics._percentile(sorted_durations, 99) if sorted_durations else 0,
            'p99.9': self.metrics._percentile(sorted_durations, 99.9) if sorted_durations else 0,
            'avg': statistics.mean(durations) if durations else 0
        }

        total_requests = len(recent_traces)
        rps = total_requests / time_window_seconds if time_window_seconds > 0 else 0
        traffic = {
            'requests_per_second': rps,
            'total_requests': total_requests,
            'time_window_seconds': time_window_seconds
        }

        error_count = sum(1 for t in recent_traces if t.error_count > 0)
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        errors = {
            'error_rate': error_rate,
            'error_count': error_count,
            'success_count': total_requests - error_count
        }

        with self.tracing.lock:
            active_spans_count = len(self.tracing.active_spans)
            active_traces_count = len(self.tracing.active_traces)

        saturation = {
            'active_requests': active_traces_count,
            'active_spans': active_spans_count,
            'queue_depth': 0,
            'resource_utilization': 0
        }

        return {
            'latency': latency,
            'traffic': traffic,
            'errors': errors,
            'saturation': saturation,
            'timestamp': datetime.now(UTC).isoformat(),
            'sla_compliance': self._check_sla_compliance(latency, errors)
        }

    def _check_sla_compliance(self, latency: dict, errors: dict) -> dict[str, Any]:
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
        # TODO: Split this function (33 lines) - KISS principle
        }

    def detect_anomalies(self) -> list[dict[str, Any]]:
        signals = self.get_golden_signals(time_window_seconds=300)
        anomalies = []

        p99 = signals['latency']['p99']
        if 'latency_p99' in self.baselines:
            baseline = self.baselines['latency_p99']
            if p99 > baseline * 3:
                anomaly = self._create_anomaly_alert(
                    severity=AlertSeverity.HIGH,
                    anomaly_type='latency_spike',
                    description=f"P99 latency {p99:.2f}ms is 3x baseline ({baseline:.2f}ms)",
                    metrics={'p99': p99, 'baseline': baseline}
                )
                anomalies.append(asdict(anomaly))

        alpha = 0.1
        self.baselines['latency_p99'] = alpha * p99 + (1 - alpha) * self.baselines.get('latency_p99', p99)

        error_rate = signals['errors']['error_rate']
        if 'error_rate' in self.baselines:
            baseline = self.baselines['error_rate']
            if error_rate > baseline * 2 and error_rate > 1.0:
                anomaly = self._create_anomaly_alert(
                    severity=AlertSeverity.CRITICAL,
                    anomaly_type='error_spike',
                    description=f"Error rate {error_rate:.2f}% is 2x baseline ({baseline:.2f}%)",
                    metrics={'error_rate': error_rate, 'baseline': baseline}
                )
                anomalies.append(asdict(anomaly))

        self.baselines['error_rate'] = alpha * error_rate + (1 - alpha) * self.baselines.get('error_rate', error_rate)

        return anomalies

    def _create_anomaly_alert(self, severity: AlertSeverity, anomaly_type: str, description: str, metrics: dict[str, Any]) -> AnomalyAlert:
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
            self.stats['anomalies_detected'] += 1
        return alert

    def _get_recommended_action(self, anomaly_type: str) -> str:
        recommendations = {
            'latency_spike': 'Check database query performance, review recent code changes, consider scaling',
            'error_spike': 'Check error logs, review recent deployments, validate dependencies',
            'traffic_spike': 'Verify load balancer health, check for DDoS, review caching'
        }
        return recommendations.get(anomaly_type, 'Investigate immediately')

    def get_service_dependencies(self) -> dict[str, list[str]]:
        # This logic needs to be rebuilt because dependency tracking was implicit in the monolithic service
        # Let's rebuild it from completed traces in TracingManager
        dependencies: dict[str, set[str]] = {}
        with self.tracing.lock:
            for trace in self.tracing.completed_traces:
                service_spans = defaultdict(list)
                for span in trace.spans:
                    service_name = span.tags.get('service.name', self.service_name)
                    service_spans[service_name].append(span)

                for span in trace.spans:
                    if span.parent_span_id:
                        for parent_span in trace.spans:
                            if parent_span.span_id == span.parent_span_id:
                                parent_service = parent_span.tags.get('service.name', self.service_name)
                                child_service = span.tags.get('service.name', self.service_name)

                                if parent_service != child_service:
                                    if parent_service not in dependencies:
                                        dependencies[parent_service] = set()
                                    dependencies[parent_service].add(child_service)

        return {k: list(v) for k, v in dependencies.items()}

    def _span_to_dict(self, span: UnifiedSpan) -> dict[str, Any]:
        return {
            'span_id': span.span_id,
            'parent_span_id': span.parent_span_id,
            'operation_name': span.operation_name,
            'service_name': span.service_name,
            'start_time': datetime.fromtimestamp(span.start_time, UTC).isoformat(),
            'end_time': datetime.fromtimestamp(span.end_time, UTC).isoformat() if span.end_time else None,
            'duration_ms': span.duration_ms,
            'status': span.status,
            'error_message': span.error_message,
            'tags': span.tags,
            'events': span.events,
            'metrics': span.metrics
        }

    # Delegate helper methods for backward compatibility (used in tests)
    def _generate_trace_id(self) -> str:
        return self.tracing._generate_trace_id()

    def _generate_span_id(self) -> str:
        return self.tracing._generate_span_id()

    def get_statistics(self) -> dict[str, Any]:
        with self.lock, self.tracing.lock, self.metrics.lock, self.logging.lock:
             return {
                **self.stats,
                **self.tracing.stats,
                **self.metrics.stats,
                **self.logging.stats,
                'active_traces': len(self.tracing.active_traces),
                'active_spans': len(self.tracing.active_spans),
                'completed_traces': len(self.tracing.completed_traces),
                'metrics_buffer_size': len(self.metrics.metrics_buffer),
                'logs_buffer_size': len(self.logging.logs_buffer),
                'anomaly_alerts': len(self.anomaly_alerts)
            }

# Singleton Instance Management
_unified_observability: UnifiedObservabilityService | None = None
_obs_lock = threading.Lock()

def get_unified_observability() -> UnifiedObservabilityService:
    global _unified_observability
    if _unified_observability is None:
        with _obs_lock:
            if _unified_observability is None:
                _unified_observability = UnifiedObservabilityService()
    return _unified_observability
