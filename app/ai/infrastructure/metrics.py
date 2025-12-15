"""
Metrics Infrastructure Implementations
=======================================
Concrete implementations of MetricsPort and ObservabilityPort.

Provides comprehensive metrics collection and observability:
- In-memory metrics for development
- Time-series data collection
- Distributed tracing support
"""
from __future__ import annotations
import logging
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from app.ai.domain.ports import MetricsPort, ObservabilityPort
_LOG = logging.getLogger(__name__)


@dataclass
class Counter:
    """Counter metric that increments."""
    value: float = 0.0
    tags: dict[str, str] = field(default_factory=dict)

    def increment(self, value: float=1.0) ->None:
        """Increment counter."""
        self.value += value


@dataclass
class Gauge:
    """Gauge metric for current values."""
    value: float = 0.0
    tags: dict[str, str] = field(default_factory=dict)

    def set(self, value: float) ->None:
        """Set gauge value."""
        self.value = value


@dataclass
class Histogram:
    """Histogram for distribution of values."""
    values: list[float] = field(default_factory=list)
    tags: dict[str, str] = field(default_factory=dict)

    def record(self, value: float) ->None:
        """Record a value."""
        self.values.append(value)

    def percentile(self, p: float) ->float:
        """Calculate percentile (p in 0-1)."""
        if not self.values:
            return 0.0
        sorted_values = sorted(self.values)
        idx = int(len(sorted_values) * p)
        return sorted_values[min(idx, len(sorted_values) - 1)]

    def mean(self) ->float:
        """Calculate mean."""
        return sum(self.values) / len(self.values) if self.values else 0.0

    def min(self) ->float:
        """Get minimum value."""
        return min(self.values) if self.values else 0.0

    def max(self) ->float:
        """Get maximum value."""
        return max(self.values) if self.values else 0.0


class InMemoryMetrics(MetricsPort):
    """
    In-memory metrics collector.
    
    Features:
    - Thread-safe operations
    - Support for counters, gauges, histograms
    - Tagging/labeling support
    - Statistical aggregations
    """

    def __init__(self):
        """Initialize in-memory metrics collector."""
        self._counters: dict[str, Counter] = defaultdict(Counter)
        self._gauges: dict[str, Gauge] = defaultdict(Gauge)
        self._histograms: dict[str, Histogram] = defaultdict(Histogram)
        self._lock = threading.Lock()

    def _get_key(self, name: str, tags: (dict[str, str] | None)) ->str:
        """Generate unique key from name and tags."""
        if not tags:
            return name
        tag_str = ','.join(f'{k}={v}' for k, v in sorted(tags.items()))
        return f'{name}:{tag_str}'

    def increment_counter(self, name: str, value: float=1.0, tags: (dict[
        str, str] | None)=None) ->None:
        """Increment a counter metric."""
        key = self._get_key(name, tags)
        with self._lock:
            counter = self._counters[key]
            counter.increment(value)
            if tags:
                counter.tags = tags

    def record_gauge(self, name: str, value: float, tags: (dict[str, str] |
        None)=None) ->None:
        """Record a gauge metric."""
        key = self._get_key(name, tags)
        with self._lock:
            gauge = self._gauges[key]
            gauge.set(value)
            if tags:
                gauge.tags = tags

    def record_histogram(self, name: str, value: float, tags: (dict[str,
        str] | None)=None) ->None:
        """Record a histogram metric."""
        key = self._get_key(name, tags)
        with self._lock:
            histogram = self._histograms[key]
            histogram.record(value)
            if tags:
                histogram.tags = tags

    def get_metrics(self) ->dict[str, Any]:
        """Get all collected metrics."""
        with self._lock:
            metrics: dict[str, Any] = {'counters': {}, 'gauges': {},
                'histograms': {}}
            for key, counter in self._counters.items():
                metrics['counters'][key] = {'value': counter.value, 'tags':
                    counter.tags}
            for key, gauge in self._gauges.items():
                metrics['gauges'][key] = {'value': gauge.value, 'tags':
                    gauge.tags}
            for key, histogram in self._histograms.items():
                metrics['histograms'][key] = {'count': len(histogram.values
                    ), 'mean': histogram.mean(), 'min': histogram.min(),
                    'max': histogram.max(), 'p50': histogram.percentile(0.5
                    ), 'p95': histogram.percentile(0.95), 'p99': histogram.
                    percentile(0.99), 'tags': histogram.tags}
            return metrics

    def reset(self) ->None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


