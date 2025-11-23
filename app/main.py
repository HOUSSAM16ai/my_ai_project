# app/main.py
"""
The main application entry point for the FastAPI service, orchestrated by the
Reality Kernel V3.
"""

import inspect
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

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

# SERVICE ORCHESTRATION
kernel.app.mount("/static", StaticFiles(directory="app/static"), name="static")

add_error_handlers(kernel.app)
kernel.app.add_middleware(FlaskCompatMiddleware)

# Mount routers
kernel.app.include_router(system.router)
kernel.app.include_router(admin.router)
kernel.app.include_router(chat.router)
kernel.app.include_router(ai_service.router)
kernel.app.include_router(crud.router)
kernel.app.include_router(observability.router)
kernel.app.include_router(security.router)
kernel.app.include_router(gateway.router)
kernel.app.include_router(intelligent_platform.router)


@kernel.app.get("/", summary="Root Endpoint", tags=["System"])
async def root():
    """
    Provides a basic welcome message and a link to the API documentation.
    """
    return {
        "message": "Welcome to the CogniForge Reality Kernel V3. See /docs for API documentation."
    }


# Health check aliases
@kernel.app.get("/api/v1/health", tags=["System"])
@kernel.app.get("/health", tags=["System"])
async def api_v1_health():
    return JSONResponse(
        content={
            "status": "success",
            "message": "System operational",
            "data": {"status": "healthy", "database": "connected", "version": "v1.0"},
            "timestamp": datetime.now(UTC).isoformat(),
        },
        status_code=200,
    )


# --- EXPLICIT APP FACTORY ---
# This resolves ambiguity for Uvicorn, ensuring it treats the app correctly
# regardless of how it's imported or wrapped.
def create_app() -> FastAPI:
    """
    Factory function to return the FastAPI application instance.
    Used by Uvicorn with the --factory flag.
    """
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

    return kernel.app


# Expose the FastAPI app instance cleanly for Uvicorn (Legacy/Direct support)
app = kernel.app
