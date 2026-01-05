"""اختبارات محددات المعدل لضمان الدقة والصرامة في تتبع الاستخدام."""

from types import SimpleNamespace

from starlette.requests import Request

from app.security import rate_limiter


def _build_request(host: str) -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": (host, 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "root_path": "",
        "app": None,
        "asgi": {"version": "3.0", "spec_version": "2.3"},
    }
    return Request(scope)


def _freeze_time(monkeypatch, timestamps: list[float]) -> None:
    iterator = iter(timestamps)
    monkeypatch.setattr(rate_limiter, "time", SimpleNamespace(time=lambda: next(iterator)))


def test_check_rate_limit_allows_until_limit(monkeypatch) -> None:
    limiter = rate_limiter.AdaptiveRateLimiter()
    limiter.limits[rate_limiter.UserTier.FREE] = (2, 60)
    request = _build_request("1.1.1.1")

    _freeze_time(monkeypatch, [10.0, 20.0])

    allowed_first, status_first = limiter.check_rate_limit(request)
    allowed_second, status_second = limiter.check_rate_limit(request)

    assert allowed_first is True
    assert status_first.remaining == 1
    assert allowed_second is True
    assert status_second.remaining == 0


def test_check_rate_limit_blocks_after_limit(monkeypatch) -> None:
    limiter = rate_limiter.AdaptiveRateLimiter()
    limiter.limits[rate_limiter.UserTier.FREE] = (1, 30)
    request = _build_request("2.2.2.2")

    _freeze_time(monkeypatch, [50.0, 55.0])

    allowed_first, status_first = limiter.check_rate_limit(request)
    allowed_second, status_second = limiter.check_rate_limit(request)

    assert allowed_first is True
    assert status_first.remaining == 0
    assert allowed_second is False
    assert status_second.reset_time == 25


def test_check_rate_limit_prefers_user_id_over_ip(monkeypatch) -> None:
    limiter = rate_limiter.AdaptiveRateLimiter()
    limiter.limits[rate_limiter.UserTier.PREMIUM] = (1, 120)
    first_request = _build_request("9.9.9.9")
    second_request = _build_request("8.8.8.8")

    _freeze_time(monkeypatch, [100.0, 110.0])

    allowed_first, _ = limiter.check_rate_limit(
        first_request, user_id="alpha", tier=rate_limiter.UserTier.PREMIUM
    )
    allowed_second, status_second = limiter.check_rate_limit(
        second_request, user_id="alpha", tier=rate_limiter.UserTier.PREMIUM
    )

    assert allowed_first is True
    assert allowed_second is False
    assert set(limiter.memory_store.keys()) == {"alpha"}
    assert status_second.limit == 1
