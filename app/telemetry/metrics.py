from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque

from app.telemetry.models import MetricSample

logger = logging.getLogger(__name__)

class MetricsManager:
    def __init__(self):
        self.metrics_buffer: deque[MetricSample] = deque(maxlen=100000)
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=10000))
        self.trace_metrics: dict[str, list[MetricSample]] = defaultdict(list)
        self.lock = threading.RLock()
        self.stats = {'metrics_recorded': 0}

    # TODO: Reduce parameters (6 params) - Use config object
    def record_metric(self, name: str, value: float, labels: dict[str, str] | None = None,
                      trace_id: str | None = None, span_id: str | None = None) -> None:
        sample = MetricSample(
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            exemplar_trace_id=trace_id,
            exemplar_span_id=span_id
        )
        with self.lock:
            self.metrics_buffer.append(sample)
            self.stats['metrics_recorded'] += 1
            self.histograms[name].append(value)
            if trace_id:
                self.trace_metrics[trace_id].append(sample)

    def increment_counter(self, name: str, amount: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = self._metric_key(name, labels)
        with self.lock:
            self.counters[key] += amount

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._metric_key(name, labels)
        with self.lock:
            self.gauges[key] = value

    def get_percentiles(self, metric_name: str) -> dict[str, float]:
        with self.lock:
            values = list(self.histograms.get(metric_name, []))

        if not values:
            return {'p50': 0, 'p90': 0, 'p95': 0, 'p99': 0, 'p99.9': 0}

        sorted_values = sorted(values)
        return {
            'p50': self._percentile(sorted_values, 50),
            'p90': self._percentile(sorted_values, 90),
            'p95': self._percentile(sorted_values, 95),
            'p99': self._percentile(sorted_values, 99),
            'p99.9': self._percentile(sorted_values, 99.9)
        }

    def _metric_key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ','.join(f'{k}={v}' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'

    def _percentile(self, sorted_data: list[float], percentile: float) -> float:
        if not sorted_data:
            return 0.0
        index = (len(sorted_data) - 1) * (percentile / 100.0)
        lower = int(index)
        fraction = index - lower
        if lower + 1 < len(sorted_data):
            return sorted_data[lower] + fraction * (sorted_data[lower + 1] - sorted_data[lower])
        return sorted_data[lower]

    def export_prometheus_metrics(self) -> str:
        lines = []
        with self.lock:
            for key, value in self.counters.items():
                lines.append(f'{key} {value}')
            for key, value in self.gauges.items():
                lines.append(f'{key} {value}')
        return '\n'.join(lines)
