# app/overmind/planning/base_planner.py
# ======================================================================================
# OVERMIND / MAESTRO – STRATEGIST CORE (Base Planner Foundation)
# Version: 4.5.0  •  Codename: "HYPER-STRATEGIST / STRUCT-AWARE / DRIFT-SENSE / RELIABILITY-DECAY+"
# ======================================================================================
# PURPOSE
#   Canonical abstract planner base class supplying:
#     - Deterministic registration + governance (allow / block / quarantine / env gating).
#     - Self-test admission (with quarantine control & timeout).
#     - Exponential half-life reliability model with Laplace smoothing.
#     - Instrumented sync & async execution with hard timeouts.
#     - Unified error taxonomy (PlannerError + derived).
#     - Selection scoring with structural telemetry augmentation (optional).
#     - Deep context passthrough (LLM structural / index signals).
#     - Structural scoring (grade + entropy + density + diversity) + drift detection.
#     - Apparent reliability nudge (non-persistent) for superior structural grades.
#
# UPGRADE HIGHLIGHTS (vs legacy 3.x):
#   + deep_context injection (instrumented_generate / a_instrumented_generate).
#   + Structural plan awareness: struct_base_score / struct_bonus / struct_drift.
#   + Dual-phase selection score: selection_score_base vs selection_score (post-struct).
#   + Grade bonuses (A/B/C) tunable via environment.
#   + Drift detection (task ratio change + grade drop delta).
#   + Apparent reliability nudge for grade A outputs (reporting only).
#   + Hardened self-test handling + explicit quarantine bypass env toggle.
#
# ENV VARS
#   OVERMIND_ENV=prod|dev                               Execution environment label.
#   PLANNERS_ALLOW="planner_a,planner_b"                Allow list (case-insensitive).
#   PLANNERS_BLOCK="legacy_planner,stub"                Block list (case-insensitive).
#   PLANNER_DECAY_HALF_LIFE=900                         Seconds half-life for reliability weights.
#   PLANNER_MIN_RELIABILITY=0.05                        Floor for multi-planner usage.
#   PLANNER_SELF_TEST_TIMEOUT=5                         Seconds for self-test.
#   PLANNER_DEFAULT_TIMEOUT=40                          Fallback global planner timeout (s).
#   PLANNER_DISABLE_QUARANTINE=0|1                      Disable quarantine gating.
#
#   # Structural scoring / drift (all optional):
#   PLANNER_STRUCT_SCORE_ENABLE=1                       Toggle structural scoring integration.
#   PLANNER_STRUCT_SCORE_WEIGHT=0.07                    Weight factor for struct_base_score.
#   PLANNER_STRUCT_GRADE_BONUS_A=0.05                   Grade A additive bonus.
#   PLANNER_STRUCT_GRADE_BONUS_B=0.02                   Grade B additive bonus.
#   PLANNER_STRUCT_GRADE_BONUS_C=0.0                    Grade C additive bonus.
#   PLANNER_STRUCT_DRIFT_TASK_RATIO=0.30                Relative task count change to flag drift.
#   PLANNER_STRUCT_DRIFT_GRADE_DROP=2                   Grade drop severity threshold (A=3,B=2,C=1).
#   PLANNER_STRUCT_RELIABILITY_NUDGE=0.01               Apparent reliability uplift for grade A.
#
# DESIGN NOTES
#   - Structural metrics consumed from MissionPlanSchema.meta (PlanMeta).
#   - NO persistent reliability modification from structural signals (only apparent).
#   - All added metadata fields are additive / backward compatible.
#   - generate_plan / a_generate_plan remain the sole abstract obligations.
#
# SECURITY & STABILITY
#   - Self-test isolated in thread with timeout.
#   - Quarantine ensures unverified planners cannot silently degrade environment (unless disabled).
#   - Defensive checks around plan duck-typing to enforce canonical schema usage.
#
# EXTENSION IDEAS (Future)
#   - Adaptive reliability weighting by structural volatility trends.
#   - Planner ensemble arbitration layer (merge + reconcile).
#   - Negative drift penalties progression.
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
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, ClassVar

