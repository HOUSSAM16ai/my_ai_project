from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.core.base_middleware import BaseMiddleware

def test_rate_limit_middleware_exists():
    assert issubclass(RateLimitMiddleware, BaseMiddleware)
