# app/__init__.py
"""App package initializer."""

__all__ = ["api", "kernel", "models", "services"]


def __getattr__(name: str) -> object:
    """يوفر تحميلًا كسولًا للوحدات الثقيلة لتجنّب الآثار الجانبية عند الاستيراد."""
    if name == "models":
        from app.core.domain import models

        return models
    raise AttributeError(f"module 'app' has no attribute {name!r}")
