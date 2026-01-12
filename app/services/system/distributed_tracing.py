from __future__ import annotations

import logging
import threading
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class SpanKind(Enum):
    """Span kind classification"""

    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


class SamplingStrategy(Enum):
    """Trace sampling strategies"""

    ALWAYS = "always"
    NEVER = "never"
    PROBABILISTIC = "probabilistic"
    RATE_LIMITING = "rate_limiting"


@dataclass
class SpanContext:
    """Span context for trace propagation"""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    baggage: dict[str, str] = field(default_factory=dict)


@dataclass
class Span:
    """Trace span"""

    span_id: str
    trace_id: str
    operation_name: str
    service_name: str
    kind: SpanKind
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    parent_span_id: str | None = None
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    status_code: str = "OK"
    status_message: str | None = None
    baggage: dict[str, str] = field(default_factory=dict)


@dataclass
class Trace:
    """Complete trace aggregation"""

    trace_id: str
    root_span_id: str
    service_name: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    spans: list[Span] = field(default_factory=list)
    span_count: int = 0
    error_count: int = 0


class TraceContextPropagator:
    """
    Propagates trace context across services

    Implements W3C Trace Context specification
    """

    TRACEPARENT_HEADER = "traceparent"
    TRACESTATE_HEADER = "tracestate"

    @staticmethod
    def inject(span_context: SpanContext, headers: dict[str, str]) -> None:
        """
        Inject trace context into HTTP headers

        Format: 00-{trace_id}-{span_id}-{flags}
        """
        traceparent = f"00-{span_context.trace_id}-{span_context.span_id}-01"
        headers[TraceContextPropagator.TRACEPARENT_HEADER] = traceparent
        if span_context.baggage:
            tracestate = ",".join(f"{k}={v}" for k, v in span_context.baggage.items())
            headers[TraceContextPropagator.TRACESTATE_HEADER] = tracestate

    @staticmethod
    def extract(headers: dict[str, str]) -> SpanContext | None:
        """Extract trace context from HTTP headers"""
        traceparent = headers.get(TraceContextPropagator.TRACEPARENT_HEADER)
        if not traceparent:
            return None
        try:
            parts = traceparent.split("-")
            if len(parts) != 4:
                return None
            _version, trace_id, span_id, _flags = parts
            baggage = {}
            tracestate = headers.get(TraceContextPropagator.TRACESTATE_HEADER, "")
            if tracestate:
                for item in tracestate.split(","):
                    if "=" in item:
                        k, v = item.split("=", 1)
                        baggage[k.strip()] = v.strip()
            return SpanContext(
                trace_id=trace_id, span_id=span_id, parent_span_id=span_id, baggage=baggage
            )
        except Exception as e:
            logging.getLogger("distributed_tracing").error(f"Failed to extract trace context: {e}")
            return None


