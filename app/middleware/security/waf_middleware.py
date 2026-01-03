# app/middleware/security/waf_middleware.py
# ======================================================================================
# ==                    WAF MIDDLEWARE ADAPTER (v∞)                                 ==
# ======================================================================================
"""
وسيط جدار الحماية للتطبيقات - WAF Middleware

Adapter for the existing WAF component using the new middleware architecture.
Integrates Web Application Firewall functionality into the pipeline.
"""

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.security.waf import WebApplicationFirewall

class WAFMiddleware(BaseMiddleware):
    """
    Web Application Firewall Middleware

    Protects against common web attacks:
    - SQL Injection
    - XSS (Cross-Site Scripting)
    - Path Traversal
    - Command Injection
    - LDAP Injection
    """

    name = "WAF"
    order = 10  # Execute early in the pipeline

    def _setup(self):
        """Initialize WAF component"""
        self.waf = WebApplicationFirewall()
        self.blocked_count = 0
        self.checked_count = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """Check request for malicious patterns - KISS principle applied"""
        self.checked_count += 1

        # Skip WAF for health check endpoints
        if self._is_health_check(ctx.path):
            return MiddlewareResult.success()

        try:
            is_safe, attack = self._check_for_attacks(ctx)

            if not is_safe:
                return self._create_blocked_response(attack)

            return MiddlewareResult.success()

        except Exception as e:
            return self._handle_error(e)

    def _is_health_check(self, path: str) -> bool:
        """Check if path is a health check endpoint"""
        return path in ["/health", "/api/health", "/ping"]

    def _check_for_attacks(self, ctx: RequestContext) -> tuple:
        """Check request using WAF"""
        return self.waf.check_request(ctx._raw_request)

    def _create_blocked_response(self, attack) -> MiddlewareResult:
        """Create response for blocked request"""
        self.blocked_count += 1
        attack_type = attack.attack_type if attack else "unknown"

        return MiddlewareResult.forbidden(
            message=f"Request blocked by WAF: {attack_type}"
        ).with_details(
            attack_type=attack_type,
            reason="Malicious pattern detected",
        )

    def _handle_error(self, error: Exception) -> MiddlewareResult:
        """Handle WAF errors gracefully"""
        return MiddlewareResult.success().with_metadata("waf_error", str(error))

    def get_statistics(self) -> dict:
        """Return WAF statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "checked_count": self.checked_count,
                "blocked_count": self.blocked_count,
                "block_rate": (
                    self.blocked_count / self.checked_count if self.checked_count > 0 else 0.0
                ),
            }
        )
        return stats
