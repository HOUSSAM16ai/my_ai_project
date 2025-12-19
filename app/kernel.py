import importlib
import inspect
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.blueprints import Blueprint
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


class RealityKernel:
    """
    Cognitive Reality Weaver V4 (The Core Application Engine).

    The Reality Kernel acts as the central nervous system of the CogniForge application.
    It is designed to be the single source of truth for application initialization, ensuring
    consistency and stability across all services.

    Key Responsibilities (The Role):
    1.  **Application Factory**: It instantiates the FastAPI application, the heart of the system.
    2.  **Middleware Orchestration**: It layers essential middleware (Security, CORS, GZip) to protect and optimize traffic.
    3.  **Lifespan Management**: It governs the birth (startup) and death (shutdown) of the application, handling database connections and cleanup.
    4.  **Dynamic Routing (Weaving)**: It automatically discovers and registers "Blueprints" (modular routes), allowing the system to expand without modifying the core.

    Why this class exists:
    To decouple configuration and startup logic from the global scope, making the application
    testable, modular, and easy to configure for different environments (Dev, Test, Prod).
    """

    def __init__(self, settings: dict[str, Any]):
        """
        Initialize the Reality Kernel with the provided configuration.

        This constructor accepts a dictionary of settings, which allows dependency injection
        of configuration values. This is crucial for testing, where we might want to inject
        test-specific settings (like a test database URL) instead of loading them from the environment.

        Args:
            settings (dict[str, Any]): A dictionary containing application configuration (e.g., SECRET_KEY, DATABASE_URL).
        """
        self.settings = settings
        self.app: FastAPI = self._create_pristine_app()
        self._discover_and_weave_blueprints()

    def get_app(self) -> FastAPI:
        """Returns the fully woven FastAPI application."""
        return self.app

    def _create_pristine_app(self) -> FastAPI:
        """
        Creates the core FastAPI instance with essential configuration and middleware.
        """

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan handler - manages startup and shutdown logic."""
            async for _ in self._handle_lifespan_events():
                yield

        # Initialize FastAPI
        app = FastAPI(
            title=self.settings.get("PROJECT_NAME", "CogniForge"),
            version="v4.0-woven",
            docs_url="/docs" if self.settings.get("ENVIRONMENT") == "development" else None,
            redoc_url="/redoc" if self.settings.get("ENVIRONMENT") == "development" else None,
            lifespan=lifespan,
        )

        self._configure_middleware(app)
        add_error_handlers(app)

        return app

    async def _handle_lifespan_events(self):
        """Executes logic during application startup and shutdown."""
        # === STARTUP ===
        logger.info("🚀 CogniForge starting up...")

        # Schema Validation (Skipped in testing to save time/avoid conflicts)
        if self.settings.get("ENVIRONMENT") != "testing":
            try:
                # Import here to avoid circular dependencies or early DB init
                from app.core.database import validate_schema_on_startup
                await validate_schema_on_startup()
            except Exception as e:
                logger.warning(f"⚠️ Schema validation skipped or failed: {e}")

        logger.info("✅ CogniForge ready to serve requests")

        yield  # Application is running

        # === SHUTDOWN ===
        logger.info("👋 CogniForge shutting down...")

    def _configure_middleware(self, app: FastAPI):
        """Configures the middleware stack for the application."""

        # 1. Trusted Host
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=self.settings.get("ALLOWED_HOSTS", [])
        )

        # 2. CORS (Cross-Origin Resource Sharing)
        self._configure_cors(app)

        # 3. Security Headers
        app.add_middleware(SecurityHeadersMiddleware)

        # 4. Rate Limiting (Disabled in testing)
        if self.settings.get("ENVIRONMENT") != "testing":
            app.add_middleware(RateLimitMiddleware)

        # 5. Remove Blocking Headers (Dev/Codespaces support)
        # This wraps inner layers, so it ensures headers are stripped from responses
        app.add_middleware(RemoveBlockingHeadersMiddleware)

        # 6. GZip Compression
        app.add_middleware(GZipMiddleware, minimum_size=1000)

    def _configure_cors(self, app: FastAPI):
        """Configures CORS settings based on environment."""
        raw_origins = self.settings.get("BACKEND_CORS_ORIGINS", [])
        allow_origins = raw_origins if isinstance(raw_origins, list) else []

        # Fallback: If no explicit origins, derive from environment
        if not allow_origins:
            if self.settings.get("ENVIRONMENT") == "development":
                allow_origins = ["*"]
            else:
                allow_origins = [self.settings.get("FRONTEND_URL")]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "X-Requested-With",
                "X-CSRF-Token",
            ],
            expose_headers=["Content-Length", "Content-Range"],
        )

    def _discover_and_weave_blueprints(self):
        """
        Discovers and registers all blueprints from the app.blueprints package.
        Uses introspection to find Blueprint instances.
        """
        blueprints_path = os.path.join(os.path.dirname(__file__), "blueprints")
        logger.info(f"Reality Kernel: Weaving blueprints from {blueprints_path}")

        # Walk through the blueprints directory
        for _, _, files in os.walk(blueprints_path):
            for filename in files:
                if filename.endswith("_blueprint.py"):
                    self._load_blueprint_module(filename)

    def _load_blueprint_module(self, filename: str):
        """Helper to load a single blueprint module."""
        module_name = f"app.blueprints.{filename[:-3]}"
        try:
            module = importlib.import_module(module_name)
            # Inspect module members for Blueprint instances
            for _, obj in inspect.getmembers(module):
                if isinstance(obj, Blueprint):
                    self._register_blueprint(obj)
        except ImportError as e:
            logger.error(f"Failed to import blueprint module {module_name}: {e}")

    def _register_blueprint(self, blueprint: Blueprint):
        """Registers a single blueprint with the application."""
        logger.info(f"Weaving blueprint: {blueprint.name}")
        self.app.include_router(
            blueprint.router,
            prefix=f"/{blueprint.name}",
            tags=[blueprint.name.capitalize()]
        )
