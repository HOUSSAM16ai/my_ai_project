# app/overmind/planning/strategies/base_strategy.py
"""
Base Strategy Interface.
Defines the contract for all planning strategies.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..schemas import MissionPlanSchema, PlanningContext


@runtime_checkable
class BasePlanningStrategy(Protocol):
    """
    Protocol definition for a planning strategy.
    Strategies utilize underlying Planners to execute generation.
    """

    name: str = "abstract_strategy"

    def generate(self, objective: str, context: PlanningContext | None = None) -> MissionPlanSchema:
        """Synchronous generation."""
        ...

    async def a_generate(
        self, objective: str, context: PlanningContext | None = None
    ) -> MissionPlanSchema:
        """Asynchronous generation."""
        ...
