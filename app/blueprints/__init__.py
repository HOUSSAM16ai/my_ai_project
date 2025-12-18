# app/blueprints/__init__.py
"""Blueprints - Modular API route organization."""
from fastapi import APIRouter


class Blueprint:
    """A blueprint is a self-contained module of the application."""

    def __init__(self, name: str):
        self.name = name
        self.router = APIRouter()

    def register(self, app):
        """Registers the blueprint with the FastAPI application."""
        app.include_router(self.router)
