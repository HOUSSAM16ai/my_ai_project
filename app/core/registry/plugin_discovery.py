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
from types import ModuleType

from app.core.protocols import PluginProtocol as IPlugin
from app.core.registry.plugin_registry import registry

logger = logging.getLogger(__name__)


def _load_plugin_module(plugin_dir: str, module_name: str) -> tuple[ModuleType, str] | None:
    """
    Attempt to import the plugin module.
    """
    full_name = f"{plugin_dir}.{module_name}"
    try:
        return importlib.import_module(f"{full_name}.plugin"), full_name
    except ImportError as e:
        logger.debug(f"No plugin in {module_name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading plugin {module_name}: {e}")
        return None


def _extract_plugin_instance(plugin_module: ModuleType, full_name: str) -> IPlugin | None:
    """
    Extract and validate the plugin instance from the module.
    """
    if not hasattr(plugin_module, "plugin"):
        return None

    plugin = plugin_module.plugin
    if isinstance(plugin, IPlugin):
        return plugin

    logger.warning(f"Module {full_name} has 'plugin' but it's not IPlugin")
    return None


def _register_plugin(plugin: IPlugin) -> None:
    """
    Register the plugin with the registry.
    """
    registry.register(plugin)
    logger.info(f"Discovered and registered: {plugin.name}")


def discover_plugins(plugin_dir: str = "app.plugins", auto_register: bool = True) -> list[IPlugin]:
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
    discovered: list[IPlugin] = []
    try:
        package = importlib.import_module(plugin_dir)
        if not package.__file__:
            logger.warning(f"Plugin package '{plugin_dir}' has no file attribute")
            return discovered
        package_path = Path(package.__file__).parent
    except ImportError:
        logger.warning(f"Plugin directory '{plugin_dir}' not found")
        return discovered

    for _, module_name, is_pkg in pkgutil.iter_modules([str(package_path)]):
        if not is_pkg:
            continue

        result = _load_plugin_module(plugin_dir, module_name)
        if not result:
            continue

        plugin_module, full_name = result
        plugin = _extract_plugin_instance(plugin_module, full_name)

        if plugin:
            discovered.append(plugin)
            if auto_register:
                _register_plugin(plugin)

    return discovered