# =============================================================================
# Strict schema imports – MUST succeed (single source of truth)
# =============================================================================
from .schemas import MissionPlanSchema, PlanningContext

try:
    from .schemas import PlanMeta  # type hint only
except Exception:  # pragma: no cover
    PlanMeta = object  # type: ignore

# =============================================================================
# Refactored module imports
# =============================================================================
from ._configs import DriftDetectionConfig, SelfTestConfig, StructuralScoringConfig
from ._drift_detection import detect_structural_drift
from ._self_test_runner import run_self_test as _run_self_test_impl
from ._structural_scoring import (
    compute_final_selection_score,
    compute_structural_enrichment,
    safe_numeric,
)

# =============================================================================
# Logging
# =============================================================================
logger = logging.getLogger("overmind.planning.base_planner")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


# =============================================================================
# Error Helpers
# =============================================================================
def _flatten_extras(extra: dict[str, Any]) -> dict[str, Any]:
    # Simple shallow flattening hook (reserve for nested expansions if needed).
    flat: dict[str, Any] = {}
    for k, v in extra.items():
        flat[k] = v
    return flat


class PlannerError(Exception):
    """Unified planner exception with context rich formatting."""

    def __init__(
        self, message: str, planner_name: str = "unknown_planner", objective: str = "", **extra: Any
    ):
        base_msg = f"[{planner_name}] objective='{objective}' :: {message}"
        if extra:
            try:
                flat = _flatten_extras(extra)
                preview_items: list[str] = []
                for k, v in flat.items():
                    vs = repr(v)
                    if len(vs) > 40:
                        vs = vs[:37] + "..."
                    preview_items.append(f"{k}={vs}")
                preview_str = ", ".join(preview_items)
                if len(preview_str) > 180:
                    preview_str = preview_str[:177] + "..."
                base_msg += f" | extra: {preview_str}"
            except Exception as e:
                base_msg += f" | extra_format_error={e!r}"
        super().__init__(base_msg)
        self.planner_name = planner_name
        self.objective = objective
        self.raw_message = message
        self.extra: dict[str, Any] | None = extra or None
        self.extra_flat: dict[str, Any] | None = _flatten_extras(extra) if extra else None
        self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
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
    pass


class ExternalServiceError(PlannerError):
    pass


class PlannerTimeoutError(PlannerError):
    pass


class PlannerAdmissionError(PlannerError):
    pass


# =============================================================================
# Environment / Governance
# =============================================================================
_ENV = os.getenv("OVERMIND_ENV", "dev").strip().lower()
_ALLOW_LIST = {x.strip().lower() for x in os.getenv("PLANNERS_ALLOW", "").split(",") if x.strip()}
_BLOCK_LIST = {x.strip().lower() for x in os.getenv("PLANNERS_BLOCK", "").split(",") if x.strip()}
_DECAY_HALF_LIFE = float(os.getenv("PLANNER_DECAY_HALF_LIFE", "900"))
_MIN_RELIABILITY = float(os.getenv("PLANNER_MIN_RELIABILITY", "0.05"))
_FALLBACK_DEFAULT_TIMEOUT = float(os.getenv("PLANNER_DEFAULT_TIMEOUT", "40"))

_NAME_PATTERN = re.compile(r"^[a-z0-9_][a-z0-9_\-]{2,63}$")

# Configuration objects for refactored modules
_STRUCT_ENABLE = os.getenv("PLANNER_STRUCT_SCORE_ENABLE", "1") == "1"

_STRUCT_CONFIG = StructuralScoringConfig(
    grade_bonuses={
        "A": float(os.getenv("PLANNER_STRUCT_GRADE_BONUS_A", "0.05") or 0.05),
        "B": float(os.getenv("PLANNER_STRUCT_GRADE_BONUS_B", "0.02") or 0.02),
        "C": float(os.getenv("PLANNER_STRUCT_GRADE_BONUS_C", "0.0") or 0.0),
    },
    struct_weight=float(os.getenv("PLANNER_STRUCT_SCORE_WEIGHT", "0.07") or 0.07),
    reliability_nudge=float(os.getenv("PLANNER_STRUCT_RELIABILITY_NUDGE", "0.01") or 0.01),
)

