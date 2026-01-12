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
        """Verify Zero Trust session - KISS principle applied"""
        session_id = self._get_session_id(ctx)

        if not session_id:
            return self._create_missing_session_response()

        try:
            is_valid, session = self._verify_session(session_id, ctx)

            if not is_valid:
                return self._create_invalid_session_response(session_id)

            self._store_session_in_context(ctx, session)
            self.verified_count += 1
            return MiddlewareResult.success()

        except Exception as e:
            return self._handle_error(e)

    def _get_session_id(self, ctx: RequestContext) -> str:
        """Get session ID from headers or context"""
        return ctx.get_header("X-Session-ID") or ctx.session_id

    def _create_missing_session_response(self) -> MiddlewareResult:
        """Create response for missing session ID"""
        return MiddlewareResult.unauthorized(message="Zero Trust session required").with_details(
            reason="Missing session ID",
            required_header="X-Session-ID",
        )

    def _verify_session(self, session_id: str, ctx: RequestContext) -> tuple:
        """Perform continuous verification of session"""
        return self.zero_trust.continuous_verify(
            session_id,
            ctx._raw_request,
        )

    def _create_invalid_session_response(self, session_id: str) -> MiddlewareResult:
        """Create response for invalid session"""
        self.failed_count += 1
        return MiddlewareResult.unauthorized(message="Continuous verification failed").with_details(
            reason="Session validation failed",
            session_id=session_id,
        )

    def _store_session_in_context(self, ctx: RequestContext, session: dict) -> None:
        """Store validated session in request context"""
        ctx.add_metadata("zero_trust_session", session)

    def _handle_error(self, error: Exception) -> MiddlewareResult:
        """Handle Zero Trust errors gracefully"""
        return MiddlewareResult.success().with_metadata("zero_trust_error", str(error))

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
