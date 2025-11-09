# app/middleware/security/zero_trust_middleware.py
# ======================================================================================
# ==                    ZERO TRUST MIDDLEWARE ADAPTER (v∞)                          ==
# ======================================================================================
"""
وسيط الثقة المعدومة - Zero Trust Middleware

Adapter for Zero Trust authentication using the new middleware architecture.
Provides continuous verification for authenticated endpoints.
"""

from app.middleware.core.base_middleware import ConditionalMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.security.zero_trust import ZeroTrustAuthenticator


class ZeroTrustMiddleware(ConditionalMiddleware):
    """
    Zero Trust Authentication Middleware

    Features:
    - Continuous identity verification
    - Session-based authentication
    - Context-aware validation
    - Behavioral analysis
    """

    name = "ZeroTrust"
    order = 40  # Execute after rate limiting
    enabled = False  # Disabled by default (opt-in per route)

    def _setup(self):
        """Initialize Zero Trust authenticator"""
        secret_key = self.config.get("secret_key", "change-me-in-production")
        self.zero_trust = ZeroTrustAuthenticator(secret_key)
        self.verified_count = 0
        self.failed_count = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Verify Zero Trust session

        Args:
            ctx: Request context

        Returns:
            MiddlewareResult indicating if session is valid
        """
        # Get session ID from headers or context
        session_id = ctx.get_header("X-Session-ID") or ctx.session_id

        if not session_id:
            return MiddlewareResult.unauthorized(
                message="Zero Trust session required"
            ).with_details(
                reason="Missing session ID",
                required_header="X-Session-ID",
            )

        try:
            # Continuous verification
            is_valid, session = self.zero_trust.continuous_verify(
                session_id,
                ctx._raw_request,
            )

            if not is_valid:
                self.failed_count += 1
                return MiddlewareResult.unauthorized(
                    message="Continuous verification failed"
                ).with_details(
                    reason="Session validation failed",
                    session_id=session_id,
                )

            self.verified_count += 1

            # Store session in context
            ctx.add_metadata("zero_trust_session", session)

            return MiddlewareResult.success()

        except Exception as e:
            self.failed_count += 1
            return MiddlewareResult.unauthorized(message=f"Zero Trust verification error: {str(e)}")

    def get_statistics(self) -> dict:
        """Return Zero Trust statistics"""
        stats = super().get_statistics()
        total = self.verified_count + self.failed_count
        stats.update(
            {
                "verified_count": self.verified_count,
                "failed_count": self.failed_count,
                "verification_rate": (self.verified_count / total if total > 0 else 0.0),
            }
        )
        return stats
