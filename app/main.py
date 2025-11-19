# app/main.py
"""
The main application entry point for the FastAPI service, orchestrated by the
Reality Kernel V3.
"""

from fastapi.staticfiles import StaticFiles

from app.api.routers import admin, chat, system, ai_service
from app.kernel import kernel

# SERVICE ORCHESTRATION
kernel.app.mount("/static", StaticFiles(directory="app/static"), name="static")

kernel.app.include_router(system.router)
kernel.app.include_router(admin.router)
kernel.app.include_router(chat.router)
kernel.app.include_router(ai_service.router)


@kernel.app.get("/", summary="Root Endpoint", tags=["System"])
async def root():
    """
    Provides a basic welcome message and a link to the API documentation.
    """
    return {
        "message": "Welcome to the CogniForge Reality Kernel V3. See /docs for API documentation."
    }
