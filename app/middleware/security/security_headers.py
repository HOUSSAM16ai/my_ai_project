# app/middleware/security/security_headers.py
# ======================================================================================
# ==                    SECURITY HEADERS MIDDLEWARE (v∞)                            ==
# ======================================================================================
"""
وسيط رؤوس الأمان - Security Headers Middleware

Adds comprehensive security headers to all responses.
Implements OWASP best practices for HTTP security headers.
"""


from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult


class SecurityHeadersMiddleware(BaseMiddleware):
    """
    Security Headers Middleware

    Adds critical security headers:
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - Referrer-Policy
    - Permissions-Policy
    """

    name = "SecurityHeaders"
    order = 100  # Execute last, add headers to response

    def _setup(self):
        """Initialize security headers configuration"""
        self.headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": self.config.get("x_frame_options", "DENY"),
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

        # Add HSTS if enabled
        if self.config.get("enable_hsts", True):
            max_age = self.config.get("hsts_max_age", 31536000)  # 1 year
            self.headers["Strict-Transport-Security"] = f"max-age={max_age}; includeSubDomains"

        # Add CSP if provided
        csp = self.config.get("content_security_policy")
        if csp:
            self.headers["Content-Security-Policy"] = csp

        # Add custom headers
        custom_headers = self.config.get("custom_headers", {})
        self.headers.update(custom_headers)

        self.headers_added_count = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """
        This middleware only adds response headers.
        Request processing always succeeds.

        Args:
            ctx: Request context

        Returns:
            Always returns success
        """
        # Store headers in context for response processing
        ctx.add_metadata("security_headers", self.headers)
        self.headers_added_count += 1

        return MiddlewareResult.success()

    def get_statistics(self) -> dict:
        """Return security headers statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "headers_added_count": self.headers_added_count,
                "active_headers": list(self.headers.keys()),
            }
        )
        return stats
