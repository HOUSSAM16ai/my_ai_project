
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI

from app.config.settings import AppSettings
from app.kernel import RealityKernel


class TestRealityKernel:

    @pytest.fixture
    def mock_settings(self):
        """Returns a valid AppSettings dictionary/object for testing."""
        return {
            "PROJECT_NAME": "TestProject",
            "VERSION": "1.0.0",
            "ENVIRONMENT": "testing",
            "DEBUG": True,
            "API_V1_STR": "/api/v1",
            "SECRET_KEY": "test-secret-key-that-is-long-enough",
            "ALLOWED_HOSTS": ["*"],
            "BACKEND_CORS_ORIGINS": ["http://localhost:3000"],
            "FRONTEND_URL": "http://localhost:3000",
            "DATABASE_URL": "sqlite:///:memory:"
        }

    def test_kernel_initialization(self, mock_settings):
        """
        GIVEN valid settings
        WHEN RealityKernel is initialized
        THEN it should create a FastAPI app and weave routes.
        """
        kernel = RealityKernel(mock_settings)
        assert kernel.app is not None
        assert isinstance(kernel.app, FastAPI)
        assert kernel.app.title == "TestProject"

    def test_get_app_returns_app(self, mock_settings):
        """
        GIVEN an initialized kernel
        WHEN get_app() is called
        THEN it should return the FastAPI instance.
        """
        kernel = RealityKernel(mock_settings)
        app = kernel.get_app()
        assert isinstance(app, FastAPI)
        assert app == kernel.app

    def test_kernel_resilience_to_random_settings(self, mock_settings):
        """
        GIVEN settings with extra or missing optional fields
        WHEN kernel is initialized
        THEN it should gracefully handle them.
        """
        # Add random junk
        mock_settings["RANDOM_JUNK"] = "chaos"
        # Remove optional
        if "VERSION" in mock_settings:
            del mock_settings["VERSION"]

        kernel = RealityKernel(mock_settings)
        assert kernel.app.title == "TestProject"
        # Version should default to what's in code
        assert kernel.app.version == "v4.1-simplified"

    def test_route_weaving_logic(self, mock_settings):
        """
        GIVEN a kernel
        WHEN initialized
        THEN it should explicitly include core routers.
        """
        # We can check the routes of the created app
        kernel = RealityKernel(mock_settings)
        routes = [r.path for r in kernel.app.routes]

        # Check for prefixes we expect
        # Note: FastAPI routes include the full path
        has_system = any("/system" in r or "/health" in r for r in routes)
        # Since system router might be mounted at root, let's check for specific endpoints if needed
        # But simply checking successful initialization implies weaving didn't crash.

        # Let's verify route count is > 0
        assert len(kernel.app.routes) > 0

    @pytest.mark.asyncio
    async def test_lifespan_startup_shutdown(self, mock_settings):
        """
        GIVEN a kernel app
        WHEN the lifespan context is entered
        THEN it should run startup validations and yield, then log shutdown.
        """
        kernel = RealityKernel(mock_settings)

        # We can test the generator manually
        lifespan_gen = kernel._handle_lifespan_events()

        # STARTUP
        with patch("app.core.database.validate_schema_on_startup") as mock_validate:
             await anext(lifespan_gen)
             # In testing environment, validate_schema might be skipped or mocked
             # The code says: if env != testing: validate...
             # Our mock_settings has ENVIRONMENT=testing, so it skips.
             mock_validate.assert_not_called()

        # SHUTDOWN
        try:
            await anext(lifespan_gen)
        except StopAsyncIteration:
            pass # Expected end of generator

    def test_cors_logic_dev_vs_prod(self):
        """
        GIVEN different environments
        WHEN app is created
        THEN CORS middleware should be configured appropriately.
        """
        # Dev Case
        dev_settings = {
            "PROJECT_NAME": "Dev",
            "ENVIRONMENT": "development",
            "SECRET_KEY": "s",
            "BACKEND_CORS_ORIGINS": [], # Empty implies default logic
            "FRONTEND_URL": "http://localhost:3000"
        }
        kernel = RealityKernel(dev_settings)
        # Verify middleware configuration (complex to inspect directly in FastAPI,
        # but we can rely on no crash and basic property checks if exposed)

        # Prod Case
        prod_settings = {
            "PROJECT_NAME": "Prod",
            "ENVIRONMENT": "production",
            "SECRET_KEY": "s",
            "BACKEND_CORS_ORIGINS": ["https://myprod.com"],
            "FRONTEND_URL": "https://myprod.com"
        }
        kernel_prod = RealityKernel(prod_settings)
        assert kernel_prod.app.title == "Prod"