_DRIFT_CONFIG = DriftDetectionConfig(
    task_ratio_threshold=float(os.getenv("PLANNER_STRUCT_DRIFT_TASK_RATIO", "0.30") or 0.30),
    grade_drop_threshold=int(os.getenv("PLANNER_STRUCT_DRIFT_GRADE_DROP", "2") or 2),
)

_SELF_TEST_CONFIG = SelfTestConfig(
    timeout_seconds=float(os.getenv("PLANNER_SELF_TEST_TIMEOUT", "5")),
    disable_quarantine=os.getenv("PLANNER_DISABLE_QUARANTINE", "0") == "1",
)



# =============================================================================
# Reliability State (exponential decay laplace-smoothed)
# =============================================================================
@dataclass
class _ReliabilityState:
    success_weight: float = 0.0
    failure_weight: float = 0.0
    last_update_ts: float = field(default_factory=time.time)
    total_invocations: int = 0
    total_failures: int = 0
    total_duration_ms: float = 0.0
    last_success_ts: float | None = None
    registration_time: float = field(default_factory=time.time)
    last_error: str | None = None

    quarantined: bool = False
    self_test_passed: bool | None = None
    production_ready: bool = False
    tier: str = "experimental"
    risk_rating: str = "medium"

    def decay(self, now: float | None = None):
        now = now or time.time()
        dt = now - self.last_update_ts
        if dt <= 0 or _DECAY_HALF_LIFE <= 0:
            self.last_update_ts = now
            return
        factor = 0.5 ** (dt / _DECAY_HALF_LIFE)
        self.success_weight *= factor
        self.failure_weight *= factor
        self.last_update_ts = now

    def update(self, success: bool, duration_seconds: float):
        self.decay()
        if success:
            self.success_weight += 1.0
            self.last_success_ts = time.time()
        else:
            self.failure_weight += 1.0
            self.total_failures += 1
        self.total_invocations += 1
        self.total_duration_ms += duration_seconds * 1000.0

    def reliability_score(self) -> float:
        # Laplace smoothing (1 prior success + 1 prior failure)
        num = self.success_weight + 1.0
        den = self.success_weight + self.failure_weight + 2.0
        score = num / den if den > 0 else 0.5
        return max(0.0, min(1.0, score))

    @property
    def avg_duration_ms(self) -> float:
        if self.total_invocations == 0:
            return 0.0
        return self.total_duration_ms / self.total_invocations


