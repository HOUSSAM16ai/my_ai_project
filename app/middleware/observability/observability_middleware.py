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
        بدء التتبع وجمع بيانات الطلب
        Start trace and collect request metadata

        Args:
            ctx: Request context

        Returns:
            Always succeeds
        """
        self.traces_started += 1

        # استخراج سياق الأصل | Extract parent context
        parent_context = self._extract_parent_context(ctx)

        # بدء التتبع | Start trace
        trace_context = self._start_trace(ctx, parent_context)

        # تحديث السياق | Update context
        ctx.set_trace_context(trace_context.trace_id, trace_context.span_id)
        ctx.add_metadata("observability_start_time", time.time())
        ctx.add_metadata("trace_context", trace_context)

        # تسجيل بداية الطلب | Log request start
        self._log_request_start(ctx, trace_context)

        return MiddlewareResult.success()

    def _extract_parent_context(self, ctx: RequestContext) -> TraceContext | None:
        """استخراج سياق التتبع الأصلي من الترويسات | Extract parent trace context from headers"""
        traceparent = ctx.get_header("traceparent")
        tracestate = ctx.get_header("tracestate")

        if traceparent:
            return TraceContext.from_headers(
                {"traceparent": traceparent, "tracestate": tracestate or ""}
            )
        return None

    def _start_trace(self, ctx: RequestContext, parent_context: TraceContext | None) -> TraceContext:
        """بدء تتبع جديد | Start new trace"""
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

        return self.obs.start_trace(
            operation_name=operation_name,
            parent_context=parent_context,
            tags=tags,
        )

    def _log_request_start(self, ctx: RequestContext, trace_context: TraceContext) -> None:
        """تسجيل بداية الطلب | Log request start"""
        operation_name = f"{ctx.method} {ctx.path}"
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

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """
        انتهاء التتبع وتسجيل المقاييس
        End trace and record metrics

        Args:
            ctx: Request context
            result: Middleware result
        """
        # استرجاع البيانات الأساسية | Get basic data
        start_time = ctx.get_metadata("observability_start_time")
        trace_context = ctx.get_metadata("trace_context")

        if not start_time or not trace_context:
            return

        # حساب المدة والحالة | Calculate duration and status
        duration_ms = self._calculate_duration(start_time)
        status, status_code = self._determine_status(result)

        # إنهاء التتبع | End tracing
        self._end_trace_span(trace_context, status, status_code, duration_ms)

        # تسجيل المقاييس | Record metrics
        self._record_request_metrics(ctx, trace_context, duration_ms, status_code, result.is_success)

        # تسجيل الإكمال | Log completion
        self._log_completion(ctx, trace_context, status_code, duration_ms, result.is_success)

    def _calculate_duration(self, start_time: float) -> float:
        """حساب مدة الطلب بالملي ثانية | Calculate request duration in ms"""
        duration = time.time() - start_time
        return duration * 1000

    def _determine_status(self, result: MiddlewareResult) -> tuple[str, int]:
        """تحديد الحالة ورمز الحالة | Determine status and status code"""
        status = "OK" if result.is_success else "ERROR"
        status_code = result.status_code
        return status, status_code

    def _end_trace_span(
        self, trace_context: TraceContext, status: str, status_code: int, duration_ms: float
    ) -> None:
        """إنهاء نطاق التتبع | End trace span"""
        self.obs.end_span(
            span_id=trace_context.span_id,
            status=status,
            metrics={
                "http.status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

    def _record_request_metrics(
        self,
        ctx: RequestContext,
        trace_context: TraceContext,
        duration_ms: float,
        status_code: int,
        is_success: bool,
    ) -> None:
        """تسجيل مقاييس الطلب | Record request metrics"""
        # مدة الطلب | Request duration
        self.obs.record_metric(
            name="http.request.duration_seconds",
            value=duration_ms / 1000,
            labels={
                "method": ctx.method,
                "endpoint": ctx.path,
                "status": str(status_code),
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

        # إجمالي الطلبات | Total requests
        self.obs.increment_counter(
            name="http.requests.total",
            labels={
                "method": ctx.method,
                "endpoint": ctx.path,
                "status": str(status_code),
            },
        )

        # إجمالي الأخطاء | Total errors
        if not is_success:
            self.obs.increment_counter(
                name="http.errors.total",
                labels={
                    "method": ctx.method,
                    "status": str(status_code),
                },
            )

    def _log_completion(
        self,
        ctx: RequestContext,
        trace_context: TraceContext,
        status_code: int,
        duration_ms: float,
        is_success: bool,
    ) -> None:
        """تسجيل اكتمال الطلب | Log request completion"""
        self.obs.log(
            level="ERROR" if not is_success else "INFO",
            message=f"Request completed: {ctx.method} {ctx.path}",
            context={
                "status_code": status_code,
                "duration_ms": duration_ms,
                "success": is_success,
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

    def on_error(self, ctx: RequestContext, error: Exception) -> None:
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
