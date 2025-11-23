# app/core/config.py
"""
COMPATIBILITY LAYER.

This module is deprecated. Use app.config.settings instead.
It redirects calls to the new Superhuman Configuration Nexus.
"""
from app.config.settings import AppSettings as Settings
from app.config.settings import get_settings

# Re-export generic settings instance for legacy consumers
settings = get_settings()

__all__ = ["Settings", "get_settings", "settings"]
