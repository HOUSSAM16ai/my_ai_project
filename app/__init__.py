# app/__init__.py
"""App package initializer."""

# Removed the side-effect import of models that was causing circular dependencies and
# ImportErrors when running isolated tests.
# from app.core.domain import models

__all__ = ["api", "kernel", "services"]
