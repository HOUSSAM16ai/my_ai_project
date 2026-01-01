# app/middleware/config/middleware_settings.py
# ======================================================================================
# ==                    MIDDLEWARE SETTINGS (v∞)                                    ==
# ======================================================================================
"""
إعدادات الوسيط - Middleware Settings

Configuration model for middleware system.
"""
from typing import Any

class MiddlewareSettings:
    """
    Middleware Settings

    Centralized configuration for the middleware system.
    """

    def __init__(self, **kwargs):
        """
        Initialize settings

        Args:
            **kwargs: Configuration parameters
        """
        self.config: dict[str, Any] = kwargs

    def get(self, key: str, default: dict[str, str | int | bool] = None) -> dict[str, str | int | bool]:
        """
        Get configuration value

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        return self.config.get(key, default)

    def set(self, key: str, value: dict[str, str | int | bool]) -> None:
        """
        Set configuration value

        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary"""
        return self.config.copy()
