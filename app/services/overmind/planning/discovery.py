"""
This module contains the PlannerDiscovery class, which is responsible for
discovering planners from the filesystem and metadata registries.
"""
from __future__ import annotations

import importlib
import importlib.util
import logging
import pkgutil
from typing import TYPE_CHECKING, Any

from .config import FactoryConfig

if TYPE_CHECKING:
    from types import ModuleType

    from .factory_core import PlannerRecord
try:
    from .base_planner import BasePlanner
except (ImportError, ModuleNotFoundError):


    class BasePlanner:

        @staticmethod
        def live_planner_classes():
            return {}

        @staticmethod
        def planner_metadata():
            return {}


def _get_planner_record_class():
    """Lazy import of PlannerRecord to avoid circular import."""
    from .factory_core import PlannerRecord
    return PlannerRecord


class PlannerDiscovery:
    """
    Handles the discovery of planners.
    """

    def __init__(self, config: FactoryConfig, logger: logging.Logger):
        self._config = config
        self._logger = logger
        self._import_failures: dict[str, str] = {}

    def _log(self, message: str, level: str='INFO', **fields):
        """Helper for structured logging."""
        self._logger.log(getattr(logging, level, logging.INFO), message,
            extra={'component': 'PlannerDiscovery', **fields})

    def _import_module(self, module_name: str) ->(ModuleType | None):
        """Import a module and record any failures."""
        try:
            return importlib.import_module(module_name)
        except Exception as exc:
            self._import_failures[module_name] = str(exc)
            self._log(f"Failed to import module '{module_name}': {exc}",
                'ERROR', module=module_name)
            return None

    def _iter_submodules(self, package_name: str):
        """Iterate over all submodules of a package."""
        try:
            package = importlib.import_module(package_name)
            if hasattr(package, '__path__'):
                for m in pkgutil.walk_packages(package.__path__, package.
                    __name__ + '.'):
                    yield m.name
        except Exception as exc:
            self._import_failures[package_name] = f'root import failed: {exc}'
            self._log(f"Failed to import root package '{package_name}': {exc}",
                'ERROR')

    def _is_module_allowed(self, module_name: str) ->bool:
        """Check if a module is allowed by the factory configuration."""
        if module_name in self._config.exclude_modules:
            return False
        if module_name not in self._config.allowed_planners:
            self._log(f'Skipping module not in ALLOWED_PLANNERS: {module_name}'
                , 'DEBUG', module=module_name)
            return False
        return True

    def _get_planner_metadata(self) ->dict:
        """Safely get planner metadata from the BasePlanner registry."""
        if hasattr(BasePlanner, 'planner_metadata'):
            try:
                return BasePlanner.planner_metadata()
            except Exception as e:
                self._log(f'planner_metadata() failed: {e}', 'WARN')
        return {}

    def _get_live_planner_classes(self) ->dict:
        """Safely get live planner classes from the BasePlanner registry."""
        if hasattr(BasePlanner, 'live_planner_classes'):
            try:
                return BasePlanner.live_planner_classes()
            except Exception as e:
                self._log(f'live_planner_classes() failed: {e}', 'WARN')
        return {}

    def _extract_attribute_set(self, obj: Any, attr: str) ->set[str]:
        """Extract a set of strings from an object's attribute."""
        val = getattr(obj, attr, None)
        if isinstance(val, list | tuple | set):
            return {str(v).strip() for v in val if v is not None}
        return set()

    def _update_record_from_meta(self, rec: PlannerRecord, meta: dict):
        """Update a PlannerRecord with data from a metadata dictionary."""
        rec.reliability_score = meta.get('reliability_score', rec.
            reliability_score)
        rec.total_invocations = meta.get('total_invocations', rec.
            total_invocations)
        rec.total_failures = meta.get('total_failures', rec.total_failures)
        rec.avg_duration_ms = meta.get('avg_duration_ms', rec.avg_duration_ms)
        rec.tier = meta.get('tier', rec.tier)
        rec.quarantined = meta.get('quarantined', rec.quarantined)
        rec.self_test_passed = meta.get('self_test_passed', rec.
            self_test_passed)
        rec.production_ready = meta.get('production_ready', rec.
            production_ready)
        rec.version = meta.get('version', rec.version)
