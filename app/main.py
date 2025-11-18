# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routers import admin, chat, system

app = FastAPI(title="CogniForge - Unified ASGI Service")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include modular routers
app.include_router(system.router)
app.include_router(admin.router)
app.include_router(chat.router)


@app.get("/", summary="Root Endpoint", tags=["System"])
async def root():
    """
    Provides a basic welcome message and a link to the API documentation.
    """
    return {
        "message": "Welcome to the CogniForge ASGI service. See /docs for API documentation."
    }
