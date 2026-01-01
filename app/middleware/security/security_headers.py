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

    # TODO: Split this function (47 lines) - KISS principle
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

        # --- PREVIEW GUARD ---
        # Allow embedding in GitHub Codespaces Preview when in development mode
        # This fixes the "White Page" issue in VS Code Preview
        env = os.environ.get("ENVIRONMENT", "production")
        if env == "development":
            # Remove X-Frame-Options to allow framing
            if "X-Frame-Options" in self.headers:
                del self.headers["X-Frame-Options"]

            # Update CSP to allow GitHub domains
            csp = self.headers.get("Content-Security-Policy", "")
            # If no CSP is present, we don't need to add one, but if frame-ancestors is in it, we modify it.
            # If frame-ancestors is NOT present, but CSP IS, it defaults to allowed (unless default-src 'none').
            # The issue usually comes when a restrictive CSP is set.
            # However, looking at diagnostics, we saw:
            # content-security-policy: default-src 'self'; ... frame-ancestors 'none';
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
