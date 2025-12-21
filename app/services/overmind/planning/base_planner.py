from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from collections.abc import Iterable
from typing import Any, ClassVar

from .schemas import MissionPlanSchema, PlanningContext

try:
    from .schemas import PlanMeta
except Exception:
    PlanMeta = object
from ._drift_detection import detect_structural_drift
from ._self_test_runner import run_self_test as _run_self_test_impl
from ._structural_scoring import compute_final_selection_score, compute_structural_enrichment
from .exceptions import (
    ExternalServiceError,
    PlannerAdmissionError,
    PlannerError,
    PlannerTimeoutError,
    PlanValidationError,
)
from .execution import run_with_timeout_async, run_with_timeout_sync
from .governance import DECAY_HALF_LIFE as _DECAY_HALF_LIFE
from .governance import DRIFT_CONFIG as _DRIFT_CONFIG
from .governance import ENV as _ENV
from .governance import FALLBACK_DEFAULT_TIMEOUT as _FALLBACK_DEFAULT_TIMEOUT
from .governance import MIN_RELIABILITY as _MIN_RELIABILITY
from .governance import SELF_TEST_CONFIG as _SELF_TEST_CONFIG
from .governance import STRUCT_CONFIG as _STRUCT_CONFIG
from .governance import STRUCT_ENABLE as _STRUCT_ENABLE
from .governance import is_planner_allowed
from .reliability import ReliabilityState