class DistributedTracer:
    """
    Distributed tracing service

    Creates and manages spans across distributed services
    """

    def __init__(
        self,
        service_name: str = "cogniforge",
        sampling_strategy: SamplingStrategy = SamplingStrategy.ALWAYS,
        sampling_rate: float = 1.0,
    ):
        self.service_name = service_name
        self.sampling_strategy = sampling_strategy
        self.sampling_rate = sampling_rate
        self.active_spans: dict[str, Span] = {}
        self.traces: dict[str, Trace] = {}
        self.trace_history: deque = deque(maxlen=1000)
        self.pending_spans: dict[str, list[Span]] = defaultdict(list)
        self.lock = threading.RLock()
        self.metrics = {
            "total_traces": 0,
            "total_spans": 0,
            "traces_with_errors": 0,
            "avg_trace_duration_ms": 0,
        }

    def start_trace(
        self,
        operation_name: str,
        kind: SpanKind = SpanKind.SERVER,
        parent_context: (SpanContext | None) = None,
    ) -> SpanContext:
        """
        Start a new trace or continue existing one

        Returns span context for propagation
        """
        if not self._should_sample():
            return SpanContext(trace_id="not_sampled", span_id="not_sampled")
        if parent_context and parent_context.trace_id != "not_sampled":
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        else:
            trace_id = self._generate_trace_id()
            parent_span_id = None
        span_id = self._generate_span_id()
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            operation_name=operation_name,
            service_name=self.service_name,
            kind=kind,
            start_time=datetime.now(UTC),
            parent_span_id=parent_span_id,
            baggage=parent_context.baggage if parent_context else {},
        )
        with self.lock:
            self.active_spans[span_id] = span
        return SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=span.baggage.copy(),
        )

    def end_span(
        self,
        span_context: SpanContext,
        status_code: str = "OK",
        status_message: (str | None) = None,
    ):
        """End a span"""
        span_id = span_context.span_id
        with self.lock:
            span = self.active_spans.get(span_id)
            if not span:
                return
            span.end_time = datetime.now(UTC)
            span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
            span.status_code = status_code
            span.status_message = status_message
            self.pending_spans[span.trace_id].append(span)
            del self.active_spans[span_id]
            self._try_aggregate_trace(span.trace_id)

    def add_span_tag(
        self, span_context: SpanContext, key: str, value: dict[str, str | int | bool]
    ) -> None:
        """Add tag to span"""
        with self.lock:
            span = self.active_spans.get(span_context.span_id)
            if span:
                span.tags[key] = value

    def add_span_log(
        self, span_context: SpanContext, message: str, fields: (dict[str, Any] | None) = None
    ):
        """Add log event to span"""
        with self.lock:
            span = self.active_spans.get(span_context.span_id)
            if span:
                log_entry = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "message": message,
                    "fields": fields or {},
                }
                span.logs.append(log_entry)

    def add_baggage(self, span_context: SpanContext, key: str, value: str) -> None:
        """Add baggage item (propagated to child spans)"""
        span_context.baggage[key] = value
        with self.lock:
            span = self.active_spans.get(span_context.span_id)
            if span:
                span.baggage[key] = value

    def _try_aggregate_trace(self, trace_id: str):
        """Try to aggregate trace if all spans are complete"""
        with self.lock:
            spans = self.pending_spans.get(trace_id, [])
            if not spans:
                return
            active_for_trace = [s for s in self.active_spans.values() if s.trace_id == trace_id]
            if active_for_trace:
                return
            root_span = min(spans, key=lambda s: s.start_time)
            last_span = max(spans, key=lambda s: s.end_time or s.start_time)
            trace = Trace(
                trace_id=trace_id,
                root_span_id=root_span.span_id,
                service_name=root_span.service_name,
                start_time=root_span.start_time,
                end_time=last_span.end_time,
                duration_ms=(last_span.end_time - root_span.start_time).total_seconds() * 1000
                if last_span.end_time
                else None,
                spans=spans,
                span_count=len(spans),
                error_count=sum(1 for s in spans if s.status_code == "ERROR"),
            )
            self.traces[trace_id] = trace
            self.trace_history.append(trace)
            self.metrics["total_traces"] += 1
            self.metrics["total_spans"] += len(spans)
            if trace.error_count > 0:
                self.metrics["traces_with_errors"] += 1
            del self.pending_spans[trace_id]

    def get_trace(self, trace_id: str) -> Trace | None:
        """Get completed trace"""
        with self.lock:
            return self.traces.get(trace_id)

    def get_recent_traces(self, limit: int = 100) -> list[Trace]:
        """Get recent traces"""
        with self.lock:
            return list(self.trace_history)[-limit:]

    def get_service_dependencies(self) -> dict[str, set[str]]:
        """
        Analyze service dependencies from traces

        Returns mapping of service -> called services
        """
        dependencies = defaultdict(set)
        with self.lock:
            for trace in self.traces.values():
                service_spans = defaultdict(list)
                for span in trace.spans:
                    service_spans[span.service_name].append(span)
                for span in trace.spans:
                    if span.parent_span_id:
                        for parent_span in trace.spans:
                            if (
                                parent_span.span_id == span.parent_span_id
                                and parent_span.service_name != span.service_name
                            ):
                                dependencies[parent_span.service_name].add(span.service_name)
        return {k: list(v) for k, v in dependencies.items()}

    def get_metrics(self) -> dict[str, Any]:
        """Get tracing metrics"""
        with self.lock:
            active_spans_count = len(self.active_spans)
            pending_traces = len(self.pending_spans)
            completed_traces = len(self.traces)
            completed_with_duration = [t for t in self.traces.values() if t.duration_ms is not None]
            avg_duration = (
                sum(t.duration_ms for t in completed_with_duration) / len(completed_with_duration)
                if completed_with_duration
                else 0
            )
            return {
                "active_spans": active_spans_count,
                "pending_traces": pending_traces,
                "completed_traces": completed_traces,
                "total_traces": self.metrics["total_traces"],
                "total_spans": self.metrics["total_spans"],
                "traces_with_errors": self.metrics["traces_with_errors"],
                "avg_trace_duration_ms": avg_duration,
                "error_rate": self.metrics["traces_with_errors"]
                / self.metrics["total_traces"]
                * 100
                if self.metrics["total_traces"] > 0
                else 0,
            }

    def _should_sample(self) -> bool:
        """Determine if trace should be sampled"""
        if self.sampling_strategy == SamplingStrategy.ALWAYS:
            return True
        if self.sampling_strategy == SamplingStrategy.NEVER:
            return False
        if self.sampling_strategy == SamplingStrategy.PROBABILISTIC:
            import random

            return random.random() < self.sampling_rate
        return True

    def _generate_trace_id(self) -> str:
        """Generate unique trace ID (32 hex chars)"""
        return uuid.uuid4().hex

    def _generate_span_id(self) -> str:
        """Generate unique span ID (16 hex chars)"""
        return uuid.uuid4().hex[:16]


_tracer_instance: DistributedTracer | None = None
_tracer_lock = threading.Lock()


def get_distributed_tracer() -> DistributedTracer:
    """Get singleton distributed tracer instance"""
    global _tracer_instance
    if _tracer_instance is None:
        with _tracer_lock:
            if _tracer_instance is None:
                _tracer_instance = DistributedTracer()
    return _tracer_instance