# =============================================================================
# BasePlanner Class
# =============================================================================
class BasePlanner:
    _registry: ClassVar[dict[str, type[BasePlanner]]] = {}
    _reliability: ClassVar[dict[str, _ReliabilityState]] = {}
    _lock: ClassVar[threading.RLock] = threading.RLock()

    # Overridable static attributes
    name: ClassVar[str] = "abstract_base"
    version: ClassVar[str | None] = None
    capabilities: ClassVar[set[str]] = set()
    production_ready: ClassVar[bool] = False
    tier: ClassVar[str] = "experimental"
    risk_rating: ClassVar[str] = "medium"
    default_timeout_seconds: ClassVar[float | None] = None
    allow_registration: ClassVar[bool] = True

    # --------------------------------------------------------------
    # Registration logic
    # --------------------------------------------------------------
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:
            BasePlanner._attempt_register(cls)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed registering planner subclass %s: %s", cls.__name__, exc)

    @classmethod
    def _attempt_register(cls, planner_cls: type[BasePlanner]):
        if planner_cls is BasePlanner:
            return
        if not getattr(planner_cls, "allow_registration", True):
            logger.debug(
                "Planner %s registration skipped (allow_registration=False).", planner_cls.__name__
            )
            return
        planner_name = getattr(planner_cls, "name", None)
        if not isinstance(planner_name, str):
            logger.error("Planner class %s missing 'name' attribute.", planner_cls.__name__)
            return
        key = planner_name.strip().lower()
        if not _NAME_PATTERN.match(key):
            logger.error("Planner name '%s' invalid (pattern).", key)
            return
        if key in _BLOCK_LIST:
            logger.warning("Planner '%s' blocked via PLANNERS_BLOCK.", key)
            return
        if _ALLOW_LIST and key not in _ALLOW_LIST:
            logger.info("Planner '%s' skipped (not in PLANNERS_ALLOW).", key)
            return
        with cls._lock:
            if key in cls._registry:
                logger.debug("Planner '%s' already registered.", key)
                return
            state = _ReliabilityState(
                quarantined=not _DISABLE_QUARANTINE,
                production_ready=getattr(planner_cls, "production_ready", False),
                tier=getattr(planner_cls, "tier", "experimental"),
                risk_rating=getattr(planner_cls, "risk_rating", "medium"),
            )
            cls._registry[key] = planner_cls
            cls._reliability[key] = state
        logger.info(
            "Registered planner '%s' (tier=%s prod_ready=%s quarantine=%s)",
            key,
            state.tier,
            state.production_ready,
            state.quarantined,
        )
        cls._run_self_test(planner_cls, key, state)

    @classmethod
    def _run_self_test(cls, planner_cls: type[BasePlanner], key: str, state: _ReliabilityState):
        """Refactored: delegates to extracted self-test runner module."""
        _run_self_test_impl(planner_cls, key, state, _ENV, _SELF_TEST_CONFIG)

    # --------------------------------------------------------------
    # Abstract contract
    # --------------------------------------------------------------
    def generate_plan(
        self, objective: str, context: PlanningContext | None = None
    ) -> MissionPlanSchema:
        """Implement in subclass."""
        raise NotImplementedError

    async def a_generate_plan(
        self, objective: str, context: PlanningContext | None = None
    ) -> MissionPlanSchema:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.generate_plan, objective, context)

    # --------------------------------------------------------------
    # Plan validation hook (lightweight)
    # --------------------------------------------------------------
    def validate_plan(
        self, plan: MissionPlanSchema, objective: str, context: PlanningContext | None = None
    ) -> None:
        if not hasattr(plan, "objective"):
            raise PlanValidationError("Plan missing 'objective' attribute.", self.name, objective)
        if not hasattr(plan, "tasks"):
            raise PlanValidationError("Plan missing 'tasks' attribute.", self.name, objective)

    # --------------------------------------------------------------
    # Reliability internal update
    # --------------------------------------------------------------
    @classmethod
    def _update_reliability(
        cls, name: str, success: bool, duration_seconds: float, error: str | None = None
    ):
        lower = name.lower()
        with cls._lock:
            state = cls._reliability.get(lower)
            if not state:
                return
            state.update(success, duration_seconds)
            if not success and error:
                state.last_error = error[:240]
            if success and state.quarantined and state.self_test_passed is not False:
                # Auto unquarantine on successful generation if self-test not definitively failed
                state.quarantined = False

    def current_reliability_score(self) -> float:
        with BasePlanner._lock:
            state = BasePlanner._reliability.get(self.name.lower())
            if not state:
                return 0.5
            state.decay()
            return state.reliability_score()

    @classmethod
    def planner_metadata(cls) -> dict[str, Any]:
        data: dict[str, Any] = {}
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
                    "last_error": st.last_error,
                    "version": getattr(cls._registry.get(name), "version", None),
                    "capabilities": sorted(getattr(cls._registry.get(name), "capabilities", [])),
                }
                data[name] = meta
        return data

    # --------------------------------------------------------------
    # Retrieval APIs
    # --------------------------------------------------------------
    @classmethod
    def get_planner_class(cls, name: str) -> type[BasePlanner]:
        key = name.lower()
        with cls._lock:
            if key not in cls._registry:
                raise PlannerAdmissionError(f"Planner '{name}' not registered.", name)
            state = cls._reliability.get(key)
            if state and state.quarantined:
                raise PlannerAdmissionError(f"Planner '{name}' is quarantined.", name)
            return cls._registry[key]

    @classmethod
    def instantiate(cls, name: str) -> BasePlanner:
        return cls.get_planner_class(name)()

    @classmethod
    def live_planner_classes(cls) -> dict[str, type[BasePlanner]]:
        accepted: dict[str, type[BasePlanner]] = {}
        with cls._lock:
            scored: list[tuple[str, type[BasePlanner], float]] = []
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
    def instantiate_all(cls) -> list[BasePlanner]:
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

    # --------------------------------------------------------------
    # Timeout helpers (sync)
    # --------------------------------------------------------------
    def _run_with_timeout(
        self, objective: str, context: PlanningContext | None, timeout: float
    ) -> MissionPlanSchema:
        container: dict[str, BaseException | MissionPlanSchema] = {}
        q: queue.Queue[int] = queue.Queue()

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
            raise PlannerTimeoutError(
                f"Timeout {timeout:.2f}s exceeded.", self.name, objective
            ) from exc

        if "error" in container:
            err = container["error"]
            if isinstance(err, PlannerError):
                raise err
            raise PlannerError(str(err), self.name, objective) from err
        result = container.get("result")
        if not isinstance(result, MissionPlanSchema):
            if hasattr(result, "objective") and hasattr(result, "tasks"):
                raise PlannerError(
                    "Planner returned non-canonical MissionPlanSchema (duck-type detected). "
                    "Ensure canonical schema usage.",
                    self.name,
                    objective,
                )
            raise PlannerError("Planner returned invalid result type.", self.name, objective)
        return result

    # --------------------------------------------------------------
    # Timeout helpers (async)
    # --------------------------------------------------------------
    async def _a_run_with_timeout(
        self, objective: str, context: PlanningContext | None, timeout: float
    ) -> MissionPlanSchema:
        try:
            return await asyncio.wait_for(self.a_generate_plan(objective, context), timeout=timeout)
        except TimeoutError as exc:
            raise PlannerTimeoutError(
                f"Async timeout {timeout:.2f}s exceeded.", self.name, objective
            ) from exc

    # --------------------------------------------------------------
    # Instrumented sync
    # --------------------------------------------------------------
    def instrumented_generate(
        self,
        objective: str,
        context: PlanningContext | None = None,
        *,
        include_node_count: bool = True,
        extra_metadata: dict[str, Any] | None = None,
        enforce_timeout: bool = True,
        deep_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        success_flag = False
        error_obj: Exception | None = None
        timeout = self.default_timeout_seconds or _FALLBACK_DEFAULT_TIMEOUT

        with BasePlanner._lock:
            st = BasePlanner._reliability.get(self.name.lower())
            if st and st.quarantined:
                raise PlannerAdmissionError(
                    "Planner is quarantined (self-test failed or pending).", self.name, objective
                )

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
                self.name, success_flag, duration, error=str(error_obj) if error_obj else None
            )

        # Validate
        try:
            self.validate_plan(plan, objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlanValidationError(
                f"Unexpected validation failure: {exc}", self.name, objective
            ) from exc

        duration = time.perf_counter() - start
        return self._enrich_and_finalize_plan(
            plan, objective, duration, deep_context, extra_metadata, include_node_count
        )

    def _enrich_and_finalize_plan(
        self,
        plan: MissionPlanSchema,
        objective: str,
        duration: float,
        deep_context: dict[str, Any] | None,
        extra_metadata: dict[str, Any] | None,
        include_node_count: bool,
    ) -> dict[str, Any]:
        """
        Refactored: Orchestrator calling focused helper modules (reduced complexity).
        Enriches plan with metadata and structural scores.
        """
        node_count = self._infer_node_count(plan) if include_node_count else None
        rel_score = self.current_reliability_score()

        # Build base metadata
        meta: dict[str, Any] = {
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
            "timestamp": time.time(),
            "deep_context_used": bool(deep_context),
        }
        if extra_metadata:
            meta.update(extra_metadata)

        # Structural enrichment (delegated to extracted module)
        struct_base = 0.0
        struct_bonus = 0.0
        if _STRUCT_ENABLE and isinstance(plan, MissionPlanSchema) and plan.meta:
            struct_result = compute_structural_enrichment(plan.meta, rel_score, _STRUCT_CONFIG)
            meta.update(struct_result.to_dict())
            struct_base = struct_result.struct_base_score
            struct_bonus = struct_result.struct_bonus

            # Drift detection (delegated to extracted module)
            drift_detected = detect_structural_drift(
                self.name, plan, struct_result.grade, _DRIFT_CONFIG
            )
            if drift_detected:
                meta["struct_drift"] = True

        # Final selection score computation
        base_selection = self.compute_selection_score(objective, None)
        final_selection = compute_final_selection_score(
            base_selection, struct_base, struct_bonus, _STRUCT_ENABLE, _STRUCT_CONFIG
        )

        meta["selection_score_base"] = round(base_selection, 4)
        meta["selection_score"] = round(final_selection, 4)

        return {"plan": plan, "meta": meta}

    # --------------------------------------------------------------
    # Instrumented async
    # --------------------------------------------------------------
    async def a_instrumented_generate(
        self,
        objective: str,
        context: PlanningContext | None = None,
        *,
        include_node_count: bool = True,
        extra_metadata: dict[str, Any] | None = None,
        enforce_timeout: bool = True,
        deep_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        success_flag = False
        error_obj: Exception | None = None
        timeout = self.default_timeout_seconds or _FALLBACK_DEFAULT_TIMEOUT

        with BasePlanner._lock:
            st = BasePlanner._reliability.get(self.name.lower())
            if st and st.quarantined:
                raise PlannerAdmissionError(
                    "Planner is quarantined (self-test failed or pending).", self.name, objective
                )

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
                self.name, success_flag, duration, error=str(error_obj) if error_obj else None
            )

        try:
            self.validate_plan(plan, objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlanValidationError(
                f"Unexpected validation failure: {exc}", self.name, objective
            ) from exc

        duration = time.perf_counter() - start
        return self._enrich_and_finalize_plan(
            plan, objective, duration, deep_context, extra_metadata, include_node_count
        )

    # --------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------
    def _infer_node_count(self, plan: MissionPlanSchema) -> int | None:
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
        self, objective: str, desired_capabilities: set[str] | None = None
    ) -> float:
        # Base compute (structural injection occurs AFTER in instrumented pipeline)
        rel_score = self.current_reliability_score()
        caps = getattr(self, "capabilities", set())
        if desired_capabilities:
            match = len(caps & desired_capabilities) / max(1, len(desired_capabilities))
        else:
            match = 1.0 if caps else 0.5
        length_factor = min(len(objective or "") / 500.0, 1.0)
        length_component = 0.10 * length_factor
        tier = getattr(self, "tier", "experimental")
        tier_adjust = {"core": 0.05, "experimental": 0.0, "shadow": -0.03}.get(tier, 0.0)
        prod_adjust = 0.03 if getattr(self, "production_ready", False) else 0.0
        base = rel_score * 0.55 + match * 0.30 + length_component
        score = base + tier_adjust + prod_adjust
        return max(0.0, min(1.0, score))

    def reliability_snapshot(self) -> dict[str, Any]:
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
                "last_error": st.last_error,
            }


# =============================================================================
# Public Utility Functions
# =============================================================================
def list_planner_metadata() -> dict[str, Any]:
    return BasePlanner.planner_metadata()


def instantiate_all_planners() -> list[BasePlanner]:
    return BasePlanner.instantiate_all()


def get_planner_instance(name: str) -> BasePlanner:
    return BasePlanner.instantiate(name)


# =============================================================================
# Exports
# =============================================================================
__all__ = [
    "BasePlanner",
    "ExternalServiceError",
    "PlanValidationError",
    "PlannerAdmissionError",
    "PlannerError",
    "PlannerTimeoutError",
    "get_planner_instance",
    "instantiate_all_planners",
    "list_planner_metadata",
]

# ======================================================================================
# END OF FILE
# ======================================================================================
