# app/middleware/cors/cors_middleware.py
# ======================================================================================
# ==                    CORS MIDDLEWARE (v∞)                                        ==
# ======================================================================================
"""
وسيط CORS - CORS Middleware

Handles Cross-Origin Resource Sharing with the new architecture.
"""

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult


class CORSMiddleware(BaseMiddleware):
    """
    CORS Middleware

    Manages Cross-Origin Resource Sharing headers.
    """

    name = "CORS"
    order = 101  # Execute after security headers

    def _setup(self):
        """Initialize CORS configuration"""
        self.allowed_origins = self.config.get(
            "allowed_origins",
            ["http://localhost:5000", "http://localhost:3000"],
        )
        self.allowed_methods = self.config.get(
            "allowed_methods",
            ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        )
        self.allowed_headers = self.config.get(
            "allowed_headers",
            ["Content-Type", "Authorization", "X-API-Key"],
        )
        self.max_age = self.config.get("max_age", 3600)

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Store CORS headers in context

        Args:
            ctx: Request context

        Returns:
            Always succeeds
        """
        cors_headers = {
            "Access-Control-Allow-Origin": "*",  # Or check origin
            "Access-Control-Allow-Methods": ", ".join(self.allowed_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allowed_headers),
            "Access-Control-Max-Age": str(self.max_age),
        }

        ctx.add_metadata("cors_headers", cors_headers)

        return MiddlewareResult.success()
