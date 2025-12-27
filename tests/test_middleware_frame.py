import os
from unittest import mock

from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import Response

from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware


def test_dev_frame_middleware_development():
    """Verify that RemoveBlockingHeadersMiddleware removes blocked headers."""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
        app = Starlette(middleware=[Middleware(RemoveBlockingHeadersMiddleware)])

        @app.route("/")
        async def homepage(request):
            return Response(
                "ok",
                headers={
                    "Server": "TestServer/1.0",
                    "X-Powered-By": "TestFramework",
                    "X-Frame-Options": "DENY",
                    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
                },
            )

        client = TestClient(app)
        response = client.get("/")

        # Assertions - RemoveBlockingHeadersMiddleware only removes specific headers
        assert "server" not in response.headers
        assert "x-powered-by" not in response.headers
        # X-Frame-Options and CSP are NOT removed by this middleware
        assert "x-frame-options" in response.headers
        assert "content-security-policy" in response.headers


def test_dev_frame_middleware_production():
    """Verify that RemoveBlockingHeadersMiddleware works the same in production."""
    with mock.patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
        app = Starlette(middleware=[Middleware(RemoveBlockingHeadersMiddleware)])

        @app.route("/")
        async def homepage(request):
            return Response(
                "ok",
                headers={
                    "Server": "TestServer/1.0",
                    "X-Powered-By": "TestFramework",
                    "X-Frame-Options": "DENY",
                    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
                },
            )

        client = TestClient(app)
        response = client.get("/")

        # Assertions: Middleware removes blocked headers regardless of environment
        assert "server" not in response.headers
        assert "x-powered-by" not in response.headers
        assert response.headers["x-frame-options"] == "DENY"
        assert (
            response.headers["content-security-policy"]
            == "default-src 'self'; frame-ancestors 'none'"
        )
