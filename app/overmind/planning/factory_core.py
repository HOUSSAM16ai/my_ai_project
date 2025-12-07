# app/overmind/planning/factory_core.py
"""
Core Factory Logic for Planner Management and Strategy Selection.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil

from .base_planner import BasePlanner, instantiate_all_planners
from .exceptions import PlannerNotFound
from .schemas import PlanningContext
from .strategies.base_strategy import BasePlanningStrategy
from .strategies.linear_strategy import LinearStrategy
from .strategies.recursive_strategy import RecursiveStrategy

logger = logging.getLogger(__name__)


class PlannerFactory:
    """
    Manages the lifecycle and discovery of planners.
    Acts as the Registry and Factory for "Atomic Intelligence Units".
    """

    @staticmethod
    def discover_planners(
        root_package: str = "app.overmind.planning.generators",
    ) -> dict[str, BasePlanner]:
        """
        Discovers and instantiates all available planners.
        Iterates over the given package to find and import planner modules,
        triggering their registration in BasePlanner.
        """
        try:
            package = importlib.import_module(root_package)
            if hasattr(package, "__path__"):
                for _, name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
                    try:
                        importlib.import_module(name)
                    except Exception as e:
                        logger.warning(f"Failed to import planner module {name}: {e}")
        except Exception as e:
            logger.warning(f"Failed to scan root package {root_package}: {e}")

        planners = instantiate_all_planners()
        if not planners:
            logger.warning("No active planners discovered.")

        return {p.name: p for p in planners}

    @staticmethod
    def get_planner(name: str) -> BasePlanner:
        """
        Direct retrieval of a specific planner.
        """
        try:
            return BasePlanner.get_planner_class(name)()
        except Exception as e:
            raise PlannerNotFound(name, context=str(e)) from e

    @staticmethod
    def select_strategy(
        objective: str, context: PlanningContext | None = None
    ) -> BasePlanningStrategy:
        """
        Selects the optimal strategy based on objective complexity and context.
        """
        # Simple heuristic: length of objective or context flags
        complexity_score = len(objective.split())

        # Determine preferred backend planner names (could be config driven)
        # For now we assume 'standard_planner' and 'recursive_planner' exist in the registry
        # If not, the Strategy classes will raise/log when accessing .planner property.

        if context and context.constraints.get("fast_mode"):
            return LinearStrategy(planner_name="standard_planner")

        if complexity_score > 50 or "complex" in objective.lower():
            return RecursiveStrategy(planner_name="recursive_planner")

        return LinearStrategy(planner_name="standard_planner")


def select_strategy(objective: str, context: PlanningContext | None = None) -> BasePlanningStrategy:
    """Convenience alias for PlannerFactory.select_strategy"""
    return PlannerFactory.select_strategy(objective, context)
