# app/overmind/planning/strategies/linear_strategy.py
"""
Linear Planning Strategy.
Wraps a specific BasePlanner implementation (e.g., 'standard') to execute linear tasks.
"""
from __future__ import annotations
import logging
from typing import Any

from ..schemas import MissionPlanSchema, PlanningContext
from ..base_planner import BasePlanner, get_planner_instance
from .base_strategy import BasePlanningStrategy

logger = logging.getLogger(__name__)

class LinearStrategy:
    """
    Standard linear execution planner strategy.
    Delegates to a concrete BasePlanner instance (e.g., a 'standard' planner).
    """
    name = "linear_strategy"

    def __init__(self, planner_name: str = "standard_planner"):
        self.planner_name = planner_name
        self._planner_instance: BasePlanner | None = None

    @property
    def planner(self) -> BasePlanner:
        if not self._planner_instance:
            # Lazy loading to avoid circular imports or early registry access issues
            try:
                self._planner_instance = get_planner_instance(self.planner_name)
            except Exception:
                # Fallback or error handling if planner not found
                # For now we might want to let it raise or log
                logger.warning(f"Planner {self.planner_name} not found for LinearStrategy.")
                raise
        return self._planner_instance

    def generate(self, objective: str, context: PlanningContext | None = None) -> MissionPlanSchema:
        return self.planner.generate_plan(objective, context)

    async def a_generate(self, objective: str, context: PlanningContext | None = None) -> MissionPlanSchema:
        return await self.planner.a_generate_plan(objective, context)
