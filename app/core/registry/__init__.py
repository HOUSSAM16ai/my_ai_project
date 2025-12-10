"""
Plugin Registry - سجل الإضافات
=================================

نظام تسجيل واكتشاف الإضافات الآلي
Automatic Plugin Discovery and Registration System
"""

from app.core.registry.plugin_registry import PluginRegistry
from app.core.registry.plugin_loader import PluginLoader
from app.core.registry.plugin_discovery import discover_plugins

__all__ = [
    "PluginRegistry",
    "PluginLoader",
    "discover_plugins",
]
