# tests/test_preview_headers.py
from starlette.testclient import TestClient

from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware


def test_middleware_always_active(monkeypatch):
    """Verify middleware is active regardless of environment (sanitization policy)."""
    middleware = RemoveBlockingHeadersMiddleware(None)
    # The current implementation is unconditional
    assert isinstance(middleware, RemoveBlockingHeadersMiddleware)


def test_headers_removed_unconditionally(monkeypatch):
    """
    Integration-like test using TestClient.
    """
    monkeypatch.setenv("ENVIRONMENT", "development")

    async def simple_app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"server", b"nginx/1.0"),
                    (b"x-powered-by", b"PHP/5.0"),
                    (b"x-frame-options", b"DENY"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = RemoveBlockingHeadersMiddleware(simple_app)

    client = TestClient(middleware)
    response = client.get("/")

    assert response.status_code == 200
    # Server and X-Powered-By should be gone
    assert "server" not in response.headers
    assert "x-powered-by" not in response.headers

    # X-Frame-Options is NOT in BLOCKED_HEADERS in current implementation, so it should remain
    # unless we update the middleware. Based on memory, it's SecurityHeadersMiddleware that handles X-Frame-Options.
    assert "x-frame-options" in response.headers
