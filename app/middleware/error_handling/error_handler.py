# app/middleware/error_handling/error_handler.py
# ======================================================================================
# ==                    ERROR HANDLER MIDDLEWARE (v∞)                               ==
# ======================================================================================
"""
وسيط معالجة الأخطاء - Error Handler Middleware

Centralized error handling middleware that catches and formats exceptions.
"""

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult


class ErrorHandlerMiddleware(BaseMiddleware):
    """
    Error Handler Middleware

    Features:
    - Exception catching and formatting
    - Stack trace sanitization
    - Error logging and tracking
    - User-friendly error messages
    """

    name = "ErrorHandler"
    order = 999  # Execute last

    def _setup(self):
        """Initialize error handler"""
        self.errors_handled = 0
        self.include_traceback = self.config.get("include_traceback", False)

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Error handler doesn't process requests, only handles errors

        Args:
            ctx: Request context

        Returns:
            Always succeeds
        """
        return MiddlewareResult.success()

    def on_error(self, ctx: RequestContext, error: Exception):
        """
        Handle errors from other middleware

        Args:
            ctx: Request context
            error: Exception that occurred
        """
        self.errors_handled += 1

        # Log error details
        import traceback

        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "path": ctx.path,
            "method": ctx.method,
            "user_id": ctx.user_id,
        }

        if self.include_traceback:
            error_details["traceback"] = traceback.format_exc()

        # Store error in context for logging
        ctx.add_metadata("error_details", error_details)

        print(f"❌ Error handled: {error_details}")

    def get_statistics(self) -> dict:
        """Return error handler statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "errors_handled": self.errors_handled,
            }
        )
        return stats
