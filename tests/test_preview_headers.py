# tests/test_preview_headers.py
import os
import pytest
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.testclient import TestClient
from app.middleware.remove_csp_dev import RemoveBlockingHeadersMiddleware

class SecurityHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'; script-src 'self'"
        return response

def test_middleware_removes_blocking_headers_in_codespace():
    """
    Verifies that RemoveBlockingHeadersMiddleware correctly removes
    X-Frame-Options and CSP frame-ancestors when running in a Codespace environment.
    """
    # 1. Setup a clean FastAPI app
    app = FastAPI()

    # 2. Add a middleware that ADDS the blocking headers (simulating production security)
    # Note: Middleware added last runs first (outermost).
    # We want RemoveBlockingHeadersMiddleware to wrap SecurityHeaderMiddleware.
    # So we add SecurityHeaderMiddleware first (inner), then RemoveBlockingHeadersMiddleware (outer).
    # Wait, Starlette/FastAPI add_middleware works such that the last added is the outermost?
    # Let's verify:
    # app.add_middleware(M1) -> M1(App)
    # app.add_middleware(M2) -> M2(M1(App))
    # So M2 sees the response from M1.

    # We want: Response -> SecurityHeaderMiddleware (adds headers) -> RemoveBlockingHeadersMiddleware (removes headers) -> Client.
    # So RemoveBlockingHeadersMiddleware must be OUTSIDE SecurityHeaderMiddleware.
    # So we must add SecurityHeaderMiddleware FIRST, then RemoveBlockingHeadersMiddleware.

    app.add_middleware(SecurityHeaderMiddleware)
    app.add_middleware(RemoveBlockingHeadersMiddleware)

    @app.get("/")
    def index():
        return {"message": "ok"}

    # 3. Simulate Codespaces environment
    # We need to set the environment variable BEFORE the middleware is instantiated.
    # TestClient(app) instantiates the middleware stack.
    with pytest.MonkeyPatch.context() as m:
        m.setenv("CODESPACE_NAME", "test-codespace-123")

        with TestClient(app) as client:
            response = client.get("/")

            assert response.status_code == 200

            # X-Frame-Options should be removed
            assert "x-frame-options" not in response.headers

            # CSP should be modified: frame-ancestors removed, others kept
            csp = response.headers.get("content-security-policy", "")
            assert "frame-ancestors" not in csp
            assert "script-src 'self'" in csp

def test_middleware_does_nothing_in_production():
    """
    Verifies that RemoveBlockingHeadersMiddleware stays dormant in non-dev environments.
    """
    app = FastAPI()
    app.add_middleware(SecurityHeaderMiddleware)
    app.add_middleware(RemoveBlockingHeadersMiddleware)

    @app.get("/")
    def index():
        return {"message": "ok"}

    # Ensure NO dev/codespace env vars
    with pytest.MonkeyPatch.context() as m:
        m.delenv("CODESPACE_NAME", raising=False)
        m.setenv("ENVIRONMENT", "production")

        with TestClient(app) as client:
            response = client.get("/")

            assert response.status_code == 200

            # Headers should persist
            assert response.headers.get("x-frame-options") == "DENY"
            assert "frame-ancestors 'none'" in response.headers.get("content-security-policy", "")
