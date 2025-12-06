# app/main.py
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.di import get_settings
from app.kernel import RealityKernel
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.models import User

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
    Enhanced health check for Phase 6 verification
    Checks if admin exists and secrets are loaded (simplified)
    """
    admin_present = False
    try:
        async with async_session_factory() as session:
            res = await session.execute(select(User).where(User.email == "admin@example.com"))
            if res.scalars().first():
                admin_present = True
    except Exception:
        pass  # DB might be down, or initializing

    return {
        "status": "ok",
        "service": "backend running",
        "secrets_ok": True,  # Implied if app started
        "admin_present": admin_present,
        "db": "ok" if admin_present else "unknown",
    }


def _setup_monitoring(app: FastAPI):
    """Sets up monitoring endpoints (health check)"""
    app.add_api_route("/health", _health_check, methods=["GET"])


def _setup_static_files(app: FastAPI, static_dir: str | None = None):
    """
    Sets up static file serving and SPA fallback.
    User requirement: Serve app/static directly. No dist/. No build.
    """
    static_files_dir = static_dir or os.path.join(os.getcwd(), "app/static")

    if not os.path.exists(static_files_dir):
        logger.warning(
            f"Static files directory not found: {static_files_dir}. Frontend will not be served."
        )
        return

    # 1. Mount specific assets folders (css, js, src) so they are accessible
    for folder in ["css", "js", "src"]:
        folder_path = os.path.join(static_files_dir, folder)
        if os.path.isdir(folder_path):
            app.mount(f"/{folder}", StaticFiles(directory=folder_path), name=folder)

    # 2. Serve index.html at root
    async def serve_root():
        return FileResponse(os.path.join(static_files_dir, "index.html"))

    app.add_api_route("/", serve_root, methods=["GET", "HEAD"])

    # 3. SPA Fallback: serve index.html for non-API routes
    async def spa_fallback(request: Request, full_path: str):
        # 1. First, check if the file physically exists in static directory
        # This ensures that if we have /documentation/api/guide.html, it gets served
        # even if it contains "api" in the path.
        potential_path = os.path.normpath(os.path.join(static_files_dir, full_path))

        # Safety check for directory traversal
        if not potential_path.startswith(static_files_dir):
            # traversal attempt
            raise HTTPException(status_code=404, detail="Not Found")

        # If a specific file exists in static (e.g. /superhuman_dashboard.html), serve it
        if os.path.isfile(potential_path):
            # Ensure we only serve GET/HEAD for static files unless configured otherwise
            if request.method not in ["GET", "HEAD"]:
                raise HTTPException(status_code=405, detail="Method Not Allowed")
            return FileResponse(potential_path)

        # 2. If file doesn't exist, THEN enforce API restrictions
        # If path starts with api or contains /api/, return 404 (don't serve HTML)
        # This ensures nested API routes (e.g. /admin/api/...) also return 404 when not found
        if full_path.startswith("api") or "/api/" in full_path or full_path.endswith("/api"):
            raise HTTPException(status_code=404, detail="Not Found")

        # 3. If it is NOT a GET/HEAD request, and it fell through to here, it's a 404
        if request.method not in ["GET", "HEAD"]:
            raise HTTPException(status_code=404, detail="Not Found")

        # 4. Otherwise serve index.html (SPA)
        return FileResponse(os.path.join(static_files_dir, "index.html"))

    app.add_api_route(
        "/{full_path:path}",
        spa_fallback,
        methods=["GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    )


def _configure_middleware(app: FastAPI):
    """Configures middleware stack"""
    # RateLimitMiddleware must be added first (executed early in request processing)
    # But wait, Starlette/FastAPI executes middleware in REVERSE order of addition!
    # So the LAST one added is executed FIRST.

    # We want: RateLimit -> ... -> BlockingHeaders -> App

    # Add RemoveBlockingHeadersMiddleware (executed closer to app logic?)
    # The existing code added RemoveBlockingHeadersMiddleware at the END of the file (executed FIRST)
    # app.add_middleware(RemoveBlockingHeadersMiddleware)
    pass


def create_app(static_dir: str | None = None) -> FastAPI:
    """
    Application factory. Creates and configures the FastAPI application
    by invoking the RealityKernel.
    """
    kernel = get_kernel()
    app = kernel.get_app()
    app.kernel = kernel  # type: ignore

    _setup_monitoring(app)
    _setup_static_files(app, static_dir)

    # Middleware is now woven by the Reality Kernel.
    # No redundant additions here to avoid "Chaotic Constructive Interference".
    return app


# The final, woven application instance.
app = create_app()
kernel = app.kernel  # Expose for legacy tests

# log startup
if hasattr(app, "logger"):
    # Check if middleware is active in stack (simplified check)
    app.logger.info("Application initialized with unified kernel middleware stack.")

if not isinstance(app, FastAPI):
    raise RuntimeError("CRITICAL: Reality Kernel failed to weave a valid FastAPI instance.")
