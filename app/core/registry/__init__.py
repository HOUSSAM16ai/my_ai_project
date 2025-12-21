"""
Plugin Registry - سجل الإضافات
=================================

نظام تسجيل واكتشاف الإضافات الآلي
Automatic Plugin Discovery and Registration System
"""

from app.core.registry.plugin_discovery import discover_plugins
from app.core.registry.plugin_loader import PluginLoader
from app.core.registry.plugin_registry import PluginRegistry

__all__ = [
    "PluginRegistry",
    "PluginLoader",
    "discover_plugins",
]
