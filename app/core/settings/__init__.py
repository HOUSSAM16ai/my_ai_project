__all__ = ["BaseServiceSettings"]


def __getattr__(name: str) -> object:
    """يوفر استيرادًا كسولًا لتجنّب تحميل الإعدادات الثقيلة عند الحاجة فقط."""
    if name == "BaseServiceSettings":
        from .base import BaseServiceSettings

        return BaseServiceSettings
    raise AttributeError(f"module 'app.core.settings' has no attribute {name!r}")
