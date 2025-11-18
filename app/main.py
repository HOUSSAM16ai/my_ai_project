# app/main.py
"""
The main application entry point for the FastAPI service.

This file orchestrates the inclusion of modular routers and mounts static files,
but it defers the creation of the application object to the Reality Kernel.
"""

from fastapi.staticfiles import StaticFiles

from app.api.routers import admin, chat, system, ai_service
from app.kernel import app

# ======================================================================================
# SERVICE ORCHESTRATION
# ======================================================================================
# The Reality Kernel (`app`) is the single source of truth. Here, we attach
# the service-specific components to it.

# Mount static files for serving frontend assets
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include modular API routers
# These routers define the specific API endpoints for different domains.
app.include_router(system.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(ai_service.router)


# ======================================================================================
# ROOT ENDPOINT
# ======================================================================================
@app.get("/", summary="Root Endpoint", tags=["System"])
async def root():
    """
    Provides a basic welcome message and a link to the API documentation.
    This serves as a simple health check and discovery endpoint.
    """

    return {
        "message": "Welcome to the CogniForge Unified Reality Kernel. See /docs for API documentation."
    }
