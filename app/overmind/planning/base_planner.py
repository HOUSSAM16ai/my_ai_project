# app/overmind/planning/base_planner.py
# # -*- coding: utf-8 -*-
# # -*- coding: utf-8 -*-
# ======================================================================================
# app/overmind/planning/base_planner.py
# ======================================================================================
# THE STRATEGIST'S CODEX  v3.1  "STRATEGIST CODEX / GOVERNANCE / RELIABILITY dna"
#
# PURPOSE (UPDATED):
#   Hardened abstract planner foundation with:
#     - Governance (allow / block lists, environment awareness)
#     - Quarantine & self-test admission control
#     - Exponential–decay reliability model (time weighted + Laplace smoothing)
#     - Telemetry + selection scoring heuristics
#     - Capabilities + tiers + risk rating metadata
#     - Instrumented synchronous & asynchronous generation wrappers
#     - Timeout enforcement (threaded + asyncio.wait_for)
#     - Robust plan validation placeholder + DAG node counting heuristic
#     - Safe registration (idempotent, thread-safe) & metadata export helpers
#     - EXTENDED ERROR MODEL: PlannerError now safely accepts **extra without انفجار
#     - Extra diagnostic helpers & snapshot methods
#
# CHANGE LOG (v3.1):
#   * PlannerError now accepts **extra (stores sanitized copy in .extra / .extra_flat).
#   * Added PlannerError.to_dict() for structured logging downstream.
#   * Added defensive logging around registration & self-test.
#   * Slightly clearer reliability snapshot metadata & docstrings.
#   * Non-breaking: existing raises without extra still تعمل كما هي.
#
# ENV VARS (unchanged):
#     OVERMIND_ENV=prod|dev
#     PLANNERS_ALLOW="llm_grounded_planner,..."
#     PLANNERS_BLOCK="legacy_planner,stub,..."
#     PLANNER_DECAY_HALF_LIFE=900
#     PLANNER_MIN_RELIABILITY=0.05
#     PLANNER_SELF_TEST_TIMEOUT=5
#     PLANNER_DEFAULT_TIMEOUT=40
#     PLANNER_DISABLE_QUARANTINE=0|1
#
# COMPATIBILITY:
#   - Existing imports of: BasePlanner, PlannerError, PlanValidationError remain valid.
#   - Subclasses need no modification unless they relied on previous exception message
#     EXACT formatting (only appended extras when present).
#
# ======================================================================================

from __future__ import annotations

import asyncio
import inspect
import logging
import os
import queue
import re
import threading
import time
from dataclasses import dataclass, field
from typing import (
    Any, ClassVar, Dict, List, Optional, Type, Union, Set, Iterable, Tuple
)

# --------------------------------------------------------------------------------------
# Soft schema imports (fallbacks)
# --------------------------------------------------------------------------------------
try:  # pragma: no cover
    from .schemas import MissionPlanSchema, PlanningContext  # type: ignore
except Exception:  # pragma: no cover
    @dataclass
    class MissionPlanSchema:  # type: ignore
        objective: str
        tasks: List[Any]

    @dataclass
    class PlanningContext:  # type: ignore
        past_failures: Optional[List[str]] = None
        user_preferences: Optional[Dict[str, Any]] = None
        tags: Optional[List[str]] = None

# --------------------------------------------------------------------------------------
# Logging Setup
# --------------------------------------------------------------------------------------
logger = logging.getLogger("overmind.planning.base_planner")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

# ======================================================================================
# Exception Hierarchy (HARDENED)
# ======================================================================================

