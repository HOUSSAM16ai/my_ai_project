# app/middleware/security/security_headers.py
# ======================================================================================
# ==                    SECURITY HEADERS MIDDLEWARE (v∞)                            ==
# ======================================================================================
"""
وسيط رؤوس الأمان - Security Headers Middleware

Adds comprehensive security headers to all responses.
Implements OWASP best practices for HTTP security headers.
"""

import os

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
        """Initialize security headers configuration - KISS principle applied"""
        self.headers = self._get_default_headers()
        self._add_hsts_header()
        self._add_csp_header()
        self._add_custom_headers()
        self._apply_preview_guard()

    def _get_default_headers(self) -> dict:
        """Get default security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": self.config.get("x_frame_options", "DENY"),
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    def _add_hsts_header(self) -> None:
        """Add HSTS header if enabled"""
        if self.config.get("enable_hsts", True):
            max_age = self.config.get("hsts_max_age", 31536000)  # 1 year
            self.headers["Strict-Transport-Security"] = f"max-age={max_age}; includeSubDomains"

    def _add_csp_header(self) -> None:
        """Add Content Security Policy if provided"""
        csp = self.config.get("content_security_policy")
        if csp:
            self.headers["Content-Security-Policy"] = csp

    def _add_custom_headers(self) -> None:
        """Add custom headers from configuration"""
        custom_headers = self.config.get("custom_headers", {})
        self.headers.update(custom_headers)

    def _apply_preview_guard(self) -> None:
        """Allow embedding in GitHub Codespaces Preview (development only)"""
        env = os.environ.get("ENVIRONMENT", "production")
        if env == "development":
            # Remove X-Frame-Options to allow framing
            if "X-Frame-Options" in self.headers:
                del self.headers["X-Frame-Options"]

            # Update CSP to allow GitHub domains
            csp = self.headers.get("Content-Security-Policy", "")
            # So CSP IS present and RESTRICTIVE.
            if csp:
                allowed_ancestors = "frame-ancestors 'self' https://*.github.dev https://*.github.com http://localhost:* http://127.0.0.1:*"
                if "frame-ancestors 'none'" in csp:
                    csp = csp.replace("frame-ancestors 'none'", allowed_ancestors)
                self.headers["Content-Security-Policy"] = csp

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
