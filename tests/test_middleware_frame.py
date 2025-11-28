import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response

try:
    from app.dev_frame_middleware import DevAllowIframeMiddleware
except ImportError:
    DevAllowIframeMiddleware = None

@pytest.mark.skipif(DevAllowIframeMiddleware is None, reason="DevAllowIframeMiddleware not found")
def test_dev_frame_middleware_development():
    """Verify that in development mode, security headers are relaxed to allow framing."""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
        app = Starlette(middleware=[Middleware(DevAllowIframeMiddleware)])

        @app.route("/")
        async def homepage(request):
            return Response(
                "ok",
                headers={
                    "X-Frame-Options": "DENY",
                    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
                },
            )

        client = TestClient(app)
        response = client.get("/")

        # Assertions
        assert "x-frame-options" not in response.headers
        assert "frame-ancestors *" in response.headers["content-security-policy"]


@pytest.mark.skipif(DevAllowIframeMiddleware is None, reason="DevAllowIframeMiddleware not found")
def test_dev_frame_middleware_production():
    """Verify that in production mode, security headers remain strict."""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
        app = Starlette(middleware=[Middleware(DevAllowIframeMiddleware)])

        @app.route("/")
        async def homepage(request):
            return Response(
                "ok",
                headers={
                    "X-Frame-Options": "DENY",
                    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
                },
            )

        client = TestClient(app)
        response = client.get("/")

        # Assertions: Should NOT modify headers
        assert response.headers["x-frame-options"] == "DENY"
        assert (
            response.headers["content-security-policy"]
            == "default-src 'self'; frame-ancestors 'none'"
        )
