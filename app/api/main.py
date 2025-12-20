"""API Main Module - API router configuration and setup."""

from fastapi import FastAPI

from app.api.routers import system


def create_app():
    app = FastAPI()
    app.include_router(system.router)
    return app