logger = logging.getLogger('overmind.planning.base_planner')
if not logger.handlers:
    logging.basicConfig(level=os.getenv('AGENT_TOOLS_LOG_LEVEL', 'INFO'),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')


class BasePlanner:
    _registry: ClassVar[dict[str, type[BasePlanner]]] = {}
    _reliability: ClassVar[dict[str, ReliabilityState]] = {}
    _lock: ClassVar[threading.RLock] = threading.RLock()
    name: ClassVar[str] = 'abstract_base'
    version: ClassVar[str | None] = None
    capabilities: ClassVar[set[str]] = set()
    production_ready: ClassVar[bool] = False
    tier: ClassVar[str] = 'experimental'
    risk_rating: ClassVar[str] = 'medium'
    default_timeout_seconds: ClassVar[float | None] = None
    allow_registration: ClassVar[bool] = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        try:
            BasePlanner._attempt_register(cls)
        except Exception as exc:
            logger.error('Failed registering planner subclass %s: %s', cls.
                __name__, exc)

    @classmethod
    def _attempt_register(cls, planner_cls: type[BasePlanner]):
        if planner_cls is BasePlanner:
            return
        if not getattr(planner_cls, 'allow_registration', True):
            logger.debug(
                'Planner %s registration skipped (allow_registration=False).',
                planner_cls.__name__)
            return
        planner_name = getattr(planner_cls, 'name', None)
        if not isinstance(planner_name, str):
            logger.error("Planner class %s missing 'name' attribute.",
                planner_cls.__name__)
            return
        key = planner_name.strip().lower()
        if not is_planner_allowed(key):
            logger.info("Planner '%s' skipped by governance policy.", key)
            return
        with cls._lock:
            if key in cls._registry:
                logger.debug("Planner '%s' already registered.", key)
                return
            state = ReliabilityState(quarantined=not _SELF_TEST_CONFIG.
                disable_quarantine, production_ready=getattr(planner_cls,
                'production_ready', False), tier=getattr(planner_cls,
                'tier', 'experimental'), risk_rating=getattr(planner_cls,
                'risk_rating', 'medium'))
            cls._registry[key] = planner_cls
            cls._reliability[key] = state
        logger.info(
            "Registered planner '%s' (tier=%s prod_ready=%s quarantine=%s)",
            key, state.tier, state.production_ready, state.quarantined)
        cls._run_self_test(planner_cls, key, state)

    @classmethod
    def _run_self_test(cls, planner_cls: type[BasePlanner], key: str, state:
        ReliabilityState):
        """Delegates to extracted self-test runner module."""
        _run_self_test_impl(planner_cls, key, state, _ENV, _SELF_TEST_CONFIG)

    def generate_plan(self, objective: str, context: (PlanningContext |
        None)=None) ->MissionPlanSchema:
        """Implement in subclass."""
        raise NotImplementedError

    async def a_generate_plan(self, objective: str, context: (
        PlanningContext | None)=None) ->MissionPlanSchema:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.generate_plan,
            objective, context)

    def validate_plan(self, plan: MissionPlanSchema, objective: str,
        context: (PlanningContext | None)=None) ->None:
        if not hasattr(plan, 'objective'):
            raise PlanValidationError("Plan missing 'objective' attribute.",
                self.name, objective)
        if not hasattr(plan, 'tasks'):
            raise PlanValidationError("Plan missing 'tasks' attribute.",
                self.name, objective)

    @classmethod
    def _update_reliability(cls, name: str, success: bool, duration_seconds:
        float, error: (str | None)=None):
        lower = name.lower()
        with cls._lock:
            state = cls._reliability.get(lower)
            if not state:
                return
            state.update(success, duration_seconds, _DECAY_HALF_LIFE)
            if not success and error:
                state.last_error = error[:240]
            if (success and state.quarantined and state.self_test_passed is not
                False):
                state.quarantined = False

    def current_reliability_score(self) ->float:
        with BasePlanner._lock:
            state = BasePlanner._reliability.get(self.name.lower())
            if not state:
                return 0.5
            state.decay(_DECAY_HALF_LIFE)
            return state.reliability_score()

    @classmethod
    def planner_metadata(cls) ->dict[str, Any]:
        data: dict[str, Any] = {}
        with cls._lock:
            for name, st in cls._reliability.items():
                st.decay(_DECAY_HALF_LIFE)
                meta = {'name': name, 'reliability_score': round(st.
                    reliability_score(), 4), 'total_invocations': st.
                    total_invocations, 'total_failures': st.total_failures,
                    'avg_duration_ms': round(st.avg_duration_ms, 2),
                    'last_success_ts': st.last_success_ts,
                    'registration_time': st.registration_time,
                    'quarantined': st.quarantined, 'self_test_passed': st.
                    self_test_passed, 'production_ready': st.
                    production_ready, 'tier': st.tier, 'risk_rating': st.
                    risk_rating, 'last_error': st.last_error, 'version':
                    getattr(cls._registry.get(name), 'version', None),
                    'capabilities': sorted(getattr(cls._registry.get(name),
                    'capabilities', []))}
                data[name] = meta
        return data

    @classmethod
    def get_planner_class(cls, name: str) ->type[BasePlanner]:
        key = name.lower()
        with cls._lock:
            if key not in cls._registry:
                raise PlannerAdmissionError(f"Planner '{name}' not registered."
                    , name)
            state = cls._reliability.get(key)
            if state and state.quarantined:
                raise PlannerAdmissionError(f"Planner '{name}' is quarantined."
                    , name)
            return cls._registry[key]

    @classmethod
    def instantiate(cls, name: str) ->BasePlanner:
        return cls.get_planner_class(name)()

    @classmethod
    def live_planner_classes(cls) ->dict[str, type[BasePlanner]]:
        accepted: dict[str, type[BasePlanner]] = {}
        with cls._lock:
            scored: list[tuple[str, type[BasePlanner], float]] = []
            for key, planner_cls in cls._registry.items():
                st = cls._reliability.get(key)
                if not st:
                    continue
                st.decay(_DECAY_HALF_LIFE)
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
    def instantiate_all(cls) ->list[BasePlanner]:
        return [p() for p in cls.live_planner_classes().values()]

    def instrumented_generate(self, objective: str, context: (
        PlanningContext | None)=None, *, include_node_count: bool=True,
        extra_metadata: (dict[str, Any] | None)=None, enforce_timeout: bool
        =True, deep_context: (dict[str, Any] | None)=None) ->dict[str, Any]:
        start = time.perf_counter()
        success_flag = False
        error_obj: Exception | None = None
        timeout = self.default_timeout_seconds or _FALLBACK_DEFAULT_TIMEOUT
        with BasePlanner._lock:
            st = BasePlanner._reliability.get(self.name.lower())
            if st and st.quarantined:
                raise PlannerAdmissionError(
                    'Planner is quarantined (self-test failed or pending).',
                    self.name, objective)
        try:
            if enforce_timeout and timeout:
                plan = run_with_timeout_sync(self.generate_plan, (objective,
                    context), self.name, objective, timeout)
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
            BasePlanner._update_reliability(self.name, success_flag,
                duration, error=str(error_obj) if error_obj else None)
        try:
            self.validate_plan(plan, objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlanValidationError(f'Unexpected validation failure: {exc}',
                self.name, objective) from exc
        duration = time.perf_counter() - start
        return self._enrich_and_finalize_plan(plan, objective, duration,
            deep_context, extra_metadata, include_node_count)

    async def a_instrumented_generate(self, objective: str, context: (
        PlanningContext | None)=None, *, include_node_count: bool=True,
        extra_metadata: (dict[str, Any] | None)=None, enforce_timeout: bool
        =True, deep_context: (dict[str, Any] | None)=None) ->dict[str, Any]:
        start = time.perf_counter()
        success_flag = False
        error_obj: Exception | None = None
        timeout = self.default_timeout_seconds or _FALLBACK_DEFAULT_TIMEOUT
        with BasePlanner._lock:
            st = BasePlanner._reliability.get(self.name.lower())
            if st and st.quarantined:
                raise PlannerAdmissionError(
                    'Planner is quarantined (self-test failed or pending).',
                    self.name, objective)
        try:
            if enforce_timeout and timeout:
                plan = await run_with_timeout_async(self.a_generate_plan(
                    objective, context), self.name, objective, timeout)
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
            BasePlanner._update_reliability(self.name, success_flag,
                duration, error=str(error_obj) if error_obj else None)
        try:
            self.validate_plan(plan, objective, context)
        except PlannerError:
            raise
        except Exception as exc:
            raise PlanValidationError(f'Unexpected validation failure: {exc}',
                self.name, objective) from exc
        duration = time.perf_counter() - start
        return self._enrich_and_finalize_plan(plan, objective, duration,
            deep_context, extra_metadata, include_node_count)

    def _enrich_and_finalize_plan(self, plan: MissionPlanSchema, objective:
        str, duration: float, deep_context: (dict[str, Any] | None),
        extra_metadata: (dict[str, Any] | None), include_node_count: bool
        ) ->dict[str, Any]:
        """
        Enriches plan with metadata and structural scores.
        """
        node_count = self._infer_node_count(plan
            ) if include_node_count else None
        rel_score = self.current_reliability_score()
        meta: dict[str, Any] = {'planner': self.name, 'version': getattr(
            self, 'version', None), 'duration_ms': round(duration * 1000.0,
            2), 'node_count': node_count, 'objective_length': len(objective or
            ''), 'reliability_score': round(rel_score, 4), 'capabilities':
            sorted(getattr(self, 'capabilities', [])), 'tier': getattr(self,
            'tier', 'experimental'), 'production_ready': getattr(self,
            'production_ready', False), 'risk_rating': getattr(self,
            'risk_rating', 'medium'), 'environment': _ENV, 'timestamp':
            time.time(), 'deep_context_used': bool(deep_context)}
        if extra_metadata:
            meta.update(extra_metadata)
        struct_base = 0.0
        struct_bonus = 0.0
        if _STRUCT_ENABLE and isinstance(plan, MissionPlanSchema
            ) and plan.meta:
            struct_result = compute_structural_enrichment(plan.meta,
                rel_score, _STRUCT_CONFIG)
            meta.update(struct_result.to_dict())
            struct_base = struct_result.struct_base_score
            struct_bonus = struct_result.struct_bonus
            drift_detected = detect_structural_drift(self.name, plan,
                struct_result.grade, _DRIFT_CONFIG)
            if drift_detected:
                meta['struct_drift'] = True
        base_selection = self.compute_selection_score(objective, None)
        final_selection = compute_final_selection_score(base_selection,
            struct_base, struct_bonus, _STRUCT_ENABLE, _STRUCT_CONFIG)
        meta['selection_score_base'] = round(base_selection, 4)
        meta['selection_score'] = round(final_selection, 4)
        return {'plan': plan, 'meta': meta}

    def _infer_node_count(self, plan: MissionPlanSchema) ->(int | None):
        for attr in ('tasks', 'nodes', 'steps'):
            if hasattr(plan, attr):
                seq = getattr(plan, attr)
                if isinstance(seq, Iterable):
                    try:
                        return len(list(seq))
                    except Exception:
                        return None
        return None

    def compute_selection_score(self, objective: str, desired_capabilities:
        (set[str] | None)=None) ->float:
        rel_score = self.current_reliability_score()
        caps = getattr(self, 'capabilities', set())
        if desired_capabilities:
            match = len(caps & desired_capabilities) / max(1, len(
                desired_capabilities))
        else:
            match = 1.0 if caps else 0.5
        length_factor = min(len(objective or '') / 500.0, 1.0)
        length_component = 0.1 * length_factor
        tier = getattr(self, 'tier', 'experimental')
        tier_adjust = {'core': 0.05, 'experimental': 0.0, 'shadow': -0.03}.get(
            tier, 0.0)
        prod_adjust = 0.03 if getattr(self, 'production_ready', False) else 0.0
        base = rel_score * 0.55 + match * 0.3 + length_component
        score = base + tier_adjust + prod_adjust
        return max(0.0, min(1.0, score))


def list_planner_metadata() ->dict[str, Any]:
    return BasePlanner.planner_metadata()


def instantiate_all_planners() ->list[BasePlanner]:
    return BasePlanner.instantiate_all()


def get_planner_instance(name: str) ->BasePlanner:
    return BasePlanner.instantiate(name)


__all__ = ['BasePlanner', 'ExternalServiceError', 'PlanValidationError',
    'PlannerAdmissionError', 'PlannerError', 'PlannerTimeoutError',
    'get_planner_instance', 'instantiate_all_planners', 'list_planner_metadata'
    ]
