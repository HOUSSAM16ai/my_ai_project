# app/kernel.py
import importlib
import inspect
import logging
import os
from typing import Any

from fastapi import FastAPI

from app.blueprints import Blueprint

logger = logging.getLogger(__name__)


class RealityKernel:
    """
    Cognitive Reality Weaver V4.
    Dynamically discovers and weaves application blueprints into a cohesive FastAPI application.
    This kernel is the true central execution spine.
    """

    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.app: FastAPI = self._create_pristine_app()
        self._discover_and_weave_blueprints()

    def _create_pristine_app(self) -> FastAPI:
        """Creates the core FastAPI instance with essential middleware."""
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.middleware.gzip import GZipMiddleware
        from fastapi.middleware.trustedhost import TrustedHostMiddleware

        from app.middleware.fastapi_error_handlers import add_error_handlers
        from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
        from app.middleware.security.security_headers import SecurityHeadersMiddleware

        app = FastAPI(
            title=self.settings.get("PROJECT_NAME", "CogniForge"),
            version="v4.0-woven",
            docs_url="/docs" if self.settings.get("ENVIRONMENT") == "development" else None,
            redoc_url="/redoc" if self.settings.get("ENVIRONMENT") == "development" else None,
        )

        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=self.settings.get("ALLOWED_HOSTS", [])
        )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"]
            if self.settings.get("ENVIRONMENT") == "development"
            else [self.settings.get("FRONTEND_URL")],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        app.add_middleware(SecurityHeadersMiddleware)
        if self.settings.get("ENVIRONMENT") != "testing":
            app.add_middleware(RateLimitMiddleware)
        app.add_middleware(GZipMiddleware, minimum_size=1000)

        add_error_handlers(app)

        return app

    def _discover_and_weave_blueprints(self):
        """Discovers and registers all blueprints from the app.blueprints package."""
        blueprints_path = os.path.join(os.path.dirname(__file__), "blueprints")
        logger.info(f"Reality Kernel: Weaving blueprints from {blueprints_path}")

        for _, _, files in os.walk(blueprints_path):
            for filename in files:
                if filename.endswith("_blueprint.py"):
                    module_name = f"app.blueprints.{filename[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for _, obj in inspect.getmembers(module):
                            if isinstance(obj, Blueprint):
                                logger.info(f"Weaving blueprint: {obj.name}")
                                self.app.include_router(
                                    obj.router, prefix=f"/{obj.name}", tags=[obj.name.capitalize()]
                                )
                    except ImportError as e:
                        logger.error(f"Failed to import blueprint module {module_name}: {e}")

    def get_app(self) -> FastAPI:
        """Returns the fully woven FastAPI application."""
        return self.app
