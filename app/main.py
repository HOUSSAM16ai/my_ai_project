# app/main.py
import logging
import os
import pathlib

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

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

    # --- Static Files & SPA Support ---
    # Determine the directory where built assets are located (e.g., app/static/dist)
    base_dir = pathlib.Path(__file__).parent.resolve()
    # If static_dir is provided (e.g. testing), use it. Otherwise default to app/static/dist
    dist_dir = pathlib.Path(static_dir) if static_dir else base_dir / "static" / "dist"

    # 1. Mount assets explicitly. Vite builds assets to /assets, so we serve them at /assets.
    assets_dir = dist_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        logger.info(f"Mounted /assets from {assets_dir}")
    else:
        logger.warning(f"Assets directory not found: {assets_dir}. SPA may not render correctly.")

    # 2. Serve index.html at root
    index_file = dist_dir / "index.html"

    @app.get("/", response_class=HTMLResponse)
    async def read_index():
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse("<h1>Backend Running. Frontend not built.</h1>", status_code=404)

    # 3. SPA Catch-All: For any other path, check if it's a file in dist, else serve index.html
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def spa_catch_all(full_path: str):
        # Prevent accessing API routes via catch-all (though specific routes match first)
        if full_path.startswith("api/") or full_path.startswith("system/"):
             return JSONResponse({"detail": "Not Found"}, status_code=404)

        candidate = dist_dir / full_path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)

        # Fallback to index.html for client-side routing
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse({"detail": "Frontend not found"}, status_code=404)

    return app


# The final, woven application instance.
app = create_app()
kernel = app.kernel  # Expose for legacy tests

from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware

app.add_middleware(RemoveBlockingHeadersMiddleware)
# log startup
if hasattr(app, "logger"):
    # Instantiate with app to avoid None, though Pure ASGI logic tolerates None for 'app' during check
    app.logger.info("RemoveBlockingHeadersMiddleware enabled=%s", RemoveBlockingHeadersMiddleware(app).enabled)

if not isinstance(app, FastAPI):
    raise RuntimeError("CRITICAL: Reality Kernel failed to weave a valid FastAPI instance.")
