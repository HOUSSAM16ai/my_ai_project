import inspect
import logging
from contextlib import asynccontextmanager
from datetime import UTC

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# --- Routers ---
from app.api.routers import (
    admin,
    crud,
    gateway,
    intelligent_platform,
    observability,
    system,
)
from app.api.routers import (
    security as auth,
)
from app.core.di import get_settings
import app.models
from app.core.startup_diagnostics import run_diagnostics
from app.kernel import RealityKernel

# from app.middleware.adapters.flask_compat import FlaskCompatMiddleware
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    settings = get_settings()
    logger.info(f"Starting CogniForge (Environment: {settings.ENVIRONMENT})")

    # Run diagnostics
    await run_diagnostics()

    yield

    # Shutdown
    logger.info("Shutting down CogniForge...")


def create_app() -> FastAPI:
    """
    Factory function to create the FastAPI application.
    This ensures a fresh instance for every test/run.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="v3.0-hyper",
        description="CogniForge Unified AI Platform",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    )

    # --- Middleware Stack ---
    # 1. Trusted Host (Security)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

    # 2. CORS (Connectivity)
    # Allow all in dev, restrict in prod
    allow_origins = ["*"] if settings.ENVIRONMENT == "development" else [settings.FRONTEND_URL]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 3. Security Headers (Hardening)
    app.add_middleware(SecurityHeadersMiddleware)

    # 4. Rate Limiting (Protection) - Conditional
    if settings.ENVIRONMENT != "testing":
        app.add_middleware(RateLimitMiddleware)

    # 5. Compression (Performance)
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 6. Flask Compatibility (Legacy Support)
    # app.add_middleware(FlaskCompatMiddleware)

    # --- Router Mounting ---
    app.include_router(system.router)
    app.include_router(auth.router)
    app.include_router(admin.router)
    app.include_router(intelligent_platform.router)
    app.include_router(crud.router)
    app.include_router(gateway.router)
    app.include_router(observability.router)

    # --- API v1 Health Check (Legacy Support) ---
    @app.get("/api/v1/health", tags=["System"])
    async def health_check_v1():
        from datetime import datetime

        return {
            "status": "success",
            "message": "System operational",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {"status": "healthy", "database": "connected", "version": "v3.0-hyper"},
        }

    # --- Static Files (Frontend) ---
    import os

    static_dir = os.path.join(os.getcwd(), "app/static")
    dist_dir = os.path.join(static_dir, "dist")

    if os.path.exists(dist_dir):
        app.mount("/static", StaticFiles(directory=dist_dir), name="static")
    elif os.path.exists(static_dir):
        # Fallback to source if dist not built (dev mode)
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # --- SPA Catch-All ---
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        if full_path.startswith("api/"):
            return JSONResponse({"error": "Not Found"}, status_code=404)

        # Serve index.html
        index_path = os.path.join(
            dist_dir if os.path.exists(dist_dir) else static_dir, "index.html"
        )
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse({"error": "Frontend not built"}, status_code=503)

    # --- Error Handlers ---
    add_error_handlers(app)

    return app


# --- Reality Kernel Integration ---
# Ensure the kernel has a valid app reference for singletons
kernel = RealityKernel()
kernel.app = create_app()

# Runtime Assertion
if not isinstance(kernel.app, FastAPI):
    # Fallback check for valid callables (wrappers) that are not coroutines
    if callable(kernel.app) and not inspect.iscoroutinefunction(kernel.app):
        pass  # It is a valid callable wrapper
    else:
        # If it's not a FastAPI instance and not a callable wrapper, panic.
        raise RuntimeError("CRITICAL: Reality Kernel failed to initialize FastAPI instance.")
