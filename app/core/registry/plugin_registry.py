"""
Plugin Registry - سجل الإضافات المركزي
========================================

مركز تسجيل وإدارة جميع الإضافات
Central registration and management of all plugins

مبدأ البساطة: Singleton Pattern بسيط وواضح
"""

from typing import Any, Dict, Optional, Type

from app.core.interfaces import IPlugin


class PluginRegistry:
    """
    سجل الإضافات المركزي
    Central Plugin Registry
    
    Thread-safe singleton for managing all plugins.
    """
    
    _instance: Optional['PluginRegistry'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._plugins: Dict[str, IPlugin] = {}
            self._metadata: Dict[str, Dict[str, Any]] = {}
            self._initialized = True
    
    def register(
        self, 
        plugin: IPlugin, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        تسجيل إضافة جديدة
        Register a new plugin
        """
        name = plugin.name
        
        if name in self._plugins:
            raise ValueError(f"Plugin '{name}' already registered")
        
        self._plugins[name] = plugin
        self._metadata[name] = metadata or {}
    
    def get(self, name: str) -> Optional[IPlugin]:
        """Get plugin by name"""
        return self._plugins.get(name)
    
    def get_all(self) -> Dict[str, IPlugin]:
        """Get all registered plugins"""
        return self._plugins.copy()
    
    def get_by_type(self, plugin_type: str) -> list[IPlugin]:
        """Get all plugins of specific type"""
        return [
            p for p in self._plugins.values() 
            if p.plugin_type == plugin_type
        ]
    
    def unregister(self, name: str) -> bool:
        """Unregister plugin"""
        if name in self._plugins:
            del self._plugins[name]
            self._metadata.pop(name, None)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all plugins (for testing)"""
        self._plugins.clear()
        self._metadata.clear()
    
    def get_metadata(self, name: str) -> Dict[str, Any]:
        """Get plugin metadata"""
        return self._metadata.get(name, {})


# Global registry instance
registry = PluginRegistry()
