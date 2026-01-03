# app/__init__.py
"""App package initializer."""

# Import models from the correct location for backward compatibility
from app.core.domain import models

__all__ = ["api", "kernel", "models", "services"]
