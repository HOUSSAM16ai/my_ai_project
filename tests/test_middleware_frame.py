import os
from unittest import mock

from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response

from app.middleware.security.security_headers import SecurityHeadersMiddleware


def test_dev_frame_middleware_development():
    """Verify that in development mode, security headers are relaxed to allow framing."""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
        # We assume SecurityHeadersMiddleware adds headers.
        # We initialize it with default config (empty dict).
        app = Starlette(middleware=[Middleware(SecurityHeadersMiddleware)])

        @app.route("/")
        async def homepage(request):
            return Response("ok")

        client = TestClient(app)
        response = client.get("/")

        # Assertions
        # In dev mode, X-Frame-Options should be removed to allow framing (e.g. for Codespaces preview)
        assert "x-frame-options" not in response.headers, f"Headers: {response.headers}"

        # Check CSP if it exists, it should allow framing
        if "content-security-policy" in response.headers:
            csp = response.headers["content-security-policy"]
            assert "frame-ancestors 'none'" not in csp


def test_dev_frame_middleware_production():
    """Verify that in production mode, security headers remain strict."""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
        app = Starlette(middleware=[Middleware(SecurityHeadersMiddleware)])

        @app.route("/")
        async def homepage(request):
            return Response("ok")

        client = TestClient(app)
        response = client.get("/")

        # Assertions: Should have strict headers
        assert response.headers.get("x-frame-options") == "DENY"
        # CSP default doesn't set frame-ancestors 'none' explicitly in code unless config provided,
        # but X-Frame-Options DENY handles it.
