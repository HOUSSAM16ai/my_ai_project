# app/overmind/planning/strategies/recursive_strategy.py
"""
Recursive Planning Strategy.
Wraps a specific BasePlanner implementation (e.g., 'recursive') to execute complex tasks.
"""
from __future__ import annotations
import logging

from ..schemas import MissionPlanSchema, PlanningContext
from ..base_planner import BasePlanner, get_planner_instance
from .base_strategy import BasePlanningStrategy

logger = logging.getLogger(__name__)

class RecursiveStrategy:
    """
    Recursive planner strategy for complex tasks requiring decomposition.
    Delegates to a concrete BasePlanner instance (e.g., 'recursive' or 'deep_thought').
    """
    name = "recursive_strategy"

    def __init__(self, planner_name: str = "recursive_planner"):
        self.planner_name = planner_name
        self._planner_instance: BasePlanner | None = None

    @property
    def planner(self) -> BasePlanner:
        if not self._planner_instance:
            try:
                self._planner_instance = get_planner_instance(self.planner_name)
            except Exception:
                logger.warning(f"Planner {self.planner_name} not found for RecursiveStrategy.")
                raise
        return self._planner_instance

    def generate(self, objective: str, context: PlanningContext | None = None) -> MissionPlanSchema:
        return self.planner.generate_plan(objective, context)

    async def a_generate(self, objective: str, context: PlanningContext | None = None) -> MissionPlanSchema:
        return await self.planner.a_generate_plan(objective, context)
