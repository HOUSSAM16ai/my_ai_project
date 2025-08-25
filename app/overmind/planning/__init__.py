# app/overmind/planning/__init__.py
# ======================================================================================
# ==                            THE PLANNERS' GUILD HALL                              ==
# ======================================================================================
#
# ⚔ PURPOSE (القصد):
#   This file establishes the `planning` sub-package and serves as its public
#   interface. It exposes the most critical components from this module: the planner
#   factory and the core schemas.
#
#   By abstracting the internal file structure (e.g., `base_planner`, `llm_planner`),
#   the rest of the application can interact with the "concept" of planning
#   without needing to know the specific implementation details.
#
# 🧬 EXPORTS (الصادرات):
#   - schemas: The Pydantic models that define the structure of a valid plan.
#   - factory: The module responsible for discovering and instantiating planners.
#   - BasePlanner: The abstract class for type hinting and creating new planners.
#   - get_planner: A direct shortcut to the factory's most used function.
#
# ===============================================================================

# --- Expose the core data contracts (schemas) directly ---
from . import schemas

# --- Expose the factory for planner discovery and instantiation ---
from . import factory

# --- Expose the core abstract class for type hinting and extension ---
from .base_planner import BasePlanner, PlanningContext, PlanGenerationResult, PlannerError

# --- Provide a convenient shortcut to the most common factory function ---
from .factory import get_planner, get_all_planners, discover

# --- Define what is publicly available when someone does `from app.overmind.planning import *` ---
__all__ = [
    # Core Modules
    "schemas",
    "factory",
    
    # Core Classes & Types
    "BasePlanner",
    "PlanningContext",
    "PlanGenerationResult",
    "PlannerError",
    
    # Core Functions
    "get_planner",
    "get_all_planners",
    "discover"
]