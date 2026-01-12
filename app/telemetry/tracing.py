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
        self.stats = {"traces_started": 0, "traces_completed": 0, "spans_created": 0}

        # Dependency tracking
        self.service_dependencies: dict[str, set[str]] = {}  # Will be re-computed or updated

    def start_trace(
        self,
        operation_name: str,
        parent_context: TraceContext | None = None,
        tags: dict[str, object] | None = None,
        request: Request | None = None,
    ) -> TraceContext:
        """
        Start a new trace or child span.
        بدء تتبع جديد أو span فرعي.
        """
        # Initialize trace parameters
        trace_params = self._initialize_trace_params(parent_context)

        # Create span
        span = self._create_span(operation_name, trace_params, tags or {})

        # Register span and trace
        self._register_span_and_trace(span, trace_params)

        # Create and attach context
        context = self._create_trace_context(trace_params, span)
        if request:
            self._attach_context_to_request(request, context, span.span_id)

        return context

    def _initialize_trace_params(self, parent_context: TraceContext | None) -> dict[str, object]:
        """
        Initialize trace parameters from parent context or create new.
        تهيئة معاملات التتبع من السياق الأصلي أو إنشاء جديدة.
        """
        if parent_context:
            return {
                "sampled": parent_context.sampled,
                "trace_id": parent_context.trace_id,
                "parent_span_id": parent_context.span_id,
                "baggage": parent_context.baggage.copy(),
            }
        return {
            "sampled": self._head_based_sampling(),
            "trace_id": self._generate_trace_id(),
            "parent_span_id": None,
            "baggage": {},
        }

    def _create_span(
        self, operation_name: str, trace_params: dict[str, object], tags: dict[str, object]
    ) -> UnifiedSpan:
        """
        Create a new span with given parameters.
        إنشاء span جديد بالمعاملات المحددة.
        """
        span_id = self._generate_span_id()
        return UnifiedSpan(
            trace_id=trace_params["trace_id"],
            span_id=span_id,
            parent_span_id=trace_params["parent_span_id"],
            operation_name=operation_name,
            service_name=self.service_name,
            start_time=time.time(),
            tags=tags,
            baggage=trace_params["baggage"],
        )

    def _register_span_and_trace(self, span: UnifiedSpan, trace_params: dict[str, object]) -> None:
        """
        Register span and trace in active collections.
        تسجيل span والتتبع في المجموعات النشطة.
        """
        with self.lock:
            self.active_spans[span.span_id] = span

            if trace_params["parent_span_id"] is None:
                # Root span - create new trace
                trace = UnifiedTrace(
                    trace_id=span.trace_id, root_span=span, start_time=span.start_time
                )
                trace.spans.append(span)
                self.active_traces[span.trace_id] = trace
                self.stats["traces_started"] += 1
            elif span.trace_id in self.active_traces:
                # Child span - add to existing trace
                self.active_traces[span.trace_id].spans.append(span)

            self.stats["spans_created"] += 1

    def _create_trace_context(
        self, trace_params: dict[str, object], span: UnifiedSpan
    ) -> TraceContext:
        """
        Create trace context object.
        إنشاء كائن سياق التتبع.
        """
        return TraceContext(
            trace_id=trace_params["trace_id"],
            span_id=span.span_id,
            parent_span_id=trace_params["parent_span_id"],
            sampled=trace_params["sampled"],
            baggage=trace_params["baggage"],
        )

    def _attach_context_to_request(
        self, request: Request, context: TraceContext, span_id: str
    ) -> None:
        """
        Attach trace context to request object.
        إرفاق سياق التتبع بكائن الطلب.
        """
        request.state.trace_context = context
        request.state.current_span_id = span_id

    def end_span(
        self,
        span_id: str,
        status: str = "OK",
        error_message: str | None = None,
        metrics: dict[str, float] | None = None,
    ) -> UnifiedTrace | None:
        """
        End a span and return completed trace if applicable.
        إنهاء span وإرجاع التتبع المكتمل إن أمكن.

        Returns the Trace object if the trace is completed, else None.
        """
        with self.lock:
            if span_id not in self.active_spans:
                return None

            # Finalize span
            span = self._finalize_span(span_id, status, error_message, metrics)

            # Process trace completion
            completed_trace = self._process_trace_completion(span)

            # Cleanup
            del self.active_spans[span_id]

            return completed_trace

    def _finalize_span(
        self,
        span_id: str,
        status: str,
        error_message: str | None,
        metrics: dict[str, float] | None,
    ) -> UnifiedSpan:
        """
        Finalize span with status and metrics.
        إنهاء span بالحالة والمقاييس.
        """
        span = self.active_spans[span_id]
        span.end_time = time.time()
        span.finalize()
        span.status = status
        span.error_message = error_message
        if metrics:
            span.metrics.update(metrics)
        return span

    def _process_trace_completion(self, span: UnifiedSpan) -> UnifiedTrace | None:
        """
        Process trace completion if this is root span.
        معالجة إكمال التتبع إذا كان هذا span جذري.
        """
        trace = self.active_traces.get(span.trace_id)
        if not trace:
            return None

        # Update error count
        if span.status == "ERROR":
            trace.error_count += 1

        # Check if root span
        if span.span_id == trace.root_span.span_id:
            return self._complete_trace(trace, span)

        return None

    def _complete_trace(self, trace: UnifiedTrace, root_span: UnifiedSpan) -> UnifiedTrace | None:
        """
        Complete trace and apply tail-based sampling.
        إكمال التتبع وتطبيق العينات المتأخرة.
        """
        trace.end_time = root_span.end_time
        trace.total_duration_ms = root_span.duration_ms
        trace.analyze_critical_path()

        if self._tail_based_sampling(trace):
            self.completed_traces.append(trace)
            self.stats["traces_completed"] += 1
            completed_trace = trace
        else:
            completed_trace = None

        del self.active_traces[trace.trace_id]
        return completed_trace

    def add_span_event(
        self, span_id: str, event_name: str, attributes: dict[str, object] | None = None
    ) -> None:
        with self.lock:
            if span_id in self.active_spans:
                event = {
                    "timestamp": time.time(),
                    "name": event_name,
                    "attributes": attributes or {},
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