def _flatten_extras(extra: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flattens any nested simple dict one level for compact logging.
    Only shallow flattening - complex nested structures are kept as-is.
    """
    flat: Dict[str, Any] = {}
    for k, v in extra.items():
        if isinstance(v, dict):
            # Keep nested dict intact; avoid deep recursion for predictability
            flat[k] = v
        else:
            flat[k] = v
    return flat


class PlannerError(Exception):
    """
    خط الدفاع ضد انفجار الاستثناءات بسبب وسيط extra.
    يمكن الآن تمرير أي مفاتيح إضافية بدون كسر السلسلة.

    message       : النص الأساسي
    planner_name  : اسم المخطط (تلقائياً unknown_planner إذا غير معروف)
    objective     : الهدف الحالي (للسياق)
    **extra       : أي ميتاداتا (errors, error_code, raw, attempt, إلخ)
    """
    def __init__(
        self,
        message: str,
        planner_name: str = "unknown_planner",
        objective: str = "",
        **extra: Any
    ):
        base_msg = f"[{planner_name}] objective='{objective}' :: {message}"
        # فقط أضف ملخصاً صغيراً للـ extras إلى النص إن وُجد (لا تتجاوز 180 حرفاً)
        if extra:
            try:
                flat = _flatten_extras(extra)
                preview_items: List[str] = []
                for k, v in flat.items():
                    vs = repr(v)
                    if len(vs) > 40:
                        vs = vs[:37] + "..."
                    preview_items.append(f"{k}={vs}")
                preview_str = ", ".join(preview_items)
                if len(preview_str) > 180:
                    preview_str = preview_str[:177] + "..."
                base_msg += f" | extra: {preview_str}"
            except Exception as e:  # لا تفشل بسبب تنسيق
                base_msg += f" | extra_format_error={e!r}"
        super().__init__(base_msg)
        self.planner_name = planner_name
        self.objective = objective
        self.raw_message = message
        self.extra: Optional[Dict[str, Any]] = extra or None
        self.extra_flat: Optional[Dict[str, Any]] = _flatten_extras(extra) if extra else None
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "planner": self.planner_name,
            "objective": self.objective,
            "message": self.raw_message,
            "full_message": str(self),
            "extra": self.extra,
            "timestamp": self.timestamp,
        }


class PlanValidationError(PlannerError):
    """ Raised when validation of produced plan structure/content fails. """
    pass


class ExternalServiceError(PlannerError):
    """ Wraps errors originating in external APIs / remote services. """
    pass


class PlannerTimeoutError(PlannerError):
    """ Raised when planner execution exceeds enforced timeout. """
    pass


class PlannerAdmissionError(PlannerError):
    """ Raised when planner is blocked, quarantined, or not registered. """
    pass


# --------------------------------------------------------------------------------------
# Environment & Governance
# --------------------------------------------------------------------------------------
_ENV = os.getenv("OVERMIND_ENV", "dev").strip().lower()
_ALLOW_LIST = {
    x.strip().lower() for x in os.getenv("PLANNERS_ALLOW", "").split(",") if x.strip()
}
_BLOCK_LIST = {
    x.strip().lower() for x in os.getenv("PLANNERS_BLOCK", "").split(",") if x.strip()
}
_DECAY_HALF_LIFE = float(os.getenv("PLANNER_DECAY_HALF_LIFE", "900"))
_MIN_RELIABILITY = float(os.getenv("PLANNER_MIN_RELIABILITY", "0.05"))
_SELF_TEST_TIMEOUT = float(os.getenv("PLANNER_SELF_TEST_TIMEOUT", "5"))
_FALLBACK_DEFAULT_TIMEOUT = float(os.getenv("PLANNER_DEFAULT_TIMEOUT", "40"))
_DISABLE_QUARANTINE = os.getenv("PLANNER_DISABLE_QUARANTINE", "0") == "1"

_NAME_PATTERN = re.compile(r"^[a-z0-9_][a-z0-9_\-]{2,63}$")

# --------------------------------------------------------------------------------------
# Reliability State Model (with exponential decay)
# --------------------------------------------------------------------------------------
@dataclass
class _ReliabilityState:
    success_weight: float = 0.0
    failure_weight: float = 0.0
    last_update_ts: float = field(default_factory=time.time)
    total_invocations: int = 0
    total_failures: int = 0
    total_duration_ms: float = 0.0
    last_success_ts: Optional[float] = None
    registration_time: float = field(default_factory=time.time)
    last_error: Optional[str] = None

    # Governance extended attributes
    quarantined: bool = False
    self_test_passed: Optional[bool] = None
    production_ready: bool = False
    tier: str = "experimental"          # core | experimental | shadow
    risk_rating: str = "medium"         # low | medium | high

    def decay(self, now: Optional[float] = None):
        now = now or time.time()
        dt = now - self.last_update_ts
        if dt <= 0:
            return
        if _DECAY_HALF_LIFE <= 0:
            self.last_update_ts = now
            return
        factor = 0.5 ** (dt / _DECAY_HALF_LIFE)
        self.success_weight *= factor
        self.failure_weight *= factor
        self.last_update_ts = now

    def update(self, success: bool, duration_seconds: float):
        self.decay()
        weight = 1.0
        if success:
            self.success_weight += weight
            self.last_success_ts = time.time()
        else:
            self.failure_weight += weight
            self.total_failures += 1
        self.total_invocations += 1
        self.total_duration_ms += duration_seconds * 1000.0

    def reliability_score(self) -> float:
        numerator = self.success_weight + 1.0
        denom = self.success_weight + self.failure_weight + 2.0
        score = numerator / denom if denom > 0 else 0.5
        return max(0.0, min(1.0, score))

    @property
    def avg_duration_ms(self) -> float:
        if self.total_invocations == 0:
            return 0.0
        return self.total_duration_ms / self.total_invocations


# --------------------------------------------------------------------------------------
# Base Planner
# --------------------------------------------------------------------------------------
class BasePlanner:
    """
    Abstract Planner Base.
    Subclasses must implement generate_plan().
    """

    # Registry
    _registry: ClassVar[Dict[str, Type["BasePlanner"]]] = {}
    _reliability: ClassVar[Dict[str, _ReliabilityState]] = {}
    _lock: ClassVar[threading.RLock] = threading.RLock()

    # Required/optional class attributes
    name: ClassVar[str] = "abstract_base"
    version: ClassVar[Optional[str]] = None
    capabilities: ClassVar[Set[str]] = set()
    production_ready: ClassVar[bool] = False
    tier: ClassVar[str] = "experimental"
    risk_rating: ClassVar[str] = "medium"
    default_timeout_seconds: ClassVar[Optional[float]] = None
    allow_registration: ClassVar[bool] = True  # set to False on test stubs

    # ----- Admission & Registration Hooks -----
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:
            BasePlanner._attempt_register(cls)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed registering planner subclass %s: %s", cls.__name__, exc)

    @classmethod
    def _attempt_register(cls, planner_cls: Type["BasePlanner"]):
        if planner_cls is BasePlanner:
            return

        if not getattr(planner_cls, "allow_registration", True):
            logger.debug("Planner %s registration skipped (allow_registration=False).", planner_cls.__name__)
            return

        planner_name = getattr(planner_cls, "name", None)
        if not isinstance(planner_name, str):
            logger.error("Planner class %s missing 'name' attribute (str).", planner_cls.__name__)
            return

        key = planner_name.strip().lower()
        if not _NAME_PATTERN.match(key):
            logger.error("Planner name '%s' invalid (pattern mismatch). Skipped.", key)
            return

        if key in _BLOCK_LIST:
            logger.warning("Planner '%s' blocked via PLANNERS_BLOCK.", key)
            return

        if _ALLOW_LIST and key not in _ALLOW_LIST:
            logger.info("Planner '%s' skipped (not in PLANNERS_ALLOW).", key)
            return

        with cls._lock:
            if key in cls._registry:
                logger.debug("Planner '%s' already registered. Skipping duplicate.", key)
                return

            state = _ReliabilityState(
                quarantined=not _DISABLE_QUARANTINE,
                production_ready=getattr(planner_cls, "production_ready", False),
                tier=getattr(planner_cls, "tier", "experimental"),
                risk_rating=getattr(planner_cls, "risk_rating", "medium")
            )
            cls._registry[key] = planner_cls
            cls._reliability[key] = state

        logger.info("Registered planner '%s' (tier=%s prod_ready=%s quarantine=%s)",
                    key, state.tier, state.production_ready, state.quarantined)

        cls._run_self_test(planner_cls, key, state)

    @classmethod
    def _run_self_test(cls, planner_cls: Type["BasePlanner"], key: str, state: _ReliabilityState):
        test_method = getattr(planner_cls, "self_test", None)
        if not callable(test_method):
            if planner_cls.production_ready or _DISABLE_QUARANTINE:
                state.quarantined = False
                state.self_test_passed = True
            else:
                state.self_test_passed = None
            return

        logger.debug("Running self-test for planner '%s'...", key)
        result: Dict[str, Any] = {}

        def runner():
            try:
                sig = inspect.signature(test_method)
                if isinstance(test_method, (classmethod, staticmethod)):
                    test_method()  # type: ignore
                else:
                    if len(sig.parameters) == 0:
                        test_method()  # type: ignore
                    else:
                        instance = planner_cls()
                        test_method(instance)  # type: ignore
                result["ok"] = True
            except Exception as e:
                result["error"] = e

        th = threading.Thread(target=runner, daemon=True)
        th.start()
        th.join(_SELF_TEST_TIMEOUT)
        if th.is_alive():
            logger.error("Planner '%s' self-test timeout (>%ss).", key, _SELF_TEST_TIMEOUT)
            state.self_test_passed = False
            if not _DISABLE_QUARANTINE:
                state.quarantined = True
            return

        if "error" in result:
            logger.error("Planner '%s' self-test FAILED: %s", key, result["error"])
            state.self_test_passed = False
            if not _DISABLE_QUARANTINE:
                state.quarantined = True
            else:
                logger.warning("Quarantine disabled; allowing planner '%s' despite failed self-test.", key)
        else:
            state.self_test_passed = True
            if planner_cls.production_ready or _ENV != "prod" or _DISABLE_QUARANTINE:
                state.quarantined = False
            logger.info("Planner '%s' self-test PASSED (quarantine=%s).", key, state.quarantined)

    # ----------------------------------------------------------------------------------
    # Abstract contract
    # ----------------------------------------------------------------------------------
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> MissionPlanSchema:
        raise NotImplementedError("Subclasses must implement generate_plan()")

    async def a_generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> MissionPlanSchema:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.generate_plan, objective, context)

    # ----------------------------------------------------------------------------------
    # Validation hook
    # ----------------------------------------------------------------------------------
    def validate_plan(
        self,
        plan: MissionPlanSchema,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> None:
        if not hasattr(plan, "objective"):
            raise PlanValidationError("Plan missing 'objective' attribute.", self.name, objective)
        if not hasattr(plan, "tasks"):
            raise PlanValidationError("Plan missing 'tasks' attribute.", self.name, objective)

    # ----------------------------------------------------------------------------------
    # Reliability Utilities
    # ----------------------------------------------------------------------------------
    @classmethod
    def _update_reliability(cls, name: str, success: bool, duration_seconds: float, error: Optional[str] = None):
        lower = name.lower()
        with cls._lock:
            state = cls._reliability.get(lower)
            if not state:
                return
            state.update(success, duration_seconds)
            if not success and error:
                state.last_error = (error[:240] if error else None)
            if success and state.quarantined and state.self_test_passed is not False:
                state.quarantined = False

    def current_reliability_score(self) -> float:
        with BasePlanner._lock:
            state = BasePlanner._reliability.get(self.name.lower())
            if not state:
                return 0.5
            state.decay()
            return state.reliability_score()

    @classmethod
    def planner_metadata(cls) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        with cls._lock:
            for name, st in cls._reliability.items():
                st.decay()
                meta = {
                    "name": name,
                    "reliability_score": round(st.reliability_score(), 4),
                    "total_invocations": st.total_invocations,
                    "total_failures": st.total_failures,
                    "avg_duration_ms": round(st.avg_duration_ms, 2),
                    "last_success_ts": st.last_success_ts,
                    "registration_time": st.registration_time,
                    "quarantined": st.quarantined,
                    "self_test_passed": st.self_test_passed,
                    "production_ready": st.production_ready,
                    "tier": st.tier,
                    "risk_rating": st.risk_rating,
                    "last_error": st.last_error
                }
                planner_cls = cls._registry.get(name)
                if planner_cls:
                    meta.update({
                        "version": getattr(planner_cls, "version", None),
                        "capabilities": sorted(getattr(planner_cls, "capabilities", [])),
                    })
                data[name] = meta
        return data

    # ----------------------------------------------------------------------------------
    # Planner retrieval / filtering
    # ----------------------------------------------------------------------------------
    @classmethod
    def get_planner_class(cls, name: str) -> Type["BasePlanner"]:
        key = name.lower()
        with cls._lock:
            if key not in cls._registry:
                raise PlannerAdmissionError(f"Planner '{name}' not registered.", name)
            state = cls._reliability.get(key)
            if state and state.quarantined:
                raise PlannerAdmissionError(f"Planner '{name}' is quarantined.", name)
            return cls._registry[key]

    @classmethod
    def instantiate(cls, name: str) -> "BasePlanner":
        return cls.get_planner_class(name)()

    @classmethod
    def live_planner_classes(cls) -> Dict[str, Type["BasePlanner"]]:
        accepted: Dict[str, Type["BasePlanner"]] = {}
        with cls._lock:
            scored: List[Tuple[str, Type["BasePlanner"], float]] = []
            for key, planner_cls in cls._registry.items():
                st = cls._reliability.get(key)
                if not st:
                    continue
                st.decay()
                if st.quarantined:
                    continue
                scored.append((key, planner_cls, st.reliability_score()))
            if not scored:
                return {}
            multiple = len(scored) > 1
            for key, planner_cls, score in scored:
                if multiple and score < _MIN_RELIABILITY:
                    continue
                accepted[key] = planner_cls
        return accepted

    @classmethod
    def instantiate_all(cls) -> List["BasePlanner"]:
        return [p() for p in cls.live_planner_classes().values()]

    @classmethod
    def manual_unquarantine(cls, name: str) -> bool:
        key = name.lower()
        with cls._lock:
            st = cls._reliability.get(key)
            if not st:
                return False
            st.quarantined = False
            return True

    # ----------------------------------------------------------------------------------
    # Timeout Execution (Sync)
    # ----------------------------------------------------------------------------------
    def _run_with_timeout(
        self,
        objective: str,
        context: Optional[PlanningContext],
        timeout: float
    ) -> MissionPlanSchema:
        container: Dict[str, Union[BaseException, MissionPlanSchema]] = {}
        q: "queue.Queue[int]" = queue.Queue()

        def runner():
            try:
                container["result"] = self.generate_plan(objective, context)
            except BaseException as e:
                container["error"] = e
            finally:
                q.put(1)

        th = threading.Thread(target=runner, daemon=True)
        th.start()
        try:
            q.get(timeout=timeout)
        except queue.Empty as exc:
            raise PlannerTimeoutError(f"Timeout {timeout:.2f}s exceeded.", self.name, objective) from exc

        if "error" in container:
            err = container["error"]
            if isinstance(err, PlannerError):
                raise err
            raise PlannerError(str(err), self.name, objective) from err
        result = container.get("result")
        if not isinstance(result, MissionPlanSchema):
            raise PlannerError("Planner returned invalid result type.", self.name, objective)
        return result

    # ----------------------------------------------------------------------------------
    # Timeout Execution (Async)
    # ----------------------------------------------------------------------------------
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

    # ----------------------------------------------------------------------------------
    # Instrumented sync
    # ----------------------------------------------------------------------------------
    def instrumented_generate(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        *,
        include_node_count: bool = True,
        extra_metadata: Optional[Dict[str, Any]] = None,
        enforce_timeout: bool = True
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        success_flag = False
        error_obj: Optional[Exception] = None
        timeout = self.default_timeout_seconds or _FALLBACK_DEFAULT_TIMEOUT

        with BasePlanner._lock:
            st = BasePlanner._reliability.get(self.name.lower())
            if st and st.quarantined:
                raise PlannerAdmissionError("Planner is quarantined (self-test failed or pending).", self.name, objective)

        try:
            if enforce_timeout and timeout:
                plan = self._run_with_timeout(objective, context, timeout)
            else:
                plan = self.generate_plan(objective, context)
            success_flag = True
        except PlannerError as pe:
            error_obj = pe
            raise
        except Exception as exc:
            error_obj = exc
            raise PlannerError(str(exc), self.name, objective) from exc
        finally:
            duration = time.perf_counter() - start
            BasePlanner._update_reliability(
                self.name,
                success_flag,
                duration,
                error=str(error_obj) if error_obj else None
            )

        try:
            self.validate_plan(plan, objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlanValidationError(f"Unexpected validation failure: {exc}", self.name, objective) from exc

        node_count = self._infer_node_count(plan) if include_node_count else None
        duration = time.perf_counter() - start
        rel_score = self.current_reliability_score()

        meta: Dict[str, Any] = {
            "planner": self.name,
            "version": getattr(self, "version", None),
            "duration_ms": round(duration * 1000.0, 2),
            "node_count": node_count,
            "objective_length": len(objective or ""),
            "reliability_score": round(rel_score, 4),
            "capabilities": sorted(getattr(self, "capabilities", [])),
            "tier": getattr(self, "tier", "experimental"),
            "production_ready": getattr(self, "production_ready", False),
            "risk_rating": getattr(self, "risk_rating", "medium"),
            "environment": _ENV,
            "timestamp": time.time()
        }
        if extra_metadata:
            meta.update(extra_metadata)
        meta["selection_score"] = round(self.compute_selection_score(objective, None), 4)
        return {"plan": plan, "meta": meta}

    # ----------------------------------------------------------------------------------
    # Instrumented async
    # ----------------------------------------------------------------------------------
    async def a_instrumented_generate(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        *,
        include_node_count: bool = True,
        extra_metadata: Optional[Dict[str, Any]] = None,
        enforce_timeout: bool = True
    ) -> Dict[str, Any]:
        start = time.perf_counter()
        success_flag = False
        error_obj: Optional[Exception] = None
        timeout = self.default_timeout_seconds or _FALLBACK_DEFAULT_TIMEOUT

        with BasePlanner._lock:
            st = BasePlanner._reliability.get(self.name.lower())
            if st and st.quarantined:
                raise PlannerAdmissionError("Planner is quarantined (self-test failed or pending).", self.name, objective)

        try:
            if enforce_timeout and timeout:
                plan = await self._a_run_with_timeout(objective, context, timeout)
            else:
                plan = await self.a_generate_plan(objective, context)
            success_flag = True
        except PlannerError as pe:
            error_obj = pe
            raise
        except Exception as exc:
            error_obj = exc
            raise PlannerError(str(exc), self.name, objective) from exc
        finally:
            duration = time.perf_counter() - start
            BasePlanner._update_reliability(
                self.name,
                success_flag,
                duration,
                error=str(error_obj) if error_obj else None
            )

        try:
            self.validate_plan(plan, objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlanValidationError(f"Unexpected validation failure: {exc}", self.name, objective) from exc

        node_count = self._infer_node_count(plan) if include_node_count else None
        duration = time.perf_counter() - start
        rel_score = self.current_reliability_score()

        meta: Dict[str, Any] = {
            "planner": self.name,
            "version": getattr(self, "version", None),
            "duration_ms": round(duration * 1000.0, 2),
            "node_count": node_count,
            "objective_length": len(objective or ""),
            "reliability_score": round(rel_score, 4),
            "capabilities": sorted(getattr(self, "capabilities", [])),
            "tier": getattr(self, "tier", "experimental"),
            "production_ready": getattr(self, "production_ready", False),
            "risk_rating": getattr(self, "risk_rating", "medium"),
            "environment": _ENV,
            "timestamp": time.time()
        }
        if extra_metadata:
            meta.update(extra_metadata)
        meta["selection_score"] = round(self.compute_selection_score(objective, None), 4)
        return {"plan": plan, "meta": meta}

    # ----------------------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------------------
    def _infer_node_count(self, plan: MissionPlanSchema) -> Optional[int]:
        for attr in ("tasks", "nodes", "steps"):
            if hasattr(plan, attr):
                seq = getattr(plan, attr)
                if isinstance(seq, Iterable):
                    try:
                        return len(list(seq))
                    except Exception:
                        return None
        return None

    def compute_selection_score(
        self,
        objective: str,
        desired_capabilities: Optional[Set[str]] = None
    ) -> float:
        rel_score = self.current_reliability_score()
        caps = getattr(self, "capabilities", set())
        if desired_capabilities:
            match = len(caps & desired_capabilities) / max(1, len(desired_capabilities))
        else:
            match = 1.0 if caps else 0.5

        objective_length = len(objective or "")
        length_factor = min(objective_length / 500.0, 1.0)
        length_component = 0.10 * length_factor

        tier = getattr(self, "tier", "experimental")
        tier_adjust = {"core": 0.05, "experimental": 0.0, "shadow": -0.03}.get(tier, 0.0)
        prod_adjust = 0.03 if getattr(self, "production_ready", False) else 0.0

        base = rel_score * 0.55 + match * 0.30 + length_component
        score = base + tier_adjust + prod_adjust
        return max(0.0, min(1.0, score))

    def reliability_snapshot(self) -> Dict[str, Any]:
        with BasePlanner._lock:
            st = BasePlanner._reliability.get(self.name.lower())
            if not st:
                return {}
            st.decay()
            return {
                "planner": self.name,
                "reliability_score": round(st.reliability_score(), 4),
                "quarantined": st.quarantined,
                "total_invocations": st.total_invocations,
                "total_failures": st.total_failures,
                "avg_duration_ms": round(st.avg_duration_ms, 2),
                "last_success_ts": st.last_success_ts,
                "last_error": st.last_error
            }


# --------------------------------------------------------------------------------------
# Public metadata functions
# --------------------------------------------------------------------------------------
def list_planner_metadata() -> Dict[str, Any]:
    return BasePlanner.planner_metadata()


def instantiate_all_planners() -> List[BasePlanner]:
    return BasePlanner.instantiate_all()


def get_planner_instance(name: str) -> BasePlanner:
    return BasePlanner.instantiate(name)


__all__ = [
    "BasePlanner",
    "PlannerError",
    "PlanValidationError",
    "PlannerTimeoutError",
    "ExternalServiceError",
    "PlannerAdmissionError",
    "list_planner_metadata",
    "instantiate_all_planners",
    "get_planner_instance",
]

# ======================================================================================
# END OF FILE
# ======================================================================================