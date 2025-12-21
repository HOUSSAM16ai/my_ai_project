"""
Plugin Loader - محمل الإضافات
================================

تحميل الإضافات مع معالجة الاعتماديات
Load plugins with dependency resolution

مبدأ البساطة: Simple dependency resolution
"""
import logging
from typing import Any

from app.core.interfaces import IPlugin
from app.core.registry.plugin_registry import registry

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    محمل الإضافات
    Plugin Loader with dependency resolution
    """

    def __init__(self):
        self._loaded: set[str] = set()

    async def load(self, plugin: IPlugin, config: dict[str, Any] | None=None
        ) ->bool:
        """
        تحميل إضافة
        Load a plugin with its dependencies
        """
        name = plugin.name
        if name in self._loaded:
            logger.debug(f"Plugin '{name}' already loaded")
            return True
        deps = plugin.dependencies
        for dep_name in deps:
            dep_plugin = registry.get(dep_name)
            if not dep_plugin:
                logger.error(
                    f"Missing dependency '{dep_name}' for plugin '{name}'")
                return False
            if not await self.load(dep_plugin):
                return False
        if config:
            plugin.configure(config)
        try:
            await plugin.initialize()
            self._loaded.add(name)
            logger.info(f"Plugin '{name}' loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin '{name}': {e}")
            return False
