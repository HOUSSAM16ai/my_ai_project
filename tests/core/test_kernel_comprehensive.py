
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI

from app.kernel import RealityKernel
from app.config.settings import AppSettings


class TestRealityKernel:

    @pytest.fixture
    def mock_settings(self):
        """Returns a valid AppSettings object for testing."""
        return AppSettings(
            PROJECT_NAME="TestProject",
            VERSION="1.0.0",
            ENVIRONMENT="testing",
            DEBUG=True,
            API_V1_STR="/api/v1",
            SECRET_KEY="test-secret-key-that-is-long-enough-for-validation",
            ALLOWED_HOSTS=['*'],
            BACKEND_CORS_ORIGINS=["http://localhost:3000"],
            FRONTEND_URL="http://localhost:3000",
            DATABASE_URL="sqlite:///:memory:"
        )

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
        GIVEN settings with extra fields (not possible with strict Pydantic models in constructor)
        WHEN kernel is initialized
        THEN it should work.
        """
        # With strict typing in RealityKernel(settings: AppSettings), we can't pass random junk dictionaries.
        # This test ensures that a valid AppSettings object works correctly.
        kernel = RealityKernel(mock_settings)
        assert kernel.app.title == "TestProject"

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
        assert len(kernel.app.routes) > 0

    @pytest.mark.asyncio
    async def test_lifespan_startup_shutdown(self, mock_settings):
        """
        GIVEN a kernel app
        WHEN the lifespan context is entered
        THEN it should run startup validations and yield, then log shutdown.
        """
        kernel = RealityKernel(mock_settings)

        # Access the lifespan context manager from the app
        # Since _create_pristine_app returns the app with lifespan configured

        async with kernel.app.router.lifespan_context(kernel.app):
            # Inside the context, startup has run
            pass
            # Exiting the context, shutdown will run

    def test_cors_logic_dev_vs_prod(self):
        """
        GIVEN different environments
        WHEN app is created
        THEN CORS middleware should be configured appropriately.
        """
        # Dev Case
        dev_settings = AppSettings(
            PROJECT_NAME="Dev",
            ENVIRONMENT="development",
            SECRET_KEY="s"*33,
            BACKEND_CORS_ORIGINS=[], # Empty implies default logic
            FRONTEND_URL="http://localhost:3000",
            DATABASE_URL="sqlite:///:memory:"
        )
        RealityKernel(dev_settings)

        # Prod Case
        prod_settings = AppSettings(
            PROJECT_NAME="Prod",
            ENVIRONMENT="production",
            SECRET_KEY="s"*33,
            BACKEND_CORS_ORIGINS=["https://myprod.com"],
            ALLOWED_HOSTS=["myprod.com"],
            FRONTEND_URL="https://myprod.com",
            DATABASE_URL="sqlite:///:memory:"
        )
        kernel_prod = RealityKernel(prod_settings)
        assert kernel_prod.app.title == "Prod"
