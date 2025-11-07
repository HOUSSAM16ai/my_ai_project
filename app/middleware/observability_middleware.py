# app/middleware/observability_middleware.py
# ======================================================================================
# ==   OBSERVABILITY MIDDLEWARE - AUTOMATIC INSTRUMENTATION                        ==
# ======================================================================================
"""
وسيطة الملاحظية التلقائية - Automatic Observability Middleware

Automatically instruments all Flask requests with:
✅ Distributed tracing (W3C Trace Context)
✅ Metrics collection (Golden Signals)
✅ Structured logging with correlation
✅ Automatic trace propagation
✅ Context enrichment with baggage

Better than:
- OpenTelemetry auto-instrumentation (more lightweight, faster)
- DataDog APM (more features, open standards)
- New Relic (lower overhead, better correlation)
"""

import time
from collections.abc import Callable
from functools import wraps

from flask import Flask, Response, g, request

from app.telemetry.unified_observability import (
    TraceContext,
    get_unified_observability,
)


class ObservabilityMiddleware:
    """
    Middleware for automatic observability instrumentation

    Integrates with Flask request lifecycle:
    - before_request: Start trace, extract context
    - after_request: End trace, record metrics
    - teardown_request: Handle errors
    """

    def __init__(self, app: Flask | None = None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)

    def before_request(self):
        """
        Before request handler

        1. Extract W3C Trace Context from headers
        2. Start new span for this request
        3. Store context in Flask g
        4. Add baggage (user_id, tenant_id, etc.)
        """
        obs = get_unified_observability()

        # Extract parent context from headers
        parent_context = TraceContext.from_headers(dict(request.headers))

        # Start trace
        operation_name = f"{request.method} {request.endpoint or request.path}"
        tags = {
            "http.method": request.method,
            "http.url": request.url,
            "http.path": request.path,
            "http.scheme": request.scheme,
            "http.host": request.host,
            "http.user_agent": request.headers.get("User-Agent", ""),
        }

        trace_context = obs.start_trace(
            operation_name=operation_name,
            parent_context=parent_context,
            tags=tags,
        )

        # Store in Flask g
        g.trace_context = trace_context
        g.request_start_time = time.time()

        # Add baggage enrichment
        try:
            from flask_login import current_user

            if current_user.is_authenticated:
                obs.set_baggage("user_id", str(current_user.id))
                obs.set_baggage("user_email", current_user.email)
        except Exception:
            pass

        # Log request start
        obs.log(
            level="INFO",
            message=f"Request started: {operation_name}",
            context={
                "method": request.method,
                "path": request.path,
                "query_params": dict(request.args),
                "remote_addr": request.remote_addr,
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

    def after_request(self, response: Response) -> Response:
        """
        After request handler

        1. End span
        2. Record metrics (latency, status code)
        3. Add trace headers to response
        4. Log request completion
        """
        if not hasattr(g, "trace_context"):
            return response

        obs = get_unified_observability()
        trace_context = g.trace_context
        duration = time.time() - g.request_start_time
        duration_ms = duration * 1000

        # Determine status
        status = "OK" if response.status_code < 400 else "ERROR"

        # End span
        obs.end_span(
            span_id=trace_context.span_id,
            status=status,
            metrics={
                "http.status_code": response.status_code,
                "http.response_size": response.content_length or 0,
                "duration_ms": duration_ms,
            },
        )

        # Record metrics
        obs.record_metric(
            name="http.request.duration_seconds",
            value=duration,
            labels={
                "method": request.method,
                "endpoint": request.endpoint or "unknown",
                "status": str(response.status_code),
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

        obs.increment_counter(
            name="http.requests.total",
            labels={
                "method": request.method,
                "endpoint": request.endpoint or "unknown",
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

        # Add trace headers to response
        trace_headers = trace_context.to_headers()
        for key, value in trace_headers.items():
            response.headers[key] = value

        # Add custom headers
        response.headers["X-Trace-Id"] = trace_context.trace_id
        response.headers["X-Span-Id"] = trace_context.span_id

        # Log request completion
        obs.log(
            level="INFO",
            message=f"Request completed: {request.method} {request.path}",
            context={
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "response_size": response.content_length or 0,
            },
            trace_id=trace_context.trace_id,
            span_id=trace_context.span_id,
        )

        return response

    def teardown_request(self, exception: Exception | None = None):
        """
        Teardown request handler

        Handle errors and exceptions
        """
        if exception and hasattr(g, "trace_context"):
            obs = get_unified_observability()
            trace_context = g.trace_context

            # Log exception
            obs.log(
                level="ERROR",
                message=f"Request failed with exception: {str(exception)}",
                context={
                    "exception_type": type(exception).__name__,
                    "method": request.method,
                    "path": request.path,
                },
                exception=exception,
                trace_id=trace_context.trace_id,
                span_id=trace_context.span_id,
            )

            # Add event to span
            obs.add_span_event(
                span_id=trace_context.span_id,
                event_name="exception",
                attributes={
                    "exception.type": type(exception).__name__,
                    "exception.message": str(exception),
                },
            )


def monitor_function(operation_name: str | None = None):
    """
    Decorator to monitor specific functions with tracing

    Usage:
        @monitor_function("database_query")
        def query_database(query):
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            obs = get_unified_observability()

            # Get parent context from Flask g if available
            parent_context = (
                getattr(g, "trace_context", None) if hasattr(g, "trace_context") else None
            )

            # Start span
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            context = obs.start_trace(
                operation_name=op_name,
                parent_context=parent_context,
                tags={
                    "function.name": func.__name__,
                    "function.module": func.__module__,
                },
            )

            start_time = time.time()
            error = None
            result = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # End span
                obs.end_span(
                    span_id=context.span_id,
                    status="ERROR" if error else "OK",
                    error_message=str(error) if error else None,
                    metrics={"duration_ms": duration_ms},
                )

                # Log
                obs.log(
                    level="ERROR" if error else "DEBUG",
                    message=f"Function {'failed' if error else 'completed'}: {op_name}",
                    context={
                        "duration_ms": duration_ms,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                    exception=error,
                    trace_id=context.trace_id,
                    span_id=context.span_id,
                )

        return wrapper

    return decorator


def monitor_database_query():
    """
    Decorator to monitor database queries

    Usage:
        @monitor_database_query()
        def execute_query(query):
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            obs = get_unified_observability()
            parent_context = (
                getattr(g, "trace_context", None) if hasattr(g, "trace_context") else None
            )

            # Start span
            context = obs.start_trace(
                operation_name=f"db.query.{func.__name__}",
                parent_context=parent_context,
                tags={
                    "db.system": "postgresql",
                    "db.operation": "query",
                },
            )

            start_time = time.time()
            error = None

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                # Record database metric
                obs.record_metric(
                    name="db.query.duration_seconds",
                    value=duration_ms / 1000,
                    labels={"operation": func.__name__},
                    trace_id=context.trace_id,
                    span_id=context.span_id,
                )

                obs.end_span(
                    span_id=context.span_id,
                    status="ERROR" if error else "OK",
                    error_message=str(error) if error else None,
                    metrics={"duration_ms": duration_ms},
                )

        return wrapper

    return decorator


def monitor_external_call(service_name: str):
    """
    Decorator to monitor external API calls

    Usage:
        @monitor_external_call("payment-gateway")
        def call_payment_api():
            # Your code here
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            obs = get_unified_observability()
            parent_context = (
                getattr(g, "trace_context", None) if hasattr(g, "trace_context") else None
            )

            # Start span
            context = obs.start_trace(
                operation_name=f"http.client.{service_name}",
                parent_context=parent_context,
                tags={
                    "http.client": service_name,
                    "service.name": service_name,
                },
            )

            start_time = time.time()
            error = None

            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000

                obs.record_metric(
                    name="http.client.duration_seconds",
                    value=duration_ms / 1000,
                    labels={"service": service_name},
                    trace_id=context.trace_id,
                    span_id=context.span_id,
                )

                obs.end_span(
                    span_id=context.span_id,
                    status="ERROR" if error else "OK",
                    error_message=str(error) if error else None,
                    metrics={"duration_ms": duration_ms},
                )

        return wrapper

    return decorator
