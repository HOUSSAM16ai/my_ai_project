# app/__init__.py
"""App package initializer."""

from app.core.domain import models

__all__ = ["api", "kernel", "models", "services"]
