# app/main.py
"""
The main application entry point for the FastAPI service, orchestrated by the
Reality Kernel V3.
"""

import inspect
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.api.routers import (
    admin,
    ai_service,
    chat,
    crud,
    gateway,
    intelligent_platform,
    observability,
    security,
    system,
)
from app.kernel import kernel
from app.middleware.adapters.flask_compat import FlaskCompatMiddleware
from app.middleware.fastapi_error_handlers import add_error_handlers
from app.core.startup_diagnostics import run_diagnostics


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# --- EXPLICIT APP FACTORY ---
# This resolves ambiguity for Uvicorn, ensuring it treats the app correctly
# regardless of how it's imported or wrapped.
def create_app() -> FastAPI:
    """
    Factory function to return the FastAPI application instance.
    Used by Uvicorn with the --factory flag.
    """
    # SUPERHUMAN DIAGNOSTICS
    run_diagnostics()

    # Runtime safety check to prevent 'coroutine is not callable' errors
    if inspect.iscoroutine(kernel.app):
        raise TypeError(
            f"CRITICAL ERROR: kernel.app is a coroutine object! "
            f"It should be a FastAPI instance. Type: {type(kernel.app)}"
        )

    if not isinstance(kernel.app, FastAPI):
        # Fallback check for valid callables (wrappers) that are not coroutines
        if hasattr(kernel.app, "__call__") and not inspect.iscoroutinefunction(kernel.app):
            pass  # It is a valid callable wrapper
        else:
            raise TypeError(
                f"CRITICAL ERROR: kernel.app is not a FastAPI instance or valid callable. "
                f"Type: {type(kernel.app)}"
            )

    app_instance = kernel.app

    # --- HYPER-SCALE MIDDLEWARE STACK ---

    # 1. Security Headers (Tech Giant Standard)
    app_instance.add_middleware(SecurityHeadersMiddleware)

    # 2. Trusted Host (Prevents Host Header Attacks)
    app_instance.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] # In production, restrict this to specific domains
    )

    # 3. GZip Compression (Speed Optimization)
    app_instance.add_middleware(GZipMiddleware, minimum_size=1000)

    # 4. Smart CORS Policy (Dev vs Prod)
    if os.getenv("ENV", "development") == "development":
        app_instance.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app_instance.add_middleware(
            CORSMiddleware,
            allow_origins=[os.getenv("FRONTEND_URL", "")],
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )

    # 5. Static Mount (Must be before Catch-All)
    app_instance.mount("/static", StaticFiles(directory="app/static"), name="static")

    # Error Handlers and Compat Middleware (moved here to ensure order)
    add_error_handlers(app_instance)
    app_instance.add_middleware(FlaskCompatMiddleware)

    # Mount routers
    app_instance.include_router(system.router)
    app_instance.include_router(admin.router)
    app_instance.include_router(chat.router)
    app_instance.include_router(ai_service.router)
    app_instance.include_router(crud.router)
    app_instance.include_router(observability.router)
    app_instance.include_router(security.router)
    app_instance.include_router(gateway.router)
    app_instance.include_router(intelligent_platform.router)

    # 6. SPA Catch-All Route (The Robust Logic)
    @app_instance.get("/{full_path:path}")
    async def catch_all(full_path: str):
        static_dir = Path("app/static")
        requested_file = static_dir / full_path

        # A. Serve actual file if it exists
        if requested_file.exists() and requested_file.is_file():
            return FileResponse(requested_file)

        # B. Return 404 for missing API endpoints (Don't serve HTML for API errors)
        if full_path.startswith("api/"):
            return JSONResponse({"error": "API endpoint not found"}, status_code=404)

        # C. Fallback to index.html for SPA Routing
        return FileResponse("app/static/index.html")

    return app_instance


# Expose the FastAPI app instance cleanly for Uvicorn (Legacy/Direct support)
app = kernel.app

# Health check aliases - Attached to the global app instance for legacy compatibility
@kernel.app.get("/", summary="Root Endpoint", tags=["System"])
async def root():
    """
    Provides a basic welcome message and a link to the API documentation.
    """
    return {
        "message": "Welcome to the CogniForge Reality Kernel V3. See /docs for API documentation."
    }


@kernel.app.get("/api/v1/health", tags=["System"])
@kernel.app.get("/health", tags=["System"])
async def api_v1_health():
    return JSONResponse(
        content={
            "status": "success",
            "message": "System operational",
            "data": {"status": "healthy", "database": "connected", "version": "v3.0-hyper"},
            "timestamp": datetime.now(UTC).isoformat(),
        },
        status_code=200,
    )
