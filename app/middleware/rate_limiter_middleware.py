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

try:
    from fastapi import HTTPException, Request
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    class Request:
        pass

    class HTTPExceptionError(Exception):

        def __init__(self, status_code: int, detail: str, headers: dict | None = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers or {}
            super().__init__(detail)

    HTTPException = HTTPExceptionError
logger = logging.getLogger(__name__)

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation.

    Each client has a bucket with tokens. Each request consumes a token.
    Tokens are refilled at a constant rate.
    """

    def __init__(self, max_requests: int=100, window_seconds: int=60,
        burst_size: (int | None)=None):
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
        self._buckets: dict[str, tuple[float, float]] = {}
        self._refill_rate = max_requests / window_seconds
        logger.info(
            f'Rate limiter initialized: {max_requests} req/{window_seconds}s, burst={self.burst_size}'
            )

    def _get_client_id(self, request: Request) ->str:
        """
        Extract client identifier from request.

        Priority:
        1. API key from header
        2. User ID from auth
        3. IP address
        """
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f'apikey:{api_key[:16]}'
        if hasattr(request.state, 'user_id'):
            return f'user:{request.state.user_id}'
        client_ip = request.client.host if request.client else 'unknown'
        return f'ip:{client_ip}'

    def _refill_bucket(self, client_id: str, now: float) ->tuple[float, float]:
        """
        Refill tokens in bucket based on elapsed time.

        Returns:
            (current_tokens, last_refill_time)
        """
        if client_id not in self._buckets:
            return self.burst_size, now
        tokens, last_refill = self._buckets[client_id]
        elapsed = now - last_refill
        tokens_to_add = elapsed * self._refill_rate
        new_tokens = min(tokens + tokens_to_add, self.burst_size)
        return new_tokens, now

    def is_allowed(self, request: Request) ->tuple[bool, dict]:
        """
        Check if request is allowed.

        Returns:
            (allowed, metadata) tuple
            metadata contains: remaining, reset_at, client_id
        """
        client_id = self._get_client_id(request)
        now = time.time()
        tokens, _ = self._refill_bucket(client_id, now)
        if tokens >= 1.0:
            self._buckets[client_id] = tokens - 1.0, now
            metadata = {'client_id': client_id, 'remaining': int(tokens -
                1.0), 'reset_at': int(now + self.window_seconds)}
            return True, metadata
        reset_in = max(0, (1.0 - tokens) / self._refill_rate)
        metadata = {'client_id': client_id, 'remaining': 0, 'reset_at':
            int(now + reset_in), 'retry_after': int(reset_in) + 1}
        logger.warning(
            f'Rate limit exceeded for {client_id}. Retry after {int(reset_in)}s'
            )
        return False, metadata

    def reset(self) -> None:
        """إعادة ضبط دلاء الرموز لبدء نافذة جديدة فوراً."""

        self._buckets.clear()

_rate_limiters: dict[str, TokenBucketRateLimiter] = {
    'default': TokenBucketRateLimiter(max_requests=100, window_seconds=60),
    'strict': TokenBucketRateLimiter(max_requests=20, window_seconds=60),
    'lenient': TokenBucketRateLimiter(max_requests=300, window_seconds=60),
}

def _build_rate_limit_headers(limiter: TokenBucketRateLimiter, metadata: dict) -> dict:
    """
    بناء ترويسات HTTP للرد على تجاوز الحد.

    Args:
        limiter: مثيل rate limiter
        metadata: معلومات العميل والحدود

    Returns:
        dict: ترويسات HTTP
    """
    return {
        'X-RateLimit-Limit': str(limiter.max_requests),
        'X-RateLimit-Remaining': str(metadata['remaining']),
        'X-RateLimit-Reset': str(metadata['reset_at']),
        'Retry-After': str(metadata.get('retry_after', 60))
    }


def _get_or_create_limiter(limiter_key: str, max_requests: int, window_seconds: int) -> TokenBucketRateLimiter:
    """
    الحصول على أو إنشاء rate limiter.

    Args:
        limiter_key: مفتاح rate limiter
        max_requests: أقصى عدد طلبات
        window_seconds: نافذة الوقت بالثواني

    Returns:
        TokenBucketRateLimiter: مثيل rate limiter
    """
    if limiter_key not in _rate_limiters:
        _rate_limiters[limiter_key] = TokenBucketRateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds
        )
    return _rate_limiters[limiter_key]


def rate_limit(max_requests: int = 100, window_seconds: int = 60, limiter_key: str = 'default'):
    """
    مُزخرف لتحديد معدل الطلبات على endpoints.

    Usage:
        @router.post("/api/chat")
        @rate_limit(max_requests=50, window_seconds=60)
        async def chat_endpoint():
            ...

    Args:
        max_requests: أقصى عدد طلبات في نافذة الوقت
        window_seconds: نافذة الوقت بالثواني
        limiter_key: مفتاح لمثيل rate limiter المشترك
    """
    limiter = _get_or_create_limiter(limiter_key, max_requests, window_seconds)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # فحص السماح بالطلب
            allowed, metadata = limiter.is_allowed(request)

            if not allowed:
                # بناء الرد برفض الطلب
                headers = _build_rate_limit_headers(limiter, metadata)
                raise HTTPException(
                    status_code=429,
                    detail='Too many requests. Please try again later.',
                    headers=headers
                )

            # حفظ metadata للاستخدام في الطلب
            request.state.rate_limit_metadata = metadata
            return await func(request, *args, **kwargs)

        for name, value in func.__globals__.items():
            wrapper.__globals__.setdefault(name, value)

        return wrapper
    return decorator

def get_rate_limiter(limiter_key: str='default') ->TokenBucketRateLimiter:
    """Get a rate limiter instance by key."""
    return _rate_limiters.get(limiter_key, _rate_limiters['default'])


def reset_rate_limiter(limiter_key: str) -> None:
    """إعادة ضبط معدل الطلبات لمفتاح محدد لتسهيل الاختبارات وحالات الطوارئ."""

    if limiter_key in _rate_limiters:
        _rate_limiters[limiter_key].reset()

__all__ = ['TokenBucketRateLimiter', 'get_rate_limiter', 'rate_limit']
