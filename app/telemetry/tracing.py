from __future__ import annotations

import logging
import threading
import time
import uuid
from collections import deque

from fastapi import Request

from app.telemetry.models import TraceContext, UnifiedSpan, UnifiedTrace

logger = logging.getLogger(__name__)

class TracingManager:
    def __init__(self, service_name: str, sample_rate: float, sla_target_ms: float):
        self.service_name = service_name
        self.sample_rate = sample_rate
        self.sla_target_ms = sla_target_ms
        self.active_traces: dict[str, UnifiedTrace] = {}
        self.active_spans: dict[str, UnifiedSpan] = {}
        self.completed_traces: deque[UnifiedTrace] = deque(maxlen=10000)
        self.lock = threading.RLock()
        self.stats = {'traces_started': 0, 'traces_completed': 0, 'spans_created': 0}

        # Dependency tracking
        self.service_dependencies: dict[str, set[str]] = {} # Will be re-computed or updated

    # TODO: Split this function (49 lines) - KISS principle
    def start_trace(self, operation_name: str, parent_context: TraceContext | None = None,
                    tags: dict[str, Any] | None = None, request: Request | None = None) -> TraceContext:
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
        span = UnifiedSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=self.service_name,
            start_time=time.time(),
            tags=tags or {},
            baggage=baggage
        )

        with self.lock:
            self.active_spans[span_id] = span
            if parent_span_id is None:
                trace = UnifiedTrace(trace_id=trace_id, root_span=span, start_time=span.start_time)
                trace.spans.append(span)
                self.active_traces[trace_id] = trace
                self.stats['traces_started'] += 1
            elif trace_id in self.active_traces:
                self.active_traces[trace_id].spans.append(span)

            self.stats['spans_created'] += 1

        context = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            sampled=head_sampled,
            baggage=baggage
        )

        if request:
            request.state.trace_context = context
            request.state.current_span_id = span_id

        return context
# TODO: Split this function (38 lines) - KISS principle

    def end_span(self, span_id: str, status: str = 'OK', error_message: str | None = None,
                 metrics: dict[str, float] | None = None) -> UnifiedTrace | None:
        """
        Ends a span. Returns the Trace object if the trace is completed, else None.
        """
        with self.lock:
            if span_id not in self.active_spans:
                return None

            span = self.active_spans[span_id]
            span.end_time = time.time()
            span.finalize()
            span.status = status
            span.error_message = error_message
            if metrics:
                span.metrics.update(metrics)

            trace = self.active_traces.get(span.trace_id)
            completed_trace = None

            if trace:
                if status == 'ERROR':
                    trace.error_count += 1

                # Check if this is the root span
                if span.span_id == trace.root_span.span_id:
                    trace.end_time = span.end_time
                    trace.total_duration_ms = span.duration_ms
                    trace.analyze_critical_path()

                    if self._tail_based_sampling(trace):
                        self.completed_traces.append(trace)
                        self.stats['traces_completed'] += 1
                        completed_trace = trace

                    del self.active_traces[span.trace_id]

            del self.active_spans[span_id]
            return completed_trace

    def add_span_event(self, span_id: str, event_name: str, attributes: dict[str, Any] | None = None) -> None:
        with self.lock:
            if span_id in self.active_spans:
                event = {
                    'timestamp': time.time(),
                    'name': event_name,
                    'attributes': attributes or {}
                }
                self.active_spans[span_id].events.append(event)

    def _head_based_sampling(self) -> bool:
        import random
        return random.random() < self.sample_rate

    def _tail_based_sampling(self, trace: UnifiedTrace) -> bool:
        import random
        if trace.error_count > 0:
            return True
        if trace.total_duration_ms and trace.total_duration_ms > self.sla_target_ms * 2:
            return True
        return random.random() < self.sample_rate

    def _generate_trace_id(self) -> str:
        return uuid.uuid4().hex + uuid.uuid4().hex[:16]

    def _generate_span_id(self) -> str:
        return uuid.uuid4().hex[:16]
