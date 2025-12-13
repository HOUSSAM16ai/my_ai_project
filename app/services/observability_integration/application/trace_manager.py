"""
Trace Manager - Application Service
"""

import uuid
from datetime import UTC, datetime

from ..domain.models import Span, TraceStatus
from ..domain.ports import ITraceExporter


class TraceManager:
    """Manages distributed tracing"""

    def __init__(self, exporter: ITraceExporter):
        self._exporter = exporter

    def start_span(
        self,
        operation_name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Span:
        """Start a new span"""
        span = Span(
            span_id=str(uuid.uuid4()),
            trace_id=trace_id or str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.now(UTC),
        )
        return span

    def finish_span(self, span: Span, status: TraceStatus = TraceStatus.OK) -> None:
        """Finish a span and export it"""
        span.end_time = datetime.now(UTC)
        span.status = status
        self._exporter.export_span(span)

    def add_span_tag(self, span: Span, key: str, value: str) -> None:
        """Add a tag to a span"""
        span.tags[key] = value

    def add_span_log(self, span: Span, message: str, **kwargs) -> None:
        """Add a log entry to a span"""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": message,
            **kwargs,
        }
        span.logs.append(log_entry)

    def get_trace(self, trace_id: str) -> list[Span]:
        """Get all spans for a trace"""
        return self._exporter.get_trace(trace_id)
