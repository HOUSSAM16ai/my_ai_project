"""
Advanced Observability Layer for LLM Operations
================================================
Comprehensive monitoring, tracing, and metrics collection.

Features:
- Request/response tracing
- Performance metrics
- Cost tracking
- Error monitoring
- Distributed tracing support
- Real-time dashboards
"""
from __future__ import annotations
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
_LOG = logging.getLogger(__name__)


class TraceLevel(Enum):
    """Trace detail levels."""
    MINIMAL = 'minimal'
    STANDARD = 'standard'
    DETAILED = 'detailed'
    DEBUG = 'debug'


@dataclass
class TraceSpan:
    """Represents a single trace span."""
    span_id: str
    trace_id: str
    parent_span_id: str | None
    operation: str
    start_time: float
    end_time: float | None = None
    duration_ms: float | None = None
    status: str = 'in_progress'
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)

    def finish(self, status: str='success') ->None:
        """Mark span as finished."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def set_metadata(self, key: str, value: Any) ->None:
        """Set metadata on span."""
        self.metadata[key] = value


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: float
    name: str
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    unit: str = ''


class MetricsCollector:
    """
    Collects and aggregates metrics.
    
    Supports:
    - Counters
    - Gauges
    - Histograms
    - Timers
    """

    def __init__(self):
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._timers: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.RLock()

    def increment(self, name: str, value: float=1.0, tags: (dict[str, str] |
        None)=None) ->None:
        """Increment counter."""
        with self._lock:
            key = self._make_key(name, tags)
            self._counters[key] += value

    def gauge(self, name: str, value: float, tags: (dict[str, str] | None)=None
        ) ->None:
        """Set gauge value."""
        with self._lock:
            key = self._make_key(name, tags)
            self._gauges[key] = value

    def histogram(self, name: str, value: float, tags: (dict[str, str] |
        None)=None) ->None:
        """Record histogram value."""
        with self._lock:
            key = self._make_key(name, tags)
            self._histograms[key].append(value)
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]

    def timing(self, name: str, duration_ms: float, tags: (dict[str, str] |
        None)=None) ->None:
        """Record timing."""
        with self._lock:
            key = self._make_key(name, tags)
            self._timers[key].append(duration_ms)
            if len(self._timers[key]) > 1000:
                self._timers[key] = self._timers[key][-1000:]

    def _make_key(self, name: str, tags: (dict[str, str] | None)) ->str:
        """Create metric key from name and tags."""
        if not tags:
            return name
        tag_str = ','.join(f'{k}={v}' for k, v in sorted(tags.items()))
        return f'{name}[{tag_str}]'

    def get_histogram_stats(self, name: str, tags: (dict[str, str] | None)=None
        ) ->dict[str, float]:
        """Get histogram statistics."""
        key = self._make_key(name, tags)
        values = self._histograms.get(key, [])
        if not values:
            return {}
        sorted_values = sorted(values)
        count = len(sorted_values)
        return {'count': count, 'min': sorted_values[0], 'max':
            sorted_values[-1], 'mean': sum(sorted_values) / count, 'median':
            sorted_values[count // 2], 'p95': sorted_values[int(count * 
            0.95)], 'p99': sorted_values[int(count * 0.99)]}

    def get_timing_stats(self, name: str, tags: (dict[str, str] | None)=None
        ) ->dict[str, float]:
        """Get timing statistics."""
        key = self._make_key(name, tags)
        return self.get_histogram_stats(name, tags)

    def get_all_metrics(self) ->dict[str, Any]:
        """Get all metrics."""
        with self._lock:
            return {'counters': dict(self._counters), 'gauges': dict(self.
                _gauges), 'histograms': {k: self.get_histogram_stats(k.
                split('[')[0]) for k in self._histograms.keys()}, 'timers':
                {k: self.get_timing_stats(k.split('[')[0]) for k in self.
                _timers.keys()}}

    def reset(self) ->None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()


class Tracer:
    """
    Distributed tracing implementation.
    
    Tracks request flows across components with spans.
    """

    def __init__(self, level: TraceLevel=TraceLevel.STANDARD):
        self.level = level
        self._spans: dict[str, TraceSpan] = {}
        self._active_spans: dict[str, str] = {}
        self._lock = threading.RLock()
        self._span_counter = 0

    def start_span(self, operation: str, trace_id: (str | None)=None,
        parent_span_id: (str | None)=None, **metadata: Any) ->TraceSpan:
        """Start new trace span."""
        with self._lock:
            self._span_counter += 1
            span_id = f'span_{self._span_counter}_{int(time.time() * 1000)}'
            if trace_id is None:
                trace_id = f'trace_{int(time.time() * 1000)}'
            span = TraceSpan(span_id=span_id, trace_id=trace_id,
                parent_span_id=parent_span_id, operation=operation,
                start_time=time.time(), metadata=metadata)
            self._spans[span_id] = span
            thread_id = threading.get_ident()
            self._active_spans[thread_id] = span_id
            return span

    def finish_span(self, span: TraceSpan, status: str='success') ->None:
        """Finish trace span."""
        span.finish(status)
        thread_id = threading.get_ident()
        if self._active_spans.get(thread_id) == span.span_id:
            del self._active_spans[thread_id]

    def get_active_span(self) ->(TraceSpan | None):
        """Get active span for current thread."""
        thread_id = threading.get_ident()
        span_id = self._active_spans.get(thread_id)
        return self._spans.get(span_id) if span_id else None

    def get_trace(self, trace_id: str) ->list[TraceSpan]:
        """Get all spans for trace."""
        return [span for span in self._spans.values() if span.trace_id ==
            trace_id]

    def get_all_spans(self) ->list[TraceSpan]:
        """Get all spans."""
        return list(self._spans.values())


class ObservabilityManager:
    """
    Central observability manager.
    
    Coordinates metrics, tracing, and monitoring.
    """

    def __init__(self, trace_level: TraceLevel=TraceLevel.STANDARD):
        self.metrics = MetricsCollector()
        self.tracer = Tracer(trace_level)
        self._hooks: list[Callable[[TraceSpan], None]] = []

    def register_span_hook(self, hook: Callable[[TraceSpan], None]) ->None:
        """Register hook to be called when span finishes."""
        self._hooks.append(hook)

    def _calculate_error_rate(self, spans: list[TraceSpan]) ->float:
        """Calculate error rate from spans."""
        if not spans:
            return 0.0
        errors = len([s for s in spans if s.status == 'error'])
        return errors / len(spans) * 100

    def _calculate_avg_duration(self, spans: list[TraceSpan]) ->float:
        """Calculate average duration from spans."""
        durations = [s.duration_ms for s in spans if s.duration_ms]
        return sum(durations) / len(durations) if durations else 0.0

    def _get_operation_stats(self, spans: list[TraceSpan]) ->dict[str, Any]:
        """Get statistics by operation."""
        stats: dict[str, dict[str, Any]] = defaultdict(lambda : {'count': 0,
            'errors': 0, 'total_duration': 0.0})
        for span in spans:
            op_stats = stats[span.operation]
            op_stats['count'] += 1
            if span.status == 'error':
                op_stats['errors'] += 1
            if span.duration_ms:
                op_stats['total_duration'] += span.duration_ms
        for op, op_stats in stats.items():
            if op_stats['count'] > 0:
                op_stats['avg_duration'] = op_stats['total_duration'
                    ] / op_stats['count']
                op_stats['error_rate'] = op_stats['errors'] / op_stats['count'
                    ] * 100
        return dict(stats)


_global_observability = ObservabilityManager()


def get_observability() ->ObservabilityManager:
    """Get global observability manager."""
    return _global_observability


__all__ = ['TraceLevel', 'TraceSpan', 'MetricPoint', 'MetricsCollector',
    'Tracer', 'ObservabilityManager', 'get_observability']
