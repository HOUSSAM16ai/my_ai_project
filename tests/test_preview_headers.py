# tests/test_preview_headers.py
import os
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware

# We verify the logic via unit tests on the middleware and integration tests via TestClient

def test_middleware_logic_dev_mode():
    """Verify headers are stripped when ENVIRONMENT=development"""
    app = FastAPI()
    app.add_middleware(RemoveBlockingHeadersMiddleware)

    @app.get("/")
    def index():
        return {"msg": "ok"}

    # Mock environment
    os.environ["ENVIRONMENT"] = "development"
    # Ensure CODESPACE_NAME is not set (or is, doesn't matter, development triggers it)

    # Create a wrapper middleware that adds the bad headers first,
    # to simulate the default secure headers that might be added by other middleware
    # BUT here we are testing if RemoveBlockingHeadersMiddleware *removes* them if they exist?
    # No, usually SecurityMiddleware adds them.
    # If we want to test removal, we need to inject them *before* RemoveBlockingHeadersMiddleware runs on the response?
    # Wait, middleware order:
    # 1. RemoveBlockingHeadersMiddleware (outermost? or inner?)
    # Request -> RemoveBlocking -> ... -> Security -> Endpoint
    # Response <- RemoveBlocking <- ... <- Security <- Endpoint
    # So RemoveBlocking must wrap Security to modify its response.
    # FastAPI app.add_middleware adds to the "outer" layer.

    # Let's simulate a downstream middleware adding headers
    from starlette.middleware.base import BaseHTTPMiddleware

    class AddSecurityHeaders(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Content-Security-Policy"] = "frame-ancestors 'none'; default-src 'self'"
            return response

    # Re-build app to control order:
    # Inner: AddSecurityHeaders
    # Outer: RemoveBlockingHeadersMiddleware

    app2 = FastAPI()
    app2.add_middleware(RemoveBlockingHeadersMiddleware) # Outer
    app2.add_middleware(AddSecurityHeaders)              # Inner

    @app2.get("/")
    def index2():
        return {"msg": "ok"}

    client = TestClient(app2)
    resp = client.get("/")

    assert resp.status_code == 200
    assert "x-frame-options" not in resp.headers
    # CSP should be relaxed
    assert "frame-ancestors" not in resp.headers["content-security-policy"]
    assert "default-src 'self'" in resp.headers["content-security-policy"]


def test_middleware_logic_prod_mode():
    """Verify headers are PRESERVED when NOT in development"""
    os.environ["ENVIRONMENT"] = "production"
    if "CODESPACE_NAME" in os.environ:
        del os.environ["CODESPACE_NAME"]

    app = FastAPI()
    app.add_middleware(RemoveBlockingHeadersMiddleware)

    # Simulate security headers
    from starlette.middleware.base import BaseHTTPMiddleware
    class AddSecurityHeaders(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Frame-Options"] = "DENY"
            return response

    app.add_middleware(AddSecurityHeaders)

    @app.get("/")
    def index():
        return {"msg": "ok"}

    client = TestClient(app)
    resp = client.get("/")

    assert resp.status_code == 200
    # Should still have it
    assert resp.headers["x-frame-options"] == "DENY"

def test_codespace_trigger():
    """Verify CODESPACE_NAME triggers the removal even if env is not dev"""
    os.environ["ENVIRONMENT"] = "production"
    os.environ["CODESPACE_NAME"] = "ominous-octopus-55"

    app = FastAPI()
    app.add_middleware(RemoveBlockingHeadersMiddleware)

    from starlette.middleware.base import BaseHTTPMiddleware
    class AddSecurityHeaders(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["X-Frame-Options"] = "DENY"
            return response

    app.add_middleware(AddSecurityHeaders)

    @app.get("/")
    def index():
        return {"msg": "ok"}

    client = TestClient(app)
    resp = client.get("/")

    assert "x-frame-options" not in resp.headers

    # Cleanup
    del os.environ["CODESPACE_NAME"]
