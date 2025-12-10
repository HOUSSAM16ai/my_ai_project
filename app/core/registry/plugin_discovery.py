"""
Plugin Discovery - اكتشاف الإضافات
====================================

اكتشاف تلقائي للإضافات من المجلدات
Automatic plugin discovery from directories

مبدأ البساطة: Convention over Configuration
"""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.interfaces import IPlugin
from app.core.registry.plugin_registry import registry

logger = logging.getLogger(__name__)


def discover_plugins(
    plugin_dir: str = "app.plugins",
    auto_register: bool = True
) -> List[IPlugin]:
    """
    اكتشاف جميع الإضافات
    Discover all plugins in directory
    
    Convention: Each plugin module must have a 'plugin' variable
    that contains the plugin instance.
    
    Example:
        app/plugins/chat/plugin.py:
            from .service import ChatPlugin
            plugin = ChatPlugin()
    """
    discovered: List[IPlugin] = []
    
    try:
        # Import plugin package
        package = importlib.import_module(plugin_dir)
        package_path = Path(package.__file__).parent
        
        # Iterate through all submodules
        for _, module_name, is_pkg in pkgutil.iter_modules(
            [str(package_path)]
        ):
            if not is_pkg:
                continue
            
            try:
                # Import plugin module
                full_name = f"{plugin_dir}.{module_name}"
                plugin_module = importlib.import_module(
                    f"{full_name}.plugin"
                )
                
                # Get plugin instance
                if hasattr(plugin_module, 'plugin'):
                    plugin = plugin_module.plugin
                    
                    if isinstance(plugin, IPlugin):
                        discovered.append(plugin)
                        
                        # Auto-register
                        if auto_register:
                            registry.register(plugin)
                            logger.info(
                                f"Discovered and registered: "
                                f"{plugin.name}"
                            )
                    else:
                        logger.warning(
                            f"Module {full_name} has 'plugin' "
                            f"but it's not IPlugin"
                        )
                        
            except ImportError as e:
                logger.debug(
                    f"No plugin in {module_name}: {e}"
                )
            except Exception as e:
                logger.error(
                    f"Error loading plugin {module_name}: {e}"
                )
    
    except ImportError:
        logger.warning(f"Plugin directory '{plugin_dir}' not found")
    
    return discovered


def discover_and_configure(
    plugin_dir: str = "app.plugins",
    config: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[IPlugin]:
    """
    اكتشاف وتكوين الإضافات
    Discover and configure plugins
    """
    plugins = discover_plugins(plugin_dir, auto_register=True)
    
    if config:
        for plugin in plugins:
            plugin_config = config.get(plugin.name, {})
            if plugin_config:
                plugin.configure(plugin_config)
    
    return plugins
