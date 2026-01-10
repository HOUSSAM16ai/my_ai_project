# app/middleware/security/rate_limit_middleware.py
# ======================================================================================
# ==                    RATE LIMIT MIDDLEWARE ADAPTER (v∞)                          ==
# ======================================================================================
"""
وسيط تحديد المعدل - Rate Limit Middleware

Adapter for the existing rate limiter using the new middleware architecture.
Provides adaptive rate limiting based on user tier.
"""

import contextlib

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.security.rate_limiter import AdaptiveRateLimiter, UserTier


class RateLimitMiddleware(BaseMiddleware):
    """
    Adaptive Rate Limiting Middleware

    Features:
    - Tier-based limits (Free, Premium, Enterprise)
    - Per-IP and per-user tracking
    - Burst allowance
    - Token bucket algorithm
    """

    name = "RateLimit"
    order = 30  # Execute after security checks

    def _setup(self):
        """Initialize rate limiter"""
        self.rate_limiter = AdaptiveRateLimiter()
        self.rate_limited_count = 0
        self.checked_count = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """Check if request should be rate limited - KISS principle applied"""
        self.checked_count += 1

        # Skip rate limiting for health checks
        if self._is_health_check(ctx.path):
            return MiddlewareResult.success()

        user_tier = self._get_user_tier(ctx)

        try:
            is_allowed, info = self._check_rate_limit(ctx, user_tier)

            if not is_allowed:
                return self._create_rate_limit_response(info, user_tier)

            # Add rate limit info to context
            self._add_rate_limit_headers(ctx, info, user_tier)
            return MiddlewareResult.success()

        except Exception as e:
            return self._handle_error(e)

    def _is_health_check(self, path: str) -> bool:
        """Check if path is a health check endpoint"""
        return path in ["/health", "/api/health", "/ping"]

    def _check_rate_limit(self, ctx: RequestContext, user_tier) -> tuple:
        """Check rate limit for the request"""
        return self.rate_limiter.check_rate_limit(
            ctx._raw_request,
            user_id=ctx.user_id,
            tier=user_tier,
        )

    def _create_rate_limit_response(self, info: dict, user_tier) -> MiddlewareResult:
        """Create rate limited response"""
        self.rate_limited_count += 1
        reset_time = info.get("reset_time", 60)

        return MiddlewareResult.rate_limited(
            message="Rate limit exceeded",
            retry_after=reset_time,
        ).with_details(
            limit=info.get("limit"),
            remaining=info.get("remaining", 0),
            reset_time=reset_time,
            tier=user_tier.value,
        )

    def _add_rate_limit_headers(self, ctx: RequestContext, info: dict, user_tier) -> None:
        """Add rate limit information to response headers"""
        ctx.add_metadata(
            "rate_limit_info",
            {
                "limit": info.get("limit"),
                "remaining": info.get("remaining"),
                "reset_time": info.get("reset_time"),
                "tier": user_tier.value,
            },
        )

    def _handle_error(self, error: Exception) -> MiddlewareResult:
        """Handle rate limiter errors gracefully"""
        return MiddlewareResult.success().with_metadata("rate_limit_error", str(error))

    def _get_user_tier(self, ctx: RequestContext) -> UserTier:
        """
        Determine user tier from context

        Args:
            ctx: Request context

        Returns:
            UserTier enum value
        """
        # Default to FREE tier
        tier = UserTier.FREE

        # Check if user is authenticated and has tier metadata
        if ctx.user_id:
            tier_str = ctx.get_metadata("user_tier")
            if tier_str:
                with contextlib.suppress(KeyError, AttributeError):
                    tier = UserTier[tier_str.upper()]

        return tier

    def get_statistics(self) -> dict:
        """Return rate limiter statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "checked_count": self.checked_count,
                "rate_limited_count": self.rate_limited_count,
                "rate_limit_rate": (
                    self.rate_limited_count / self.checked_count if self.checked_count > 0 else 0.0
                ),
            }
        )
        return stats
