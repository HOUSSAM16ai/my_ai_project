# app/middleware/rate_limiter_middleware.py
"""
Rate Limiter Middleware - Request Rate Limiting
===============================================

Implements rate limiting to prevent abuse and ensure fair resource allocation.
Addresses security issue: Missing rate limiting on sensitive endpoints.

Features:
- Token bucket algorithm
- Per-client-ID tracking
- Configurable limits and windows
- Clean up of expired requests
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps

# Conditional imports for testing environments
try:
    from fastapi import HTTPException, Request

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    # Mock classes for testing without FastAPI
    class Request:
        pass

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str, headers: dict | None = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers or {}
            super().__init__(detail)


logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation.

    Each client has a bucket with tokens. Each request consumes a token.
    Tokens are refilled at a constant rate.
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        burst_size: int | None = None,
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in time window
            window_seconds: Time window in seconds
            burst_size: Maximum burst size (defaults to max_requests)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_size = burst_size or max_requests

        # Track: client_id -> (tokens, last_refill_time)
        self._buckets: dict[str, tuple[float, float]] = {}

        # Rate of token refill (tokens per second)
        self._refill_rate = max_requests / window_seconds

        logger.info(
            f"Rate limiter initialized: {max_requests} req/{window_seconds}s, "
            f"burst={self.burst_size}"
        )

    def _get_client_id(self, request: Request) -> str:
        """
        Extract client identifier from request.

        Priority:
        1. API key from header
        2. User ID from auth
        3. IP address
        """
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key[:16]}"

        # Check for authenticated user
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _refill_bucket(self, client_id: str, now: float) -> tuple[float, float]:
        """
        Refill tokens in bucket based on elapsed time.

        Returns:
            (current_tokens, last_refill_time)
        """
        if client_id not in self._buckets:
            # New client, start with full bucket
            return (self.burst_size, now)

        tokens, last_refill = self._buckets[client_id]

        # Calculate tokens to add based on elapsed time
        elapsed = now - last_refill
        tokens_to_add = elapsed * self._refill_rate

        # Add tokens but don't exceed burst size
        new_tokens = min(tokens + tokens_to_add, self.burst_size)

        return (new_tokens, now)

    def is_allowed(self, request: Request) -> tuple[bool, dict]:
        """
        Check if request is allowed.

        Returns:
            (allowed, metadata) tuple
            metadata contains: remaining, reset_at, client_id
        """
        client_id = self._get_client_id(request)
        now = time.time()

        # Refill bucket
        tokens, _ = self._refill_bucket(client_id, now)

        # Check if we have at least 1 token
        if tokens >= 1.0:
            # Consume 1 token
            self._buckets[client_id] = (tokens - 1.0, now)

            metadata = {
                "client_id": client_id,
                "remaining": int(tokens - 1.0),
                "reset_at": int(now + self.window_seconds),
            }

            return (True, metadata)
        else:
            # No tokens available
            reset_in = max(0, (1.0 - tokens) / self._refill_rate)

            metadata = {
                "client_id": client_id,
                "remaining": 0,
                "reset_at": int(now + reset_in),
                "retry_after": int(reset_in) + 1,
            }

            logger.warning(f"Rate limit exceeded for {client_id}. Retry after {int(reset_in)}s")

            return (False, metadata)

    def cleanup_expired(self, max_age_seconds: int = 3600):
        """Remove expired bucket entries to prevent memory bloat."""
        now = time.time()
        expired = [
            client_id
            for client_id, (_, last_refill) in self._buckets.items()
            if now - last_refill > max_age_seconds
        ]

        for client_id in expired:
            del self._buckets[client_id]

        if expired:
            logger.debug(f"Cleaned up {len(expired)} expired rate limit buckets")


# Global rate limiters for different endpoint categories
_rate_limiters: dict[str, TokenBucketRateLimiter] = {
    "default": TokenBucketRateLimiter(max_requests=100, window_seconds=60),
    "strict": TokenBucketRateLimiter(max_requests=20, window_seconds=60),
    "lenient": TokenBucketRateLimiter(max_requests=300, window_seconds=60),
}


def rate_limit(
    max_requests: int = 100,
    window_seconds: int = 60,
    limiter_key: str = "default",
):
    """
    Decorator for rate limiting endpoints.

    Usage:
        @router.post("/api/chat")
        @rate_limit(max_requests=50, window_seconds=60)
        async def chat_endpoint():
            ...

    Args:
        max_requests: Maximum requests in time window
        window_seconds: Time window in seconds
        limiter_key: Key for shared rate limiter instance
    """
    # Get or create rate limiter
    if limiter_key not in _rate_limiters:
        _rate_limiters[limiter_key] = TokenBucketRateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

    limiter = _rate_limiters[limiter_key]

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Check rate limit
            allowed, metadata = limiter.is_allowed(request)

            if not allowed:
                # Add rate limit headers
                headers = {
                    "X-RateLimit-Limit": str(limiter.max_requests),
                    "X-RateLimit-Remaining": str(metadata["remaining"]),
                    "X-RateLimit-Reset": str(metadata["reset_at"]),
                    "Retry-After": str(metadata.get("retry_after", 60)),
                }

                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later.",
                    headers=headers,
                )

            # Add rate limit info to response headers
            request.state.rate_limit_metadata = metadata

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def get_rate_limiter(limiter_key: str = "default") -> TokenBucketRateLimiter:
    """Get a rate limiter instance by key."""
    return _rate_limiters.get(limiter_key, _rate_limiters["default"])


__all__ = [
    "TokenBucketRateLimiter",
    "get_rate_limiter",
    "rate_limit",
]
