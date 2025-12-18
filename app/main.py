# app/main.py
"""
Entry point for the CogniForge Reality Kernel V3.
Handles application initialization, middleware weaving, and static file serving.
"""
import logging

from dotenv import load_dotenv
from fastapi import FastAPI

from app.core.di import get_settings
from app.core.static_handler import setup_static_files
from app.kernel import RealityKernel
from app.services.system_service import system_service

# Load .env file before anything else
load_dotenv()

logger = logging.getLogger(__name__)

# --- Kernel Singleton ---
# This ensures the kernel is created only once.
_kernel_instance = None


def get_kernel():
    global _kernel_instance
    if _kernel_instance is None:
        settings = get_settings()
        _kernel_instance = RealityKernel(settings.model_dump())
    return _kernel_instance


async def _health_check():
    """
    Enhanced health check for Phase 6 verification.
    Delegates to SystemService for integrity checks.
    """
    return await system_service.verify_system_integrity()


def _setup_monitoring(app: FastAPI):
    """Sets up monitoring endpoints (health check)"""
    app.add_api_route("/health", _health_check, methods=["GET"])


def create_app(static_dir: str | None = None) -> FastAPI:
    """
    Application factory. Creates and configures the FastAPI application
    by invoking the RealityKernel.
    """
    kernel = get_kernel()
    app = kernel.get_app()
    app.kernel = kernel  # type: ignore

    _setup_monitoring(app)
    # Delegate static file setup to the core handler
    setup_static_files(app, static_dir)

    return app


# The final, woven application instance.
app = create_app()
kernel = app.kernel  # Expose for legacy tests

# log startup
if hasattr(app, "logger"):
    app.logger.info("Application initialized with unified kernel middleware stack.")

if not isinstance(app, FastAPI):
    raise RuntimeError("CRITICAL: Reality Kernel failed to weave a valid FastAPI instance.")
