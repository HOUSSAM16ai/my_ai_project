# app/middleware/fastapi_observability.py
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.telemetry.unified_observability import TraceContext, get_unified_observability


class FastAPIObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> None:
        """
        معالج الطلبات مع المراقبة الشاملة.
        Request handler with comprehensive observability.
        """
        obs = get_unified_observability()

        # 1. إعداد التتبع | Setup tracing
        trace_context = self._setup_trace_context(obs, request)
        self._attach_trace_to_request(request, trace_context)

        # 2. تسجيل بداية الطلب | Log request start
        self._log_request_start(obs, request, trace_context)

        # 3. معالجة الطلب | Process request
        response = await call_next(request)

        # 4. حساب المدة | Calculate duration
        duration = time.time() - request.state.request_start_time

        # 5. إنهاء التتبع | End tracing
        self._finalize_trace(obs, trace_context, response, duration)

        # 6. تسجيل المقاييس | Record metrics
        self._record_request_metrics(obs, request, response, duration, trace_context)

        # 7. إضافة رؤوس التتبع | Add trace headers
        self._add_trace_headers(response, trace_context)

        # 8. تسجيل إكمال الطلب | Log request completion
        self._log_request_completion(obs, request, response, duration, trace_context)

        return response

    def _setup_trace_context(self, obs, request: Request) -> TraceContext:
        """
        إعداد سياق التتبع من رؤوس الطلب.
        Setup trace context from request headers.
        """
        parent_context = TraceContext.from_headers(dict(request.headers))
        operation_name = f"{request.method} {request.url.path}"
        tags = self._extract_request_tags(request)

        return obs.start_trace(
            operation_name=operation_name,
            parent_context=parent_context,
            tags=tags,
        )

    def _extract_request_tags(self, request: Request) -> dict[str, str]:
        """
        استخراج وسوم الطلب للتتبع.
        Extract request tags for tracing.
        """
        return {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.path": request.url.path,
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "http.user_agent": request.headers.get("User-Agent", ""),
        }

    def _attach_trace_to_request(self, request: Request, trace_context: TraceContext) -> None:
        """
        إرفاق سياق التتبع ووقت البداية بالطلب.
        Attach trace context and start time to request.
        """
        request.state.trace_context = trace_context
        request.state.request_start_time = time.time()

    def _log_request_start(self, obs, request: Request, trace_context: TraceContext) -> None:
        """
        تسجيل بداية الطلب.
        Log request start with context.
        """
        operation_name = f"{request.method} {request.url.path}"
        obs.log(
            level="INFO",
            message=f"Request started: {operation_name}",
            context={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "remote_addr": request.client.host,
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

    def _finalize_trace(self, obs, trace_context: TraceContext, response, duration: float) -> None:
        """
        إنهاء التتبع مع الحالة والمقاييس.
        Finalize trace span with status and metrics.
        """
        status = "OK" if response.status_code < 400 else "ERROR"
        duration_ms = duration * 1000

        obs.end_span(
            span_id=trace_context.span_id,
            status=status,
            metrics={
                "http.status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

    def _record_request_metrics(
        self, obs, request: Request, response, duration: float, trace_context: TraceContext
    ) -> None:
        """
        تسجيل مقاييس الطلب.
        Record request metrics and counters.
        """
        labels = {
            "method": request.method,
            "endpoint": request.url.path,
            "status": str(response.status_code),
        }

        # تسجيل مدة الطلب | Record duration
        obs.record_metric(
            name="http.request.duration_seconds",
            value=duration,
            labels=labels,
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

        # عداد إجمالي الطلبات | Total requests counter
        obs.increment_counter(name="http.requests.total", labels=labels)

        # عداد الأخطاء | Errors counter
        if response.status_code >= 400:
            obs.increment_counter(
                name="http.errors.total",
                labels={
                    "method": request.method,
                    "status": str(response.status_code),
                },
            )

    def _add_trace_headers(self, response, trace_context: TraceContext) -> None:
        """
        إضافة رؤوس التتبع إلى الاستجابة.
        Add trace headers to response.
        """
        trace_headers = trace_context.to_headers()
        for key, value in trace_headers.items():
            response.headers[key] = value

        response.headers["X-Trace-Id"] = trace_context.trace_id
        response.headers["X-Span-Id"] = trace_context.span_id

    def _log_request_completion(
        self, obs, request: Request, response, duration: float, trace_context: TraceContext
    ) -> None:
        """
        تسجيل إكمال الطلب.
        Log request completion with metrics.
        """
        obs.log(
            level="INFO",
            message=f"Request completed: {request.method} {request.url.path}",
            context={
                "status_code": response.status_code,
                "duration_ms": duration * 1000,
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )
