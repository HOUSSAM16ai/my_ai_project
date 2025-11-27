# app/main.py
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.di import get_settings
from app.kernel import RealityKernel

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


def create_app(static_dir: str | None = None) -> FastAPI:
    """
    Application factory. Creates and configures the FastAPI application
    by invoking the RealityKernel.
    """
    kernel = get_kernel()
    app = kernel.get_app()
    app.kernel = kernel  # type: ignore

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "backend running"}

    # --- Static Files ---
    static_files_dir = static_dir or os.path.join(os.getcwd(), "app/static/dist")
    if os.path.exists(static_files_dir):
        app.mount("/", StaticFiles(directory=static_files_dir, html=True), name="static")
    else:
        logger.warning(
            f"Static files directory not found: {static_files_dir}. Frontend will not be served."
        )

    return app


# The final, woven application instance.
app = create_app()
kernel = app.kernel  # Expose for legacy tests

if os.environ.get("ENVIRONMENT", "") == "development":
    from app.dev_frame_middleware import DevAllowIframeMiddleware
    app.add_middleware(DevAllowIframeMiddleware)

if not isinstance(app, FastAPI):
    raise RuntimeError("CRITICAL: Reality Kernel failed to weave a valid FastAPI instance.")
