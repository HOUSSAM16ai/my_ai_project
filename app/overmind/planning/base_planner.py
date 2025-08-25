# app/overmind/planning/base_planner.py
# ======================================================================================
# ==                   THE STRATEGIST'S CODEX (v2.1 • AURORA PROTOCOL)                ==
# ==                         OVERMIND PLANNING CORE INTERFACE                         ==
# ======================================================================================
#
# CHANGELOG v2.1 (Critical Fix):
#   - FIXED root cause of "planners=0" / not discovered:
#       Previously `name` was defined as an @property abstract method. Accessing
#       it at class definition inside __init_subclass__ returned a `property`
#       object, so the registry rejected it (not str) → NO planners registered.
#       NOW: `name` MUST be a CLASS ATTRIBUTE (string).
#   - Added robust registry logic (supports legacy subclasses that still define
#     a property 'name' by instantiating them safely once, with guard).
#   - Provided clear developer errors if name missing or invalid.
#   - Hardened timeout + error taxonomy.
#   - Added optional telemetry hooks & extensibility points.
#
# CONTRACT (Updated v2.1):
#   1. Subclass MUST define:
#        name: Class attribute (unique lowercase_snake). (NOT a @property)
#      Optional:
#        version: Class attribute or @property returning a short version string.
#   2. Must implement generate_plan(objective, context) -> MissionPlanSchema.
#   3. Optional: override a_generate_plan for native async.
#   4. Optional: override validate_plan for semantic checks (raise PlanValidationError).
#
# QUICK SUBCLASS TEMPLATE:
#   class MyPlanner(BasePlanner):
#       name = "my_planner_v1"
#       version = "1.0.0"
#       def generate_plan(self, objective: str, context: Optional[PlanningContext]=None) -> MissionPlanSchema:
#           ... build & return MissionPlanSchema(...)
#
# WHY CLASS ATTRIBUTE?
#   - Registry runs at class definition time (before instantiation). A property can't
#     be resolved without an instance → produced a `property` object → silent skip.
#
# SAFETY:
#   - All failures must raise PlannerError or subclasses.
#   - Timeout enforcement optionally available.
#
# ======================================================================================
from __future__ import annotations

import asyncio
import inspect
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any, ClassVar, Dict, List, Mapping, Optional, Type, Union
)

from .schemas import MissionPlanSchema  # Expected project-local schema

# --------------------------------------------------------------------------------------
# Logging (can be centralized elsewhere)
# --------------------------------------------------------------------------------------
logger = logging.getLogger("overmind.planning")
if not logger.handlers:
    _h = logging.StreamHandler()
    _f = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    _h.setFormatter(_f)
    logger.addHandler(_h)
logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------------------
# Context fed into planners
# --------------------------------------------------------------------------------------
@dataclass(slots=True)
class PlanningContext:
    mission_id: int
    initiator_id: int
    past_failures: Mapping[str, str] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

# --------------------------------------------------------------------------------------
# Structured result wrapper
# --------------------------------------------------------------------------------------
@dataclass(slots=True)
class PlanGenerationResult:
    plan: MissionPlanSchema
    duration_seconds: float
    planner_name: str
    objective: str
    planner_version: Optional[str] = None
    node_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# --------------------------------------------------------------------------------------
# Error taxonomy
# --------------------------------------------------------------------------------------
class PlannerError(Exception):
    def __init__(self, message: str, planner_name: str, objective: str):
        self.planner_name = planner_name
        self.objective = objective
        super().__init__(f"[{planner_name}] objective='{objective}' :: {message}")

class PlanValidationError(PlannerError):
    pass

class ExternalServiceError(PlannerError):
    pass

class PlannerTimeoutError(PlannerError):
    pass

