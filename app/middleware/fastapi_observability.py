# app/middleware/fastapi_observability.py
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.telemetry.unified_observability import (
    TraceContext,
    get_unified_observability,
)


class FastAPIObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        obs = get_unified_observability()
        parent_context = TraceContext.from_headers(dict(request.headers))
        operation_name = f"{request.method} {request.url.path}"
        tags = {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.path": request.url.path,
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "http.user_agent": request.headers.get("User-Agent", ""),
        }
        trace_context = obs.start_trace(
            operation_name=operation_name,
            parent_context=parent_context,
            tags=tags,
        )

        request.state.trace_context = trace_context
        request.state.request_start_time = time.time()

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

        response = await call_next(request)

        duration = time.time() - request.state.request_start_time
        duration_ms = duration * 1000

        status = "OK" if response.status_code < 400 else "ERROR"

        obs.end_span(
            span_id=trace_context.span_id,
            status=status,
            metrics={
                "http.status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        obs.record_metric(
            name="http.request.duration_seconds",
            value=duration,
            labels={
                "method": request.method,
                "endpoint": request.url.path,
                "status": str(response.status_code),
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

        obs.increment_counter(
            name="http.requests.total",
            labels={
                "method": request.method,
                "endpoint": request.url.path,
                "status": str(response.status_code),
            },
        )

        if response.status_code >= 400:
            obs.increment_counter(
                name="http.errors.total",
                labels={
                    "method": request.method,
                    "status": str(response.status_code),
                },
            )

        trace_headers = trace_context.to_headers()
        for key, value in trace_headers.items():
            response.headers[key] = value

        response.headers["X-Trace-Id"] = trace_context.trace_id
        response.headers["X-Span-Id"] = trace_context.span_id

        obs.log(
            level="INFO",
            message=f"Request completed: {request.method} {request.url.path}",
            context={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

        return response
