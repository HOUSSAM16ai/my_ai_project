# app/main.py
"""
The main application entry point for the FastAPI service, orchestrated by the
Reality Kernel V3.
"""
from datetime import datetime, timezone
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.api.routers import admin, ai_service, chat, system, crud, observability, security, gateway
from app.kernel import kernel
from app.middleware.fastapi_error_handlers import add_error_handlers

# SERVICE ORCHESTRATION
kernel.app.mount("/static", StaticFiles(directory="app/static"), name="static")

add_error_handlers(kernel.app)

# Mount routers
kernel.app.include_router(system.router)
kernel.app.include_router(admin.router)
kernel.app.include_router(chat.router)
kernel.app.include_router(ai_service.router)
kernel.app.include_router(crud.router)
kernel.app.include_router(observability.router)
kernel.app.include_router(security.router)
kernel.app.include_router(gateway.router)


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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        status_code=200,
    )
