import random
import statistics
import threading
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from fastapi import Request


class SamplingDecision(Enum):
    SAMPLE = 'sample'
    DROP = 'drop'
    DEFER = 'defer'


class AlertSeverity(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


@dataclass
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    sampled: bool = True
    baggage: dict[str, str] = field(default_factory=dict)

    def to_headers(self) ->dict[str, str]:
        flags = '01' if self.sampled else '00'
        headers = {'traceparent': f'00-{self.trace_id}-{self.span_id}-{flags}'}
        if self.baggage:
            tracestate = ','.join(f'{k}={v}' for k, v in self.baggage.items())
            headers['tracestate'] = tracestate
        return headers

    @classmethod
    def from_headers(cls, headers: dict[str, str]) ->'TraceContext | None':
        traceparent = headers.get('traceparent') or headers.get('Traceparent')
        if not traceparent:
            return None
        try:
            parts = traceparent.split('-')
            if len(parts) != 4:
                return None
            _version, trace_id, parent_span_id, flags = parts
            sampled = flags == '01'
            baggage = {}
            tracestate = headers.get('tracestate') or headers.get('Tracestate',
                '')
            for item in tracestate.split(','):
                if '=' in item:
                    k, v = item.split('=', 1)
                    baggage[k.strip()] = v.strip()
            span_id = uuid.uuid4().hex[:16]
            return cls(trace_id=trace_id, span_id=span_id, parent_span_id=
                parent_span_id, sampled=sampled, baggage=baggage)
        except Exception:
            return None


@dataclass
class UnifiedSpan:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation_name: str
    service_name: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    tags: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = 'OK'
    error_message: str | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    baggage: dict[str, str] = field(default_factory=dict)

    def finalize(self):
        if self.end_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class UnifiedTrace:
    trace_id: str
    root_span: UnifiedSpan
    spans: list[UnifiedSpan] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float | None = None
    total_duration_ms: float | None = None
    error_count: int = 0
    critical_path_ms: float | None = None
    bottleneck_span_id: str | None = None

    def analyze_critical_path(self):
        if not self.spans:
            return
        max_duration = 0.0
        bottleneck = None
        for span in self.spans:
            if span.duration_ms and span.duration_ms > max_duration:
                max_duration = span.duration_ms
                bottleneck = span.span_id
        self.critical_path_ms = max_duration
        self.bottleneck_span_id = bottleneck


@dataclass
class MetricSample:
    value: float
    timestamp: float
    labels: dict[str, str] = field(default_factory=dict)
    exemplar_trace_id: str | None = None
    exemplar_span_id: str | None = None


@dataclass
class CorrelatedLog:
    timestamp: float
    level: str
    message: str
    trace_id: str | None = None
    span_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    exception: dict[str, Any] | None = None


@dataclass
class AnomalyAlert:
    alert_id: str
    timestamp: float
    severity: AlertSeverity
    anomaly_type: str
    description: str
    metrics: dict[str, Any]
    trace_ids: list[str] = field(default_factory=list)
    recommended_action: str = ''
    resolved: bool = False


class UnifiedObservabilityService:

    def __init__(self, service_name: str='cogniforge', sample_rate: float=
        1.0, sla_target_ms: float=100.0):
        self.service_name = service_name
        self.sample_rate = sample_rate
        self.sla_target_ms = sla_target_ms
        self.active_traces: dict[str, UnifiedTrace] = {}
        self.active_spans: dict[str, UnifiedSpan] = {}
        self.completed_traces: deque = deque(maxlen=10000)
        self.metrics_buffer: deque = deque(maxlen=100000)
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, deque] = defaultdict(lambda : deque(
            maxlen=10000))
        self.logs_buffer: deque = deque(maxlen=50000)
        self.trace_logs: dict[str, list[CorrelatedLog]] = defaultdict(list)
        self.trace_metrics: dict[str, list[MetricSample]] = defaultdict(list)
        self.latency_p99_target = 100.0
        self.error_rate_target = 1.0
        self.saturation_target = 80.0
        self.anomaly_alerts: deque = deque(maxlen=1000)
        self.baselines: dict[str, float] = {}
        self.service_dependencies: dict[str, set[str]] = defaultdict(set)
        self.tail_sampling_buffer: dict[str, dict] = {}
        self.lock = threading.RLock()
        self.stats = {'traces_started': 0, 'traces_completed': 0,
            'spans_created': 0, 'metrics_recorded': 0, 'logs_recorded': 0,
            'anomalies_detected': 0}

    def start_trace(self, operation_name: str, parent_context: (
        TraceContext | None)=None, tags: (dict[str, Any] | None)=None,
        request: (Request | None)=None) ->TraceContext:
        if parent_context:
            head_sampled = parent_context.sampled
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
            baggage = parent_context.baggage.copy()
        else:
            head_sampled = self._head_based_sampling()
            trace_id = self._generate_trace_id()
            parent_span_id = None
            baggage = {}
        span_id = self._generate_span_id()
        span = UnifiedSpan(trace_id=trace_id, span_id=span_id,
            parent_span_id=parent_span_id, operation_name=operation_name,
            service_name=self.service_name, start_time=time.time(), tags=
            tags or {}, baggage=baggage)
        with self.lock:
            self.active_spans[span_id] = span
            if parent_span_id is None:
                trace = UnifiedTrace(trace_id=trace_id, root_span=span,
                    start_time=span.start_time)
                trace.spans.append(span)
                self.active_traces[trace_id] = trace
                self.stats['traces_started'] += 1
            elif trace_id in self.active_traces:
                self.active_traces[trace_id].spans.append(span)
            self.stats['spans_created'] += 1
        context = TraceContext(trace_id=trace_id, span_id=span_id,
            parent_span_id=parent_span_id, sampled=head_sampled, baggage=
            baggage)
        if request:
            request.state.trace_context = context
            request.state.current_span_id = span_id
        return context

    def end_span(self, span_id: str, status: str='OK', error_message: (str |
        None)=None, metrics: (dict[str, float] | None)=None):
        with self.lock:
            if span_id not in self.active_spans:
                return
            span = self.active_spans[span_id]
            span.end_time = time.time()
            span.finalize()
            span.status = status
            span.error_message = error_message
            if metrics:
                span.metrics.update(metrics)
            trace = self.active_traces.get(span.trace_id)
            if trace:
                if status == 'ERROR':
                    trace.error_count += 1
                if span.span_id == trace.root_span.span_id:
                    trace.end_time = span.end_time
                    trace.total_duration_ms = span.duration_ms
                    trace.analyze_critical_path()
                    if self._tail_based_sampling(trace):
                        self.completed_traces.append(trace)
                        self.stats['traces_completed'] += 1
                        self._correlate_trace(trace)
                    del self.active_traces[span.trace_id]
            del self.active_spans[span_id]

    def add_span_event(self, span_id: str, event_name: str, attributes: (
        dict[str, Any] | None)=None):
        with self.lock:
            if span_id in self.active_spans:
                event = {'timestamp': time.time(), 'name': event_name,
                    'attributes': attributes or {}}
                self.active_spans[span_id].events.append(event)

    def record_metric(self, name: str, value: float, labels: (dict[str, str
        ] | None)=None, trace_id: (str | None)=None, span_id: (str | None)=None
        ):
        sample = MetricSample(value=value, timestamp=time.time(), labels=
            labels or {}, exemplar_trace_id=trace_id, exemplar_span_id=span_id)
        with self.lock:
            self.metrics_buffer.append(sample)
            self.stats['metrics_recorded'] += 1
            self.histograms[name].append(value)
            if trace_id:
                self.trace_metrics[trace_id].append(sample)

    def increment_counter(self, name: str, amount: float=1.0, labels: (dict
        [str, str] | None)=None):
        key = self._metric_key(name, labels)
        with self.lock:
            self.counters[key] += amount

    def set_gauge(self, name: str, value: float, labels: (dict[str, str] |
        None)=None):
        key = self._metric_key(name, labels)
        with self.lock:
            self.gauges[key] = value

    def get_percentiles(self, metric_name: str) ->dict[str, float]:
        with self.lock:
            values = list(self.histograms.get(metric_name, []))
        if not values:
            return {'p50': 0, 'p90': 0, 'p95': 0, 'p99': 0, 'p99.9': 0}
        sorted_values = sorted(values)
        return {'p50': self._percentile(sorted_values, 50), 'p90': self.
            _percentile(sorted_values, 90), 'p95': self._percentile(
            sorted_values, 95), 'p99': self._percentile(sorted_values, 99),
            'p99.9': self._percentile(sorted_values, 99.9)}

    def log(self, level: str, message: str, context: (dict[str, Any] | None
        )=None, exception: (Exception | None)=None, trace_id: (str | None)=
        None, span_id: (str | None)=None):
        log_entry = CorrelatedLog(timestamp=time.time(), level=level,
            message=message, trace_id=trace_id, span_id=span_id, context=
            context or {})
        if exception:
            log_entry.exception = {'type': type(exception).__name__,
                'message': str(exception)}
        with self.lock:
            self.logs_buffer.append(log_entry)
            self.stats['logs_recorded'] += 1
            if trace_id:
                self.trace_logs[trace_id].append(log_entry)

    def get_trace_with_correlation(self, trace_id: str) ->(dict[str, Any] |
        None):
        trace = None
        with self.lock:
            if trace_id in self.active_traces:
                trace = self.active_traces[trace_id]
            else:
                for t in self.completed_traces:
                    if t.trace_id == trace_id:
                        trace = t
                        break
        if not trace:
            return None
        logs = []
        with self.lock:
            for log in self.trace_logs.get(trace_id, []):
                logs.append({'timestamp': datetime.fromtimestamp(log.
                    timestamp, UTC).isoformat(), 'level': log.level,
                    'message': log.message, 'span_id': log.span_id,
                    'context': log.context, 'exception': log.exception})
        metrics = []
        with self.lock:
            for metric in self.trace_metrics.get(trace_id, []):
                metrics.append({'value': metric.value, 'timestamp':
                    datetime.fromtimestamp(metric.timestamp, UTC).isoformat
                    (), 'labels': metric.labels})
        return {'trace_id': trace.trace_id, 'service_name': self.
            service_name, 'start_time': datetime.fromtimestamp(trace.
            start_time, UTC).isoformat(), 'end_time': datetime.
            fromtimestamp(trace.end_time, UTC).isoformat() if trace.
            end_time else None, 'total_duration_ms': trace.
            total_duration_ms, 'error_count': trace.error_count,
            'span_count': len(trace.spans), 'critical_path_ms': trace.
            critical_path_ms, 'bottleneck_span_id': trace.
            bottleneck_span_id, 'spans': [self._span_to_dict(span) for span in
            trace.spans], 'correlated_logs': logs, 'correlated_metrics':
            metrics}

    def find_traces_by_criteria(self, min_duration_ms: (float | None)=None,
        has_errors: (bool | None)=None, operation_name: (str | None)=None,
        limit: int=100) ->list[dict[str, Any]]:
        results = []
        with self.lock:
            traces = list(self.completed_traces)
        for trace in traces[-limit:]:
            if min_duration_ms and (not trace.total_duration_ms or trace.
                total_duration_ms < min_duration_ms):
                continue
            if has_errors is not None and (trace.error_count > 0
                ) != has_errors:
                continue
            if (operation_name and trace.root_span.operation_name !=
                operation_name):
                continue
            results.append({'trace_id': trace.trace_id, 'operation': trace.
                root_span.operation_name, 'duration_ms': trace.
                total_duration_ms, 'error_count': trace.error_count,
                'span_count': len(trace.spans), 'start_time': datetime.
                fromtimestamp(trace.start_time, UTC).isoformat()})
        return results

    def _correlate_trace(self, trace: UnifiedTrace):
        pass

    def get_golden_signals(self, time_window_seconds: int=300) ->dict[str, Any
        ]:
        cutoff = time.time() - time_window_seconds
        with self.lock:
            recent_traces = [t for t in self.completed_traces if t.
                start_time >= cutoff]
            if not recent_traces:
                return {'latency': {'p50': 0, 'p95': 0, 'p99': 0, 'p99.9': 
                    0}, 'traffic': {'requests_per_second': 0,
                    'total_requests': 0}, 'errors': {'error_rate': 0,
                    'error_count': 0}, 'saturation': {'active_requests': 0,
                    'queue_depth': 0}}
            durations = [t.total_duration_ms for t in recent_traces if t.
                total_duration_ms]
            sorted_durations = sorted(durations) if durations else []
            latency = {'p50': self._percentile(sorted_durations, 50) if
                sorted_durations else 0, 'p95': self._percentile(
                sorted_durations, 95) if sorted_durations else 0, 'p99': 
                self._percentile(sorted_durations, 99) if sorted_durations else
                0, 'p99.9': self._percentile(sorted_durations, 99.9) if
                sorted_durations else 0, 'avg': statistics.mean(durations) if
                durations else 0}
            total_requests = len(recent_traces)
            rps = (total_requests / time_window_seconds if 
                time_window_seconds > 0 else 0)
            traffic = {'requests_per_second': rps, 'total_requests':
                total_requests, 'time_window_seconds': time_window_seconds}
            error_count = sum(1 for t in recent_traces if t.error_count > 0)
            error_rate = (error_count / total_requests * 100 if 
                total_requests > 0 else 0)
            errors = {'error_rate': error_rate, 'error_count': error_count,
                'success_count': total_requests - error_count}
            active_spans_count = len(self.active_spans)
            active_traces_count = len(self.active_traces)
            saturation = {'active_requests': active_traces_count,
                'active_spans': active_spans_count, 'queue_depth': 0,
                'resource_utilization': 0}
        return {'latency': latency, 'traffic': traffic, 'errors': errors,
            'saturation': saturation, 'timestamp': datetime.now(UTC).
            isoformat(), 'sla_compliance': self._check_sla_compliance(
            latency, errors)}

    def _check_sla_compliance(self, latency: dict, errors: dict) ->dict[str,
        Any]:
        p99_compliant = latency['p99'] <= self.latency_p99_target
        error_rate_compliant = errors['error_rate'] <= self.error_rate_target
        return {'p99_latency_compliant': p99_compliant,
            'p99_latency_target_ms': self.latency_p99_target,
            'p99_latency_actual_ms': latency['p99'], 'error_rate_compliant':
            error_rate_compliant, 'error_rate_target_percent': self.
            error_rate_target, 'error_rate_actual_percent': errors[
            'error_rate'], 'overall_compliant': p99_compliant and
            error_rate_compliant}

    def _head_based_sampling(self) ->bool:
        return random.random() < self.sample_rate

    def _tail_based_sampling(self, trace: UnifiedTrace) ->bool:
        if trace.error_count > 0:
            return True
        if (trace.total_duration_ms and trace.total_duration_ms > self.
            sla_target_ms * 2):
            return True
        return random.random() < self.sample_rate

    def detect_anomalies(self) ->list[dict[str, Any]]:
        signals = self.get_golden_signals(time_window_seconds=300)
        anomalies = []
        p99 = signals['latency']['p99']
        if 'latency_p99' in self.baselines:
            baseline = self.baselines['latency_p99']
            if p99 > baseline * 3:
                anomaly = self._create_anomaly_alert(severity=AlertSeverity
                    .HIGH, anomaly_type='latency_spike', description=
                    f'P99 latency {p99:.2f}ms is 3x baseline ({baseline:.2f}ms)'
                    , metrics={'p99': p99, 'baseline': baseline})
                anomalies.append(asdict(anomaly))
        alpha = 0.1
        self.baselines['latency_p99'] = alpha * p99 + (1 - alpha
            ) * self.baselines.get('latency_p99', p99)
        error_rate = signals['errors']['error_rate']
        if 'error_rate' in self.baselines:
            baseline = self.baselines['error_rate']
            if error_rate > baseline * 2 and error_rate > 1.0:
                anomaly = self._create_anomaly_alert(severity=AlertSeverity
                    .CRITICAL, anomaly_type='error_spike', description=
                    f'Error rate {error_rate:.2f}% is 2x baseline ({baseline:.2f}%)'
                    , metrics={'error_rate': error_rate, 'baseline': baseline})
                anomalies.append(asdict(anomaly))
        self.baselines['error_rate'] = alpha * error_rate + (1 - alpha
            ) * self.baselines.get('error_rate', error_rate)
        return anomalies

    def _create_anomaly_alert(self, severity: AlertSeverity, anomaly_type:
        str, description: str, metrics: dict[str, Any]) ->AnomalyAlert:
        alert = AnomalyAlert(alert_id=str(uuid.uuid4())[:12], timestamp=
            time.time(), severity=severity, anomaly_type=anomaly_type,
            description=description, metrics=metrics, recommended_action=
            self._get_recommended_action(anomaly_type))
        with self.lock:
            self.anomaly_alerts.append(alert)
            self.stats['anomalies_detected'] += 1
        return alert

    def _get_recommended_action(self, anomaly_type: str) ->str:
        recommendations = {'latency_spike':
            'Check database query performance, review recent code changes, consider scaling'
            , 'error_spike':
            'Check error logs, review recent deployments, validate dependencies'
            , 'traffic_spike':
            'Verify load balancer health, check for DDoS, review caching'}
        return recommendations.get(anomaly_type, 'Investigate immediately')

    def get_service_dependencies(self) ->dict[str, list[str]]:
        dependencies: dict[str, set[str]] = {}
        with self.lock:
            for trace in self.completed_traces:
                service_spans = defaultdict(list)
                for span in trace.spans:
                    service_name = span.tags.get('service.name', self.
                        service_name)
                    service_spans[service_name].append(span)
                for span in trace.spans:
                    if span.parent_span_id:
                        for parent_span in trace.spans:
                            if parent_span.span_id == span.parent_span_id:
                                parent_service = parent_span.tags.get(
                                    'service.name', self.service_name)
                                child_service = span.tags.get('service.name',
                                    self.service_name)
                                if parent_service != child_service:
                                    if parent_service not in dependencies:
                                        dependencies[parent_service] = set()
                                    dependencies[parent_service].add(
                                        child_service)
        return {k: list(v) for k, v in dependencies.items()}

    def _generate_trace_id(self) ->str:
        return uuid.uuid4().hex + uuid.uuid4().hex[:16]

    def _generate_span_id(self) ->str:
        return uuid.uuid4().hex[:16]

    def _metric_key(self, name: str, labels: (dict[str, str] | None)) ->str:
        if not labels:
            return name
        label_str = ','.join(f'{k}={v}' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'

    def _percentile(self, sorted_data: list[float], percentile: float) ->float:
        if not sorted_data:
            return 0.0
        index = (len(sorted_data) - 1) * (percentile / 100.0)
        lower = int(index)
        fraction = index - lower
        if lower + 1 < len(sorted_data):
            return sorted_data[lower] + fraction * (sorted_data[lower + 1] -
                sorted_data[lower])
        return sorted_data[lower]

    def _span_to_dict(self, span: UnifiedSpan) ->dict[str, Any]:
        return {'span_id': span.span_id, 'parent_span_id': span.
            parent_span_id, 'operation_name': span.operation_name,
            'service_name': span.service_name, 'start_time': datetime.
            fromtimestamp(span.start_time, UTC).isoformat(), 'end_time': 
            datetime.fromtimestamp(span.end_time, UTC).isoformat() if span.
            end_time else None, 'duration_ms': span.duration_ms, 'status':
            span.status, 'error_message': span.error_message, 'tags': span.
            tags, 'events': span.events, 'metrics': span.metrics}

    def get_statistics(self) ->dict[str, Any]:
        with self.lock:
            return {**self.stats, 'active_traces': len(self.active_traces),
                'active_spans': len(self.active_spans), 'completed_traces':
                len(self.completed_traces), 'metrics_buffer_size': len(self
                .metrics_buffer), 'logs_buffer_size': len(self.logs_buffer),
                'anomaly_alerts': len(self.anomaly_alerts)}

    def export_prometheus_metrics(self) ->str:
        lines = []
        with self.lock:
            for key, value in self.counters.items():
                lines.append(f'{key} {value}')
            for key, value in self.gauges.items():
                lines.append(f'{key} {value}')
        return '\n'.join(lines)


_unified_observability: UnifiedObservabilityService | None = None
_obs_lock = threading.Lock()


def get_unified_observability() ->UnifiedObservabilityService:
    global _unified_observability
    if _unified_observability is None:
        with _obs_lock:
            if _unified_observability is None:
                _unified_observability = UnifiedObservabilityService()
    return _unified_observability
