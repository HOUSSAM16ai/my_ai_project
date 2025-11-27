# app/middleware/observability/observability_middleware.py
# ======================================================================================
# ==                    OBSERVABILITY MIDDLEWARE ADAPTER (v∞)                       ==
# ======================================================================================
"""
وسيط المراقبة - Observability Middleware

Main observability middleware that integrates tracing, metrics, and logging.
Adapts the existing observability system to the new architecture.
"""

import time

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.telemetry.unified_observability import TraceContext, get_unified_observability


class ObservabilityMiddleware(BaseMiddleware):
    """
    Unified Observability Middleware

    Features:
    - Distributed tracing (W3C Trace Context)
    - Metrics collection (Golden Signals)
    - Structured logging with correlation
    - Automatic instrumentation
    """

    name = "Observability"
    order = 2  # Execute early but after telemetry guard

    def _setup(self):
        """Initialize observability system"""
        self.obs = get_unified_observability()
        self.traces_started = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Start trace and collect request metadata

        Args:
            ctx: Request context

        Returns:
            Always succeeds
        """
        self.traces_started += 1

        # Extract parent context from headers if available
        parent_context = None
        traceparent = ctx.get_header("traceparent")
        tracestate = ctx.get_header("tracestate")

        if traceparent:
            parent_context = TraceContext.from_headers(
                {"traceparent": traceparent, "tracestate": tracestate or ""}
            )

        # Start trace
        operation_name = f"{ctx.method} {ctx.path}"
        tags = {
            "http.method": ctx.method,
            "http.url": f"{ctx.path}",
            "http.path": ctx.path,
            "http.user_agent": ctx.user_agent,
            "http.client_ip": ctx.ip_address,
        }

        if ctx.user_id:
            tags["user.id"] = ctx.user_id

        trace_context = self.obs.start_trace(
            operation_name=operation_name,
            parent_context=parent_context,
            tags=tags,
        )

        # Update request context with trace IDs
        ctx.set_trace_context(trace_context.trace_id, trace_context.span_id)

        # Store start time
        ctx.add_metadata("observability_start_time", time.time())
        ctx.add_metadata("trace_context", trace_context)

        # Log request start
        self.obs.log(
            level="INFO",
            message=f"Request started: {operation_name}",
            context={
                "method": ctx.method,
                "path": ctx.path,
                "ip_address": ctx.ip_address,
                "user_id": ctx.user_id,
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

        return MiddlewareResult.success()

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult):
        """
        End trace and record metrics

        Args:
            ctx: Request context
            result: Middleware result
        """
        start_time = ctx.get_metadata("observability_start_time")
        trace_context = ctx.get_metadata("trace_context")

        if not start_time or not trace_context:
            return

        # Calculate duration
        duration = time.time() - start_time
        duration_ms = duration * 1000

        # Determine status
        status = "OK" if result.is_success else "ERROR"
        status_code = result.status_code

        # End span
        self.obs.end_span(
            span_id=trace_context.span_id,
            status=status,
            metrics={
                "http.status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

        # Record metrics
        self.obs.record_metric(
            name="http.request.duration_seconds",
            value=duration,
            labels={
                "method": ctx.method,
                "endpoint": ctx.path,
                "status": str(status_code),
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

        self.obs.increment_counter(
            name="http.requests.total",
            labels={
                "method": ctx.method,
                "endpoint": ctx.path,
                "status": str(status_code),
            },
        )

        if not result.is_success:
            self.obs.increment_counter(
                name="http.errors.total",
                labels={
                    "method": ctx.method,
                    "status": str(status_code),
                },
            )

        # Log completion
        self.obs.log(
            level="ERROR" if not result.is_success else "INFO",
            message=f"Request completed: {ctx.method} {ctx.path}",
            context={
                "status_code": status_code,
                "duration_ms": duration_ms,
                "success": result.is_success,
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

    def on_error(self, ctx: RequestContext, error: Exception):
        """
        Log errors and add to trace

        Args:
            ctx: Request context
            error: Exception that occurred
        """
        trace_context = ctx.get_metadata("trace_context")

        if trace_context:
            # Log exception
            self.obs.log(
                level="ERROR",
                message=f"Request failed: {error!s}",
                context={
                    "exception_type": type(error).__name__,
                    "method": ctx.method,
                    "path": ctx.path,
                },
                exception=error,
                trace_id=trace_context.trace_id,
                span_id=trace_context.span_id,
            )

            # Add event to span
            self.obs.add_span_event(
                span_id=trace_context.span_id,
                event_name="exception",
                attributes={
                    "exception.type": type(error).__name__,
                    "exception.message": str(error),
                },
            )

    def get_statistics(self) -> dict:
        """Return observability statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "traces_started": self.traces_started,
            }
        )
        return stats
