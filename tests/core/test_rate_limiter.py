import time

import pytest

from app.core.rate_limiter import RateLimitConfig, ToolRateLimiter


@pytest.fixture
def limiter():
    config = RateLimitConfig(max_calls=2, window_seconds=0.4, cooldown_seconds=0.5)
    return ToolRateLimiter(config)


def test_rate_limit_enforcement(limiter):
    # Call 1: Allowed
    allowed, _ = limiter.check(1, "tool")
    assert allowed

    # Call 2: Allowed
    allowed, _ = limiter.check(1, "tool")
    assert allowed

    # Call 3: Blocked (Limit hit)
    allowed, reason = limiter.check(1, "tool")
    assert not allowed
    assert "Too many requests" in reason


def test_cooldown_expiration(limiter):
    # Hit limit
    limiter.check(1, "tool")
    limiter.check(1, "tool")
    allowed, _ = limiter.check(1, "tool")
    assert not allowed

    # Wait for cooldown
    time.sleep(1.1)

    # Call should be allowed (reset behavior)
    allowed, _ = limiter.check(1, "tool")
    assert allowed


def test_reset(limiter):
    limiter.check(1, "tool")
    limiter.check(1, "tool")
    assert not limiter.check(1, "tool")[0]

    limiter.reset(1, "tool")
    assert limiter.check(1, "tool")[0]


def test_cleanup(limiter):
    limiter.check(1, "tool")
    assert len(limiter._calls) == 1

    time.sleep(1.1)

    # Trigger cleanup
    limiter.check(2, "other")
    # Verify old key cleared (check periodic cleanup logic if integrated)
    # _periodic_cleanup runs every 5 mins. But _check_rate_limit cleans specific key.

    # Force cleanup calls
    limiter._cleanup_expired_keys(time.time())
    assert "1:tool" not in limiter._calls
