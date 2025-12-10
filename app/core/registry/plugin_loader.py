"""
Plugin Loader - محمل الإضافات
================================

تحميل الإضافات مع معالجة الاعتماديات
Load plugins with dependency resolution

مبدأ البساطة: Simple dependency resolution
"""

import logging
from typing import Any, Dict, Optional

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
    
    async def load(
        self, 
        plugin: IPlugin, 
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        تحميل إضافة
        Load a plugin with its dependencies
        """
        name = plugin.name
        
        # Already loaded
        if name in self._loaded:
            logger.debug(f"Plugin '{name}' already loaded")
            return True
        
        # Load dependencies first
        deps = plugin.dependencies
        for dep_name in deps:
            dep_plugin = registry.get(dep_name)
            if not dep_plugin:
                logger.error(
                    f"Missing dependency '{dep_name}' for plugin '{name}'"
                )
                return False
            
            # Recursive load
            if not await self.load(dep_plugin):
                return False
        
        # Configure plugin
        if config:
            plugin.configure(config)
        
        # Initialize plugin
        try:
            await plugin.initialize()
            self._loaded.add(name)
            logger.info(f"Plugin '{name}' loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin '{name}': {e}")
            return False
    
    async def unload(self, plugin: IPlugin) -> bool:
        """Unload plugin"""
        name = plugin.name
        
        if name not in self._loaded:
            return False
        
        try:
            await plugin.shutdown()
            self._loaded.remove(name)
            logger.info(f"Plugin '{name}' unloaded")
            return True
        except Exception as e:
            logger.error(f"Failed to unload plugin '{name}': {e}")
            return False
    
    def is_loaded(self, name: str) -> bool:
        """Check if plugin is loaded"""
        return name in self._loaded
    
    def get_loaded(self) -> set[str]:
        """Get all loaded plugin names"""
        return self._loaded.copy()
