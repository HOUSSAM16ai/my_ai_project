# app/main.py
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.di import get_settings
from app.kernel import RealityKernel
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware

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

    # --- Static Files & SPA Support ---
    # User requirement: Serve app/static directly. No dist/. No build.
    static_files_dir = static_dir or os.path.join(os.getcwd(), "app/static")

    if os.path.exists(static_files_dir):
        # 1. Mount specific assets folders (css, js, src) so they are accessible
        for folder in ["css", "js", "src"]:
            folder_path = os.path.join(static_files_dir, folder)
            if os.path.isdir(folder_path):
                app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)

        # 2. Serve index.html at root
        @app.api_route("/", methods=["GET", "HEAD"])
        async def serve_root():
            return FileResponse(os.path.join(static_files_dir, "index.html"))

        # 3. SPA Fallback: serve index.html for non-API routes
        @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
        async def spa_fallback(full_path: str):
            # If path starts with api, return 404 (don't serve HTML)
            if full_path.startswith("api"):
                raise HTTPException(status_code=404, detail="Not Found")

            # Safety check for directory traversal
            potential_path = os.path.normpath(os.path.join(static_files_dir, full_path))
            if not potential_path.startswith(static_files_dir):
                # traversal attempt
                raise HTTPException(status_code=404, detail="Not Found")

            # If a specific file exists in static (e.g. /superhuman_dashboard.html), serve it
            if os.path.isfile(potential_path):
                return FileResponse(potential_path)

            # Otherwise serve index.html
            return FileResponse(os.path.join(static_files_dir, "index.html"))

    else:
        logger.warning(
            f"Static files directory not found: {static_files_dir}. Frontend will not be served."
        )

    return app


# The final, woven application instance.
app = create_app()
kernel = app.kernel  # Expose for legacy tests

app.add_middleware(RemoveBlockingHeadersMiddleware)
# log startup
if hasattr(app, "logger"):
    # Instantiate with app to avoid None, though Pure ASGI logic tolerates None for 'app' during check
    app.logger.info(
        "RemoveBlockingHeadersMiddleware enabled=%s", RemoveBlockingHeadersMiddleware(app).enabled
    )

if not isinstance(app, FastAPI):
    raise RuntimeError("CRITICAL: Reality Kernel failed to weave a valid FastAPI instance.")