# --------------------------------------------------------------------------------------
# Base Planner
# --------------------------------------------------------------------------------------
class BasePlanner(ABC):
    """
    Abstract base for all Overmind planners.

    SUBCLASS REQUIREMENTS:
      - name (Class attribute, unique, str, recommended lowercase).
      - generate_plan() -> MissionPlanSchema

    OPTIONAL:
      - version (class attr or property)
      - a_generate_plan()
      - validate_plan()
      - override default_timeout_seconds
    """

    # Registry
    _registry: ClassVar[Dict[str, Type['BasePlanner']]] = {}

    # Subclass may override (seconds); if set and enforce_timeout=True in instrumented call
    default_timeout_seconds: ClassVar[Optional[float]] = None

    # REQUIRED CLASS ATTRIBUTE IN SUBCLASSES
    name: ClassVar[str] = "abstract_base"  # Must be overridden

    # OPTIONAL
    version: ClassVar[Optional[str]] = None  # Subclass may set or override property

    # --- Registration Magic ---
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Skip if abstract
        if inspect.isabstract(cls):
            return

        # Try to resolve planner name
        planner_name = getattr(cls, "name", None)

        # Fallback: If someone still used a @property def name(self) style (legacy),
        # attempt safe single instantiation to extract it.
        if not isinstance(planner_name, str):
            legacy_prop = getattr(cls, "name", None)
            if isinstance(legacy_prop, property):
                try:
                    temp_instance = cls.__new__(cls)  # Avoid full __init__ side-effects
                    # If subclass __init__ is lightweight you can call; else skip.
                    try:
                        cls.__init__(temp_instance)
                    except Exception:
                        pass
                    val = legacy_prop.fget(temp_instance)  # type: ignore
                    if isinstance(val, str):
                        planner_name = val
                        setattr(cls, "name", val)  # Promote to class attr
                        logger.warning(
                            "Planner '%s' defined 'name' as @property. "
                            "Promoted to class attribute for registry compatibility.",
                            val
                        )
                except Exception:
                    planner_name = None

        if not isinstance(planner_name, str):
            logger.error(
                "Planner subclass %s missing valid 'name' class attribute (string). NOT registered.",
                cls.__name__
            )
            return

        key = planner_name.strip().lower()
        if not key:
            logger.error("Planner subclass %s has empty 'name'. NOT registered.", cls.__name__)
            return

        if key in BasePlanner._registry:
            logger.warning(
                "Planner name collision for '%s'. Overwriting previous registration with %s.",
                key, cls.__name__
            )
        BasePlanner._registry[key] = cls
        logger.debug("Registered planner '%s' => %s", key, cls.__name__)

    # ----------------------------------------------------------------------------------
    # REQUIRED implementation in subclass
    # ----------------------------------------------------------------------------------
    @abstractmethod
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> MissionPlanSchema:
        raise NotImplementedError

    # ----------------------------------------------------------------------------------
    # Optional async version; default delegates to sync
    # ----------------------------------------------------------------------------------
    async def a_generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> MissionPlanSchema:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.generate_plan(objective, context))

    # ----------------------------------------------------------------------------------
    # Validation hook (override for semantic constraints)
    # ----------------------------------------------------------------------------------
    def validate_plan(
        self,
        plan: MissionPlanSchema,
        objective: str,
        context: Optional[PlanningContext]
    ) -> None:
        return

    # ----------------------------------------------------------------------------------
    # Public instrumentation (sync)
    # ----------------------------------------------------------------------------------
    def instrumented_generate(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        *,
        include_node_count: bool = True,
        extra_metadata: Optional[Dict[str, Any]] = None,
        enforce_timeout: bool = True
    ) -> PlanGenerationResult:
        start = time.perf_counter()
        meta: Dict[str, Any] = dict(extra_metadata or {})
        timeout = self.default_timeout_seconds

        try:
            if enforce_timeout and timeout:
                plan = self._run_with_timeout(objective, context, timeout)
            else:
                plan = self.generate_plan(objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlannerError(str(exc), self.name, objective) from exc

        # Validation
        try:
            self.validate_plan(plan, objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlanValidationError(f"Unexpected validation failure: {exc}", self.name, objective) from exc

        node_count = self._infer_node_count(plan) if include_node_count else None
        duration = time.perf_counter() - start
        meta.update({
            "context_tags": getattr(context, "tags", None),
            "has_past_failures": bool(getattr(context, "past_failures", {})),
        })

        result = PlanGenerationResult(
            plan=plan,
            duration_seconds=duration,
            planner_name=self.name,
            planner_version=getattr(self, "version", None),
            objective=objective,
            node_count=node_count,
            metadata=meta
        )

        logger.info(
            "Planner '%s'%s produced plan in %.4fs (nodes=%s objective='%s')",
            self.name,
            f" v{self.version}" if getattr(self, 'version', None) else "",
            duration,
            node_count,
            objective
        )
        return result

    # ----------------------------------------------------------------------------------
    # Public instrumentation (async)
    # ----------------------------------------------------------------------------------
    async def a_instrumented_generate(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        *,
        include_node_count: bool = True,
        extra_metadata: Optional[Dict[str, Any]] = None,
        enforce_timeout: bool = True
    ) -> PlanGenerationResult:
        start = time.perf_counter()
        meta: Dict[str, Any] = dict(extra_metadata or {})
        timeout = self.default_timeout_seconds

        try:
            if enforce_timeout and timeout:
                plan = await self._a_run_with_timeout(objective, context, timeout)
            else:
                plan = await self.a_generate_plan(objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlannerError(str(exc), self.name, objective) from exc

        try:
            self.validate_plan(plan, objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlanValidationError(f"Unexpected validation failure: {exc}", self.name, objective) from exc

        node_count = self._infer_node_count(plan) if include_node_count else None
        duration = time.perf_counter() - start
        meta.update({
            "context_tags": getattr(context, "tags", None),
            "has_past_failures": bool(getattr(context, "past_failures", {})),
        })

        result = PlanGenerationResult(
            plan=plan,
            duration_seconds=duration,
            planner_name=self.name,
            planner_version=getattr(self, "version", None),
            objective=objective,
            node_count=node_count,
            metadata=meta
        )
        logger.info(
            "Async planner '%s'%s produced plan in %.4fs (nodes=%s objective='%s')",
            self.name,
            f" v{self.version}" if getattr(self, 'version', None) else "",
            duration,
            node_count,
            objective
        )
        return result

    # ----------------------------------------------------------------------------------
    # Registry API
    # ----------------------------------------------------------------------------------
    @classmethod
    def available_planners(cls) -> List[str]:
        return sorted(cls._registry.keys())

    @classmethod
    def get_planner_class(cls, name: str) -> Type['BasePlanner']:
        key = name.strip().lower()
        if key not in cls._registry:
            raise KeyError(f"Planner '{name}' not registered.")
        return cls._registry[key]

    # ----------------------------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------------------------
    def _run_with_timeout(
        self,
        objective: str,
        context: Optional[PlanningContext],
        timeout: float
    ) -> MissionPlanSchema:
        """
        Blocking timeout wrapper. Spawns a thread for the sync generate_plan.
        Suitable ONLY if generate_plan is CPU-light or IO-light.
        """
        container: Dict[str, Union[BaseException, MissionPlanSchema]] = {}

        def runner():
            try:
                container["result"] = self.generate_plan(objective, context)
            except BaseException as e:
                container["error"] = e

        th = threading.Thread(target=runner, daemon=True)
        th.start()
        th.join(timeout)
        if th.is_alive():
            raise PlannerTimeoutError(f"Timeout {timeout:.2f}s exceeded", self.name, objective)
        if "error" in container:
            err = container["error"]
            if isinstance(err, PlannerError):
                raise err
            raise PlannerError(str(err), self.name, objective)
        return container["result"]  # type: ignore

    async def _a_run_with_timeout(
        self,
        objective: str,
        context: Optional[PlanningContext],
        timeout: float
    ) -> MissionPlanSchema:
        try:
            return await asyncio.wait_for(
                self.a_generate_plan(objective, context),
                timeout=timeout
            )
        except asyncio.TimeoutError as exc:
            raise PlannerTimeoutError(f"Async timeout {timeout:.2f}s exceeded", self.name, objective) from exc

    def _infer_node_count(self, plan: MissionPlanSchema) -> Optional[int]:
        for attr in ("tasks", "nodes", "steps"):
            if hasattr(plan, attr):
                seq = getattr(plan, attr)
                try:
                    return len(seq)  # type: ignore
                except Exception:
                    return None
        return None

# --------------------------------------------------------------------------------------
# OPTIONAL: Demonstrative Stub (safe to remove in production)
# --------------------------------------------------------------------------------------
class ExampleHeuristicPlanner(BasePlanner):
    """
    Demonstration stub. NOT for production.
    Always raises to remind you to implement real planner logic or delete this class.
    """
    name = "example_heuristic"
    version = "0.1.0"

    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> MissionPlanSchema:
        raise PlannerError(
            "ExampleHeuristicPlanner is a stub. Replace or remove.",
            self.name,
            objective
        )

    def validate_plan(
        self,
        plan: MissionPlanSchema,
        objective: str,
        context: Optional[PlanningContext]
    ) -> None:
        return

# ======================================================================================
# END OF FILE
# ======================================================================================