# app/main.py
import logging
import os
import pathlib

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
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

    # --- Static Files & SPA Support ---
    # User requirement: Serve app/static directly. No dist/. No build.
    # 1. Resolve static_dir
    static_files_dir = pathlib.Path(static_dir or os.path.join(os.getcwd(), "app/static")).resolve()

    if static_files_dir.exists() and static_files_dir.is_dir():
        # 2. Mount explicitly subfolders if they exist
        for folder in ["css", "js", "src"]:
            folder_path = static_files_dir / folder
            if folder_path.is_dir():
                app.mount(f"/{folder}", StaticFiles(directory=str(folder_path)), name=folder)

        # 3. Serve index.html at root - Support HEAD for availability checks
        @app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
        async def serve_root(request: Request):
            index_path = static_files_dir / "index.html"
            if index_path.exists() and index_path.is_file():
                return FileResponse(str(index_path))
            return HTMLResponse("<html><body><h1>404 - index.html not found</h1></body></html>", status_code=404)

        # 4. SPA catch-all route - Support HEAD
        @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], response_class=HTMLResponse)
        async def spa_fallback(request: Request, full_path: str):
            # If path starts with /api/ (or full_path.lstrip("/").startswith("api")) -> raise HTTPException(404)
            if full_path.startswith("api") or full_path.lstrip("/").startswith("api"):
                # Use JSON 404 for API
                raise HTTPException(status_code=404, detail="Not Found")

            # Normalize requested path and reject directory traversal
            try:
                requested_path = (static_files_dir / full_path).resolve()
            except Exception:
                 raise HTTPException(status_code=404, detail="Not Found")

            if not str(requested_path).startswith(str(static_files_dir)):
                raise HTTPException(status_code=404, detail="Not Found")

            # If resolved path is a file -> return that file
            if requested_path.is_file():
                return FileResponse(str(requested_path))

            # Else -> return index.html (if exists)
            index_path = static_files_dir / "index.html"
            if index_path.exists() and index_path.is_file():
                return FileResponse(str(index_path))

            # Else return clear HTML 404 message
            return HTMLResponse("<html><body><h1>404 - Not Found</h1></body></html>", status_code=404)

    else:
        logger.warning(
            f"Static files directory not found: {static_files_dir}. Frontend will not be served."
        )
        @app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
        async def serve_root_missing():
             return HTMLResponse("<html><body><h1>Static directory missing</h1></body></html>", status_code=404)


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
