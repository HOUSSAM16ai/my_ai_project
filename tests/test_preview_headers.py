# tests/test_preview_headers.py
from starlette.testclient import TestClient

from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware


def test_middleware_enabled_in_dev(monkeypatch):
    """Verify middleware identifies development environment correctly."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    middleware = RemoveBlockingHeadersMiddleware(None)
    assert middleware.enabled is True

def test_middleware_enabled_in_codespaces(monkeypatch):
    """Verify middleware identifies Codespaces environment correctly."""
    monkeypatch.setenv("CODESPACE_NAME", "my-codespace")
    middleware = RemoveBlockingHeadersMiddleware(None)
    assert middleware.enabled is True

def test_middleware_disabled_in_production(monkeypatch):
    """Verify middleware is disabled in production."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CODESPACE_NAME", raising=False)
    monkeypatch.delenv("CODESPACES", raising=False)
    middleware = RemoveBlockingHeadersMiddleware(None)
    assert middleware.enabled is False

def test_headers_removed_in_dev_client(monkeypatch):
    """
    Integration-like test using TestClient.
    """
    monkeypatch.setenv("ENVIRONMENT", "development")

    async def simple_app(scope, receive, send):
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"content-type", b"text/plain"),
                (b"x-frame-options", b"DENY"),
                (b"content-security-policy", b"default-src 'self'; frame-ancestors 'none';"),
            ],
        })
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = RemoveBlockingHeadersMiddleware(simple_app)

    client = TestClient(middleware)
    response = client.get("/")

    assert response.status_code == 200
    # X-Frame-Options should be gone
    assert "x-frame-options" not in response.headers
    # CSP should be relaxed
    csp = response.headers.get("content-security-policy", "")
    assert "frame-ancestors" not in csp.lower()
    # Other parts of CSP should remain (if our logic preserves them)
    assert "default-src 'self'" in csp

def test_headers_preserved_in_prod_client(monkeypatch):
    """Verify headers are NOT removed in production."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CODESPACE_NAME", raising=False)

    async def simple_app(scope, receive, send):
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"x-frame-options", b"DENY"),
                (b"content-security-policy", b"frame-ancestors 'none'"),
            ],
        })
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = RemoveBlockingHeadersMiddleware(simple_app)

    client = TestClient(middleware)
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors" in response.headers["content-security-policy"]
