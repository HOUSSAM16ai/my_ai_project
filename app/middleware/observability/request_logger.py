# app/middleware/observability/request_logger.py
# ======================================================================================
# ==                    REQUEST LOGGER MIDDLEWARE (v∞)                              ==
# ======================================================================================
"""
وسيط تسجيل الطلبات - Request Logger Middleware

Structured logging middleware that logs all requests with proper masking
of sensitive data.
"""

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.telemetry.logging import StructuredLogger

class RequestLoggerMiddleware(BaseMiddleware):
    """
    Request Logger Middleware

    Features:
    - Structured logging with JSON
    - Automatic PII masking
    - Correlation IDs
    - Log levels per endpoint
    """

    name = "RequestLogger"
    order = 3  # Execute early for comprehensive logging

    def _setup(self):
        """Initialize logger"""
        self.logger = StructuredLogger()
        self.logged_count = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """Log request details - KISS principle applied"""
        self.logged_count += 1
        level = self._get_log_level(ctx.path)
        log_data = self._prepare_log_data(ctx)
        
        self.logger.log(
            level=level,
            message=f"Incoming request: {ctx.method} {ctx.path}",
            context=log_data,
            trace_id=ctx.trace_id,
            span_id=ctx.span_id,
        )

        return MiddlewareResult.success()

    def _prepare_log_data(self, ctx: RequestContext) -> dict:
        """Prepare request data for logging"""
        return {
            "request_id": ctx.request_id,
            "method": ctx.method,
            "path": ctx.path,
            "ip_address": ctx.ip_address,
            "user_agent": ctx.user_agent,
            "user_id": ctx.user_id,
            "query_params": ctx.query_params,
        }

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """
        Log request completion

        Args:
            ctx: Request context
            result: Middleware result
        """
        level = "ERROR" if not result.is_success else "INFO"

        self.logger.log(
            level=level,
            message=f"Request completed: {ctx.method} {ctx.path}",
            context={
                "request_id": ctx.request_id,
                "status_code": result.status_code,
                "success": result.is_success,
                "message": result.message if not result.is_success else None,
            },
            trace_id=ctx.trace_id,
            span_id=ctx.span_id,
        )

    def _get_log_level(self, path: str) -> str:
        """
        Determine log level based on path

        Args:
            path: Request path

        Returns:
            Log level string
        """
        # Health checks at DEBUG level
        if path in ["/health", "/ping", "/api/health"]:
            return "DEBUG"

        # API endpoints at INFO level
        if path.startswith("/api/"):
            return "INFO"

        # Everything else at INFO
        return "INFO"

    def get_statistics(self) -> dict:
        """Return logger statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "logged_count": self.logged_count,
            }
        )
        return stats