@dataclass
class Span:
    """Represents a tracing span."""
    span_id: str
    operation: str
    start_time: float
    parent_span: Span | None = None
    tags: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = 'pending'
    error: Exception | None = None
    end_time: float | None = None

    @property
    def duration_ms(self) ->float:
        """Get duration in milliseconds."""
        if self.end_time is None:
            return (time.time() - self.start_time) * 1000
        return (self.end_time - self.start_time) * 1000


class SimpleObserver(ObservabilityPort):
    """
    Simple in-memory observability implementation.
    
    Features:
    - Distributed tracing with spans
    - Event recording
    - Thread-safe operations
    - Span hierarchy tracking
    """

    def __init__(self):
        """Initialize simple observer."""
        self._spans: dict[str, Span] = {}
        self._active_spans: dict[str, str] = {}
        self._lock = threading.Lock()

    def start_span(self, operation: str, parent_span: (Any | None)=None,
        tags: (dict[str, Any] | None)=None) ->Span:
        """Start a new tracing span."""
        span_id = str(uuid.uuid4())
        span = Span(span_id=span_id, operation=operation, start_time=time.
            time(), parent_span=parent_span, tags=tags or {})
        with self._lock:
            self._spans[span_id] = span
            thread_id = str(threading.get_ident())
            self._active_spans[thread_id] = span_id
        return span

    def finish_span(self, span: Span, status: str='success', error: (
        Exception | None)=None) ->None:
        """Finish a tracing span."""
        with self._lock:
            span.end_time = time.time()
            span.status = status
            span.error = error
            thread_id = str(threading.get_ident())
            if self._active_spans.get(thread_id) == span.span_id:
                del self._active_spans[thread_id]

    def record_event(self, event_name: str, attributes: (dict[str, Any] |
        None)=None) ->None:
        """Record a discrete event."""
        event = {'name': event_name, 'timestamp': time.time(), 'attributes':
            attributes or {}}
        thread_id = str(threading.get_ident())
        with self._lock:
            span_id = self._active_spans.get(thread_id)
            if span_id and span_id in self._spans:
                self._spans[span_id].events.append(event)

    def reset(self) ->None:
        """Reset all spans."""
        with self._lock:
            self._spans.clear()
            self._active_spans.clear()


_METRICS_INSTANCE: MetricsPort | None = None
_OBSERVER_INSTANCE: ObservabilityPort | None = None
_LOCK = threading.Lock()


def get_metrics() ->MetricsPort:
    """Get or create metrics instance."""
    global _METRICS_INSTANCE
    if _METRICS_INSTANCE is not None:
        return _METRICS_INSTANCE
    with _LOCK:
        if _METRICS_INSTANCE is not None:
            return _METRICS_INSTANCE
        _METRICS_INSTANCE = InMemoryMetrics()
        return _METRICS_INSTANCE


def get_observer() ->ObservabilityPort:
    """Get or create observer instance."""
    global _OBSERVER_INSTANCE
    if _OBSERVER_INSTANCE is not None:
        return _OBSERVER_INSTANCE
    with _LOCK:
        if _OBSERVER_INSTANCE is not None:
            return _OBSERVER_INSTANCE
        _OBSERVER_INSTANCE = SimpleObserver()
        return _OBSERVER_INSTANCE


def reset_observability() ->None:
    """Reset observability singletons (for testing)."""
    global _METRICS_INSTANCE, _OBSERVER_INSTANCE
    with _LOCK:
        _METRICS_INSTANCE = None
        _OBSERVER_INSTANCE = None


__all__ = ['InMemoryMetrics', 'SimpleObserver', 'Span', 'get_metrics',
    'get_observer', 'reset_observability']
