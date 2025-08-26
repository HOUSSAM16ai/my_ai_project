# app/services/master_agent_service.py
# ======================================================================================
#  OVERMIND ORCHESTRATION SERVICE (v4.4 • "TERMINAL-VISION / ANTI-PENDING UPRISING")    #
# ======================================================================================
#  PURPOSE:
#    تحويل الـ Objective إلى خطة ثم تنفيذها (Topological / Wave) مع إصلاح جذري
#    لمشكلة "شلل الحالة" حيث تبقى الـ Mission في RUNNING بعد انتهاء المهام.
#
#  CORE FIXES (v4.4):
#    1) TERMINAL VISION: لم يعد التحكم في حلقة الحياة (_tick) يعتمد فقط على تغيّر
#       حالة الـ Mission؛ أضفنا فحصاً متكرراً (Polling + Event) حتى تُغلق كل المهام.
#    2) EVENT-DRIVEN CHECK: استدعاء _check_terminal بعد نهاية كل Task (نجاح/فشل)
#       لضمان الإعلان المبكر عن النجاح أو الفشل.
#    3) POLLING LOOP REWRITE: إعادة كتابة _tick لتستمر بينما توجد مهام مفتوحة
#       (PENDING / RETRY / RUNNING) حتى تتحول الـ Mission إلى حالة نهائية.
#    4) ALIAS EXECUTION: استمرار دعم تنفيذ الأدوات عبر resolve_tool_name مع
#       تسجيل أوضح للـ canonical_tool.
#    5) ROBUST TOOL RESULT EXTRACTION: دعم صيغ ToolResult مختلفة (result / data /
#       content) بدون انكسار.
#    6) CONFIGURABLE POLL INTERVAL: متغير بيئة OVERMIND_POLL_INTERVAL_SECONDS
#       (افتراضي 0.18 ثانية).
#    7) SAFETY: حماية ضد تجاوز الزمن الكلي (MAX_TOTAL_RUNTIME_SECONDS) وإنهاء أنيق.
#
#  HIGH-LEVEL EXECUTION DECISION:
#      if task.tool_name:
#           _execute_tool(...)   --> تنفيذ مباشر للأدوات (registry) + alias resolution
#      else:
#           maestro.execute_task(task)  --> تنفيذ معرفي (LLM / multi-step) داخل generation_service
#
#  TERMINAL CHECK CRITERIA:
#      - لا يوجد أي Task بحالة PENDING / RETRY / RUNNING
#      - إن وجدت FAILED:
#            * إذا فشل >= REPLAN_FAILURE_THRESHOLD وسمح التكيّف => ADAPTING
#            * وإلا => FAILED
#        وإلا (بدون failed) => SUCCESS
#
#  ENVIRONMENT FLAGS:
#      OVERMIND_POLL_INTERVAL_SECONDS   (float, default=0.18)
#      OVERMIND_MAX_LIFECYCLE_TICKS     (int,   default=1000)
#      OVERMIND_LOG_DEBUG=1            (verbose internal logs)
#
# ======================================================================================

from __future__ import annotations

import json
import os
import random
import threading
import time
from dataclasses import dataclass
from contextlib import contextmanager
from datetime import timedelta
from typing import Any, Dict, List, Optional

from flask import current_app
from sqlalchemy import select, func, exists
from sqlalchemy.orm import joinedload

from app import db

# --------------------------------------------------------------------------------------
# Domain imports
# --------------------------------------------------------------------------------------
from app.models import (
    User,
    Mission, MissionPlan, Task,
    MissionStatus, TaskStatus, PlanStatus,
    MissionEventType,
    log_mission_event,
    update_mission_status,
    utc_now
)

# --------------------------------------------------------------------------------------
# Planner system
# --------------------------------------------------------------------------------------
try:
    from app.overmind.planning.factory import get_all_planners
except ImportError:  # pragma: no cover
    def get_all_planners():
        return []

from app.overmind.planning.schemas import MissionPlanSchema, PlanWarning

# --------------------------------------------------------------------------------------
# Maestro (Generation / Task Executor)
# --------------------------------------------------------------------------------------
try:
    from app.services import generation_service as maestro
except ImportError:  # pragma: no cover
    class maestro:  # fallback mock
        @staticmethod
        def execute_task(task: Task):
            task.result_text = f"[MOCK EXECUTION] {task.description or ''}"
            task.status = TaskStatus.SUCCESS
            task.finished_at = utc_now()
            db.session.commit()

# --------------------------------------------------------------------------------------
# Agent Tools
# --------------------------------------------------------------------------------------
try:
    from app.services import agent_tools
except ImportError:  # pragma: no cover
    agent_tools = None  # Will cause ToolNotFound if referenced

# --------------------------------------------------------------------------------------
# Policy / Verification Stubs
# --------------------------------------------------------------------------------------
class ToolPolicyEngine:
    def authorize(self, tool_name: str, mission: Mission, task: Task) -> bool:
        return True
tool_policy_engine = ToolPolicyEngine()

class VerificationService:
    def verify(self, task: Task) -> bool:
        return True
verification_service = VerificationService()

# --------------------------------------------------------------------------------------
# Metrics Hooks (stubs)
# --------------------------------------------------------------------------------------
def increment_counter(name: str, labels: Dict[str, str] | None = None): pass
def observe_histogram(name: str, value: float, labels: Dict[str, str] | None = None): pass
def set_gauge(name: str, value: float, labels: Dict[str, str] | None = None): pass

# --------------------------------------------------------------------------------------
# Config / Constants
# --------------------------------------------------------------------------------------
OVERMIND_VERSION = "4.4-terminal-vision"

DEFAULT_MAX_TASK_ATTEMPTS = 3
ADAPTIVE_MAX_CYCLES = 3
REPLAN_FAILURE_THRESHOLD = 2

EXECUTION_STRATEGY = "topological"      # "topological" | "wave_legacy"
TOPO_MAX_PARALLEL = 6
TASK_EXECUTION_HARD_TIMEOUT_SECONDS = 180

TASK_RETRY_BACKOFF_BASE = 2.0
TASK_RETRY_BACKOFF_JITTER = 0.5
MAX_TOTAL_RUNTIME_SECONDS = 7200  # 2h safety cap

# Poll configuration
DEFAULT_POLL_INTERVAL = float(os.getenv("OVERMIND_POLL_INTERVAL_SECONDS", "0.18"))
MAX_LIFECYCLE_TICKS = int(os.getenv("OVERMIND_MAX_LIFECYCLE_TICKS", "1000"))

STALL_DETECTION_WINDOW = 10
STALL_NO_PROGRESS_THRESHOLD = 0

VERBOSE_DEBUG = os.getenv("OVERMIND_LOG_DEBUG", "0") == "1"

# --------------------------------------------------------------------------------------
# Logging Helpers
# --------------------------------------------------------------------------------------
def _log(level: str, mission: Mission | None, message: str, **extra):
    payload = {
        "layer": "overmind",
        "component": "orchestrator",
        "mission_id": getattr(mission, "id", None),
        "message": message,
        **extra
    }
    line = json.dumps(payload, ensure_ascii=False)
    logger = current_app.logger
    if level == "info":
        logger.info(line)
    elif level == "warn":
        logger.warning(line)
    elif level == "error":
        logger.error(line)
    else:
        logger.debug(line)

def log_info(mission: Mission | None, message: str, **extra): _log("info", mission, message, **extra)
def log_warn(mission: Mission | None, message: str, **extra): _log("warn", mission, message, **extra)
def log_error(mission: Mission | None, message: str, **extra): _log("error", mission, message, **extra)
def log_debug(mission: Mission | None, message: str, **extra):
    if VERBOSE_DEBUG:
        _log("debug", mission, f"[DEBUG] {message}", **extra)

# --------------------------------------------------------------------------------------
# Mission Lock (advisory stub)
# --------------------------------------------------------------------------------------
@contextmanager
def mission_lock(mission_id: int):
    # TODO: Replace with DB advisory/Redis lock for distributed deployment.
    yield

# --------------------------------------------------------------------------------------
# Error Taxonomy
# --------------------------------------------------------------------------------------
class OrchestratorError(Exception): pass
class PlannerSelectionError(OrchestratorError): pass
class PlanPersistenceError(OrchestratorError): pass
class TaskExecutionError(OrchestratorError): pass
class PolicyDeniedError(OrchestratorError): pass
class AdaptiveReplanError(OrchestratorError): pass

# --------------------------------------------------------------------------------------
# Selection Data Structure
# --------------------------------------------------------------------------------------
@dataclass
class CandidatePlan:
    raw: MissionPlanSchema
    planner_name: str
    score: float
    rationale: str
    telemetry: Dict[str, Any]

# ======================================================================================
# Overmind Service
# ======================================================================================
class OvermindService:

    # ----------------------------- Public API -----------------------------------------
    def start_new_mission(self, objective: str, initiator: User) -> Mission:
        mission = Mission(
            objective=objective,
            initiator=initiator,
            status=MissionStatus.PENDING
        )
        db.session.add(mission)
        db.session.commit()
        log_mission_event(
            mission,
            MissionEventType.CREATED,
            payload={"objective": objective, "version": OVERMIND_VERSION}
        )
        db.session.commit()
        log_info(mission, "Mission created; starting lifecycle", objective=objective)
        self.run_mission_lifecycle(mission.id)
        return mission

    def run_mission_lifecycle(self, mission_id: int):
        mission = Mission.query.options(joinedload(Mission.tasks)).get(mission_id)
        if not mission:
            current_app.logger.error(f"[Overmind] Mission {mission_id} not found.")
            return
        started = time.perf_counter()
        with mission_lock(mission.id):
            try:
                self._tick(mission, overall_start_perf=started)
            except Exception as e:
                log_error(mission, "Lifecycle catastrophic failure", error=str(e))
                update_mission_status(mission, MissionStatus.FAILED, note=f"Fatal: {e}")
                db.session.commit()

    # --------------------------- Main State Loop (Polling + Event) --------------------
    def _tick(self, mission: Mission, overall_start_perf: float):
        """
        إعادة تصميم الحلقة:
          - تستمر أثناء وجود مهام مفتوحة أو حالة قابلة للتقدم.
          - لا تتوقف مبكراً بمجرد عدم تغيّر status في دورة واحدة.
        """
        loops = 0
        while loops < MAX_LIFECYCLE_TICKS:
            loops += 1

            if (time.perf_counter() - overall_start_perf) > MAX_TOTAL_RUNTIME_SECONDS:
                update_mission_status(mission, MissionStatus.FAILED, note="Exceeded total runtime limit.")
                db.session.commit()
                log_warn(mission, "Mission terminated due to total runtime limit.")
                break

            log_debug(mission, "Lifecycle loop tick", loop=loops, status=str(mission.status))

            if mission.status == MissionStatus.PENDING:
                self._plan_phase(mission)

            elif mission.status == MissionStatus.PLANNING:
                # Planners may be async or multi-step; brief wait
                time.sleep(0.05)

            elif mission.status == MissionStatus.PLANNED:
                self._prepare_execution(mission)

            elif mission.status == MissionStatus.RUNNING:
                if EXECUTION_STRATEGY == "topological":
                    self._execution_phase(mission)
                else:
                    self._execution_wave_legacy(mission)

                # Always re-check terminal conditions
                self._check_terminal(mission)

                # If still running and there remain open tasks -> poll sleep
                if mission.status == MissionStatus.RUNNING and self._has_open_tasks(mission):
                    time.sleep(DEFAULT_POLL_INTERVAL)
                else:
                    # Either success/failure or no open tasks (terminal check will adjust)
                    pass

            elif mission.status == MissionStatus.ADAPTING:
                self._adaptive_replan(mission)

            elif mission.status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                log_debug(mission, "Mission reached terminal state; exiting loop.")
                break

            # Refresh mission state & tasks
            try:
                db.session.refresh(mission)
            except Exception:
                db.session.rollback()

            # Stop if terminal
            if mission.status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                break

            # If running but no tasks open -> do a final terminal check and break
            if mission.status == MissionStatus.RUNNING and not self._has_open_tasks(mission):
                self._check_terminal(mission)
                db.session.refresh(mission)
                if mission.status in (MissionStatus.SUCCESS, MissionStatus.FAILED):
                    break
                # Safety sleep to avoid frantic loop
                time.sleep(0.05)

        else:
            # Loop exhaustion
            if mission.status == MissionStatus.RUNNING:
                log_warn(mission, "Lifecycle tick limit reached while still RUNNING.")
                self._check_terminal(mission)
                db.session.commit()

    # ------------------------------ Planning Phase ------------------------------------
    def _plan_phase(self, mission: Mission):
        update_mission_status(mission, MissionStatus.PLANNING, note="Planning started.")
        db.session.commit()
        log_info(mission, "Planning phase initiated.")

        planners = get_all_planners()
        if not planners:
            update_mission_status(mission, MissionStatus.FAILED, note="No planners available.")
            db.session.commit()
            return

        candidates: List[CandidatePlan] = []
        for planner in planners:
            try:
                result = planner.instrumented_generate(mission.objective, context=None)
                raw_schema = result.plan
                planner_name = result.planner_name
                score = self._score_plan(raw_schema, result.metadata)
                rationale = self._build_plan_rationale(raw_schema, score, result.metadata)
                candidates.append(CandidatePlan(
                    raw=raw_schema,
                    planner_name=planner_name,
                    score=score,
                    rationale=rationale,
                    telemetry={
                        "duration": result.duration_seconds,
                        "node_count": result.node_count,
                        **result.metadata
                    }
                ))
                log_info(mission, "Planner candidate produced",
                         planner=planner_name, score=score, duration=f"{result.duration_seconds:.4f}")
            except Exception as e:
                log_warn(mission, "Planner failed",
                         planner=getattr(planner, "name", "unknown"), error=str(e))

        if not candidates:
            update_mission_status(mission, MissionStatus.FAILED, note="All planners failed.")
            db.session.commit()
            return

        best = max(candidates, key=lambda c: c.score)
        version = self._next_plan_version(mission.id)
        try:
            self._persist_plan(mission, best, version)
        except Exception as e:
            update_mission_status(mission, MissionStatus.FAILED, note=f"Plan persistence error: {e}")
            db.session.commit()
            return

        update_mission_status(mission, MissionStatus.PLANNED, note=f"Plan v{version} selected.")
        db.session.commit()
        log_mission_event(
            mission,
            MissionEventType.PLAN_SELECTED,
            payload={"version": version, "planner": best.planner_name, "score": best.score}
        )
        log_info(mission, "Plan selected", planner=best.planner_name, plan_version=version, score=best.score)

    def _score_plan(self, plan: MissionPlanSchema, metadata: Dict[str, Any]) -> float:
        stats = plan.stats or {}
        tasks = stats.get("tasks", len(getattr(plan, "tasks", [])))
        roots = stats.get("roots", 0)
        longest_path = stats.get("longest_path", 1)
        risk_counts = stats.get("risk_counts", {})
        high_risk = risk_counts.get("HIGH", 0)
        if tasks == 0:
            return 0.0
        parallel_factor = roots / tasks if tasks else 0
        risk_penalty = high_risk * 2
        depth_penalty = max(longest_path - 25, 0) * 0.5
        size_penalty = max(tasks - 120, 0) * 0.2
        base = 100.0 + (parallel_factor * 15.0) - risk_penalty - depth_penalty - size_penalty
        return round(base, 3)

    def _build_plan_rationale(self, plan: MissionPlanSchema, score: float, metadata: Dict[str, Any]) -> str:
        stats = plan.stats or {}
        return "; ".join([
            f"score={score}",
            f"tasks={stats.get('tasks')}",
            f"roots={stats.get('roots')}",
            f"high_risk={stats.get('risk_counts', {}).get('HIGH', 0)}",
            f"longest_path={stats.get('longest_path')}",
        ])

    def _next_plan_version(self, mission_id: int) -> int:
        max_version = db.session.scalar(
            select(func.max(MissionPlan.version)).where(MissionPlan.mission_id == mission_id)
        )
        return (max_version or 0) + 1

    # ------------------------- Persist Plan & Tasks -----------------------------------
    def _persist_plan(self, mission: Mission, candidate: CandidatePlan, version: int):
        schema = candidate.raw
        stats_json = json.dumps(schema.stats or {}, ensure_ascii=False)
        warnings_list = [
            (w.model_dump() if isinstance(w, PlanWarning) else w)
            for w in (schema.warnings or [])
        ]
        warnings_json = json.dumps(warnings_list, ensure_ascii=False)

        raw_json = json.dumps({
            "objective": schema.objective,
            "topological_order": schema.topological_order,
            "stats": schema.stats,
            "warnings": warnings_list
        }, ensure_ascii=False)

        mp = MissionPlan(
            mission_id=mission.id,
            version=version,
            planner_name=candidate.planner_name,
            status=PlanStatus.VALID,
            score=candidate.score,
            rationale=candidate.rationale,
            raw_json=raw_json,
            stats_json=stats_json,
            warnings_json=warnings_json,
            content_hash=schema.content_hash
        )
        db.session.add(mp)
        db.session.flush()

        for t in schema.tasks:
            task_row = Task(
                mission_id=mission.id,
                plan_id=mp.id,
                task_key=t.task_id,
                description=t.description,
                tool_name=t.tool_name,            # may be alias like 'file_system'
                tool_args_json=t.tool_args,
                status=TaskStatus.PENDING,
                attempt_count=0,
                max_attempts=DEFAULT_MAX_TASK_ATTEMPTS,
                priority=t.priority,
                risk_level=t.risk_level.value if hasattr(t.risk_level, "value") else str(t.risk_level),
                criticality=t.criticality.value if hasattr(t.criticality, "value") else str(t.criticality),
                depends_on_json=t.dependencies
            )
            db.session.add(task_row)

        mission.active_plan_id = mp.id
        db.session.commit()
        increment_counter("overmind_plans_created_total", {"planner": candidate.planner_name})

    # ---------------------------- Prepare Execution -----------------------------------
    def _prepare_execution(self, mission: Mission):
        update_mission_status(mission, MissionStatus.RUNNING, note="Execution initiated.")
        db.session.commit()
        log_mission_event(
            mission,
            MissionEventType.EXECUTION_STARTED,
            payload={"plan_id": mission.active_plan_id, "strategy": EXECUTION_STRATEGY}
        )
        db.session.commit()
        log_info(mission, "Execution phase started.", strategy=EXECUTION_STRATEGY)
        increment_counter("overmind_missions_started_total")

    # ==================================================================================
    # Topological Execution Phase
    # ==================================================================================
    def _execution_phase(self, mission: Mission):
        plan = MissionPlan.query.get(mission.active_plan_id)
        if not plan:
            log_error(mission, "Active plan not found; cannot execute.")
            update_mission_status(mission, MissionStatus.FAILED, note="No active plan.")
            db.session.commit()
            return

        try:
            raw = plan.raw_json if isinstance(plan.raw_json, dict) else json.loads(plan.raw_json or "{}")
        except Exception:
            raw = {}
        topo_layers: List[List[str]] = raw.get("topological_order") or []
        if not topo_layers:
            topo_layers = [[t.task_key for t in mission.tasks]]

        task_index: Dict[str, Task] = {t.task_key: t for t in mission.tasks}

        total_success_before = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.SUCCESS).count()
        progress_attempted = False

        for layer_idx, layer_keys in enumerate(topo_layers):
            layer_tasks = [task_index.get(k) for k in layer_keys if task_index.get(k)]
            if layer_tasks and all(t.status in (TaskStatus.SUCCESS, TaskStatus.FAILED) for t in layer_tasks):
                continue

            ready: List[Task] = []
            for t in layer_tasks:
                if t.status not in (TaskStatus.PENDING, TaskStatus.RETRY):
                    continue
                deps = t.depends_on_json or []
                dep_ok = True
                for d in deps:
                    dep_task = task_index.get(d)
                    if not dep_task:
                        log_warn(mission, "Missing dependency reference", task_key=t.task_key, missing=d)
                        dep_ok = False
                        break
                    if dep_task.status != TaskStatus.SUCCESS:
                        dep_ok = False
                        break
                if dep_ok:
                    ready.append(t)

            if not ready:
                continue

            if len(ready) > TOPO_MAX_PARALLEL:
                ready = ready[:TOPO_MAX_PARALLEL]

            log_info(mission, "Executing layer batch",
                     layer=layer_idx, batch_size=len(ready), layer_total=len(layer_tasks))
            progress_attempted = True

            threads: List[threading.Thread] = []
            for tk in ready:
                th = threading.Thread(
                    target=self._execute_task_with_retry_topological,
                    args=(mission, tk, layer_idx),
                    daemon=True
                )
                th.start()
                threads.append(th)

            for th in threads:
                th.join(timeout=TASK_EXECUTION_HARD_TIMEOUT_SECONDS)

        total_success_after = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.SUCCESS).count()
        newly = total_success_after - total_success_before
        self._update_stall_metrics(mission, newly, progress_attempted)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    # ------------------ Legacy Fallback (Wave) ----------------------------------------
    def _execution_wave_legacy(self, mission: Mission):
        ready = self._find_ready_tasks(mission)
        if not ready:
            failed_count = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.FAILED).count()
            pending_count = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.PENDING).count()
            retry_count = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.RETRY).count()
            if pending_count == 0 and retry_count == 0 and failed_count > 0:
                if failed_count >= REPLAN_FAILURE_THRESHOLD:
                    update_mission_status(mission, MissionStatus.ADAPTING, note="Triggering adaptive replan.")
                    db.session.commit()
            time.sleep(0.05)
            return
        for t in ready[:TOPO_MAX_PARALLEL]:
            self._execute_task_with_retry_topological(mission, t, layer_index=-1)

    # ---------------------------- Stall Tracking --------------------------------------
    def _update_stall_metrics(self, mission: Mission, newly_success: int, attempted: bool):
        key = f"_stall_state_{mission.id}"
        state = getattr(self, key, {"window": [], "cycles": 0})
        state["window"].append(newly_success)
        if len(state["window"]) > STALL_DETECTION_WINDOW:
            state["window"].pop(0)
        if newly_success <= STALL_NO_PROGRESS_THRESHOLD and not attempted:
            state["cycles"] += 1
        else:
            state["cycles"] = 0
        setattr(self, key, state)
        if state["cycles"] > STALL_DETECTION_WINDOW:
            log_warn(mission, "Potential execution stall detected",
                     window=state["window"], cycles=state["cycles"])

    # ---------------------- Ready Discovery (Legacy Wave) -----------------------------
    def _find_ready_tasks(self, mission: Mission) -> List[Task]:
        candidates: List[Task] = Task.query.filter(
            Task.mission_id == mission.id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.RETRY])
        ).all()
        ready: List[Task] = []
        for t in candidates:
            deps = t.depends_on_json or []
            if not deps:
                ready.append(t)
                continue
            dep_rows = Task.query.filter(
                Task.mission_id == mission.id,
                Task.task_key.in_(deps)
            ).all()
            if len(dep_rows) != len(deps):
                log_warn(mission, "Task has missing dependency reference", task_key=t.task_key)
                continue
            if all(dr.status == TaskStatus.SUCCESS for dr in dep_rows):
                ready.append(t)
        return ready

    # ------------------ Core Execution (Retry Wrapper) --------------------------------
    def _execute_task_with_retry_topological(self, mission: Mission, task: Task, layer_index: int):
        # Refresh row to guard against stale session state
        task = Task.query.get(task.id)
        if not task or task.status not in (TaskStatus.PENDING, TaskStatus.RETRY):
            return

        nxt = getattr(task, "next_retry_at", None)
        if nxt and utc_now() < nxt:
            return

        if task.tool_name and not tool_policy_engine.authorize(task.tool_name, mission, task):
            task.status = TaskStatus.FAILED
            task.error_text = "PolicyDenied"
            db.session.commit()
            log_warn(mission, "Policy denied tool", task_key=task.task_key, tool=task.tool_name)
            self._safe_terminal_event(mission)
            return

        attempt_index = task.attempt_count + 1
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        db.session.commit()

        log_mission_event(
            mission,
            MissionEventType.TASK_STARTED,
            payload={
                "task_id": task.id,
                "task_key": task.task_key,
                "layer": layer_index,
                "attempt": attempt_index,
                "tool": task.tool_name
            }
        )
        log_debug(mission, "Task started", task_key=task.task_key, attempt=attempt_index, tool=task.tool_name)

        perf_start = time.perf_counter()

        try:
            if task.tool_name:  # Direct Tool Task
                result_payload = self._execute_tool(task)
                if not verification_service.verify(task):
                    raise TaskExecutionError("Verification failed.")
                task.result_text = (result_payload.get("result_text") or "")[:5000]
                extra_meta = result_payload.get("meta")
                if hasattr(task, "result_meta_json") and extra_meta:
                    try:
                        task.result_meta_json = extra_meta
                    except Exception:
                        pass
                task.status = TaskStatus.SUCCESS
            else:  # Delegated to Maestro
                if hasattr(maestro, "execute_task"):
                    maestro.execute_task(task)  # expected to set status
                    db.session.refresh(task)
                    if task.status == TaskStatus.RUNNING:  # Defensive; Maestro forgot to finalize
                        task.status = TaskStatus.SUCCESS
                else:
                    task.result_text = "[Generic Execution Fallback]"
                    task.status = TaskStatus.SUCCESS

            task.attempt_count = attempt_index
            task.finished_at = utc_now()
            task.duration_ms = int((time.perf_counter() - perf_start) * 1000)
            db.session.commit()

            increment_counter("overmind_tasks_executed_total", {"result": "success"})
            log_mission_event(
                mission,
                MissionEventType.TASK_COMPLETED,
                payload={"task_id": task.id, "attempt": attempt_index, "layer": layer_index}
            )
            log_info(
                mission,
                "Task success",
                task_key=task.task_key,
                attempt=attempt_index,
                layer=layer_index,
                duration_ms=task.duration_ms
            )

        except Exception as e:
            # Reload row safely (avoid stale state)
            try:
                db.session.refresh(task)
            except Exception:
                pass
            task.attempt_count = attempt_index
            task.error_text = str(e)[:500]
            task.finished_at = utc_now()
            task.duration_ms = int((time.perf_counter() - perf_start) * 1000)

            allow_retry = task.attempt_count < task.max_attempts
            if allow_retry:
                task.status = TaskStatus.RETRY
                backoff = self._compute_backoff(task.attempt_count)
                if hasattr(task, "next_retry_at"):
                    task.next_retry_at = utc_now() + timedelta(seconds=backoff)
                log_warn(
                    mission,
                    "Task failed; scheduling retry",
                    task_key=task.task_key,
                    attempt=task.attempt_count,
                    backoff_s=round(backoff, 2),
                    error=str(e)
                )
                log_mission_event(
                    mission,
                    MissionEventType.TASK_FAILED,
                    payload={
                        "task_id": task.id,
                        "attempt": task.attempt_count,
                        "retry": True,
                        "layer": layer_index,
                        "error": str(e)[:200]
                    }
                )
                increment_counter("overmind_tasks_executed_total", {"result": "retry"})
            else:
                task.status = TaskStatus.FAILED
                log_warn(
                    mission,
                    "Task failed permanently",
                    task_key=task.task_key,
                    attempt=task.attempt_count,
                    error=str(e)
                )
                log_mission_event(
                    mission,
                    MissionEventType.TASK_FAILED,
                    payload={
                        "task_id": task.id,
                        "attempt": task.attempt_count,
                        "retry": False,
                        "layer": layer_index,
                        "error": str(e)[:200]
                    }
                )
                increment_counter("overmind_tasks_executed_total", {"result": "failed"})
            db.session.commit()

        # EVENT-DRIVEN TERMINAL CHECK
        self._safe_terminal_event(mission)

    # ------------------------------ Tool Execution Core --------------------------------
    def _execute_tool(self, task: Task) -> Dict[str, Any]:
        """
        تنفيذ مباشر للأدوات عبر سجل agent_tools مع دعم aliases.
        يعيد Payload موحد:
            {
              "status": "success" | "error",
              "result_text": "...",
              "data": {...} أو قيمة,
              "meta": {...}
            }
        يرفع TaskExecutionError عند الفشل.
        """
        if agent_tools is None:
            raise TaskExecutionError("Agent tools module not available.")

        tool_name_raw = task.tool_name or ""
        if not tool_name_raw:
            raise TaskExecutionError("Empty tool_name for tool execution path.")

        # Alias resolution
        canonical = None
        if hasattr(agent_tools, "resolve_tool_name"):
            try:
                canonical = agent_tools.resolve_tool_name(tool_name_raw)
            except Exception:
                canonical = None
        canonical = canonical or tool_name_raw

        registry = getattr(agent_tools, "_TOOL_REGISTRY", {})
        meta = registry.get(tool_name_raw) or registry.get(canonical)
        if not meta:
            raise TaskExecutionError(f"ToolNotFound: {tool_name_raw}")

        handler = meta.get("handler")
        if not handler:
            raise TaskExecutionError(f"ToolHandlerMissing: {tool_name_raw}")

        args = task.tool_args_json or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {"raw": args}

        try:
            result_obj = handler(**args)
        except TypeError as te:
            raise TaskExecutionError(f"ToolArgError: {te}") from te
        except Exception as ex:
            raise TaskExecutionError(f"ToolRaised: {ex}") from ex

        # Normalization
        status_ok = True
        result_text = ""
        meta_payload = {"canonical_tool": canonical, "invocation_tool_name": tool_name_raw}
        data_payload = None

        # ToolResult pattern attempts
        if hasattr(result_obj, "ok"):
            status_ok = getattr(result_obj, "ok", True)
            # unify possible payload locations
            candidate_attrs = ["data", "result", "content", "_content"]
            for attr in candidate_attrs:
                if hasattr(result_obj, attr):
                    data_payload = getattr(result_obj, attr)
                    if data_payload is not None:
                        break
            error_attr = getattr(result_obj, "error", None)
            if not status_ok and error_attr:
                raise TaskExecutionError(f"ToolFailed: {error_attr}")
            # meta
            if hasattr(result_obj, "meta"):
                try:
                    meta_field = getattr(result_obj, "meta")
                    if isinstance(meta_field, dict):
                        meta_payload.update(meta_field)
                except Exception:
                    pass
        else:
            # Raw return (dict / str / other)
            data_payload = result_obj

        # Derive result_text
        if isinstance(data_payload, dict):
            if "content" in data_payload and isinstance(data_payload["content"], str):
                result_text = data_payload["content"]
            elif "written" in data_payload:
                result_text = f"File written: {data_payload['written']}"
            elif "appended" in data_payload:
                result_text = f"Appended: {data_payload['appended']}"
            else:
                try:
                    result_text = json.dumps(data_payload, ensure_ascii=False)[:1000]
                except Exception:
                    result_text = str(data_payload)[:1000]
        elif isinstance(data_payload, str):
            result_text = data_payload[:1000]
        elif data_payload is not None:
            result_text = str(data_payload)[:1000]
        else:
            if not result_text:
                result_text = "[NO TOOL OUTPUT]"

        return {
            "status": "success" if status_ok else "error",
            "result_text": result_text,
            "data": data_payload,
            "meta": meta_payload
        }

    def _compute_backoff(self, attempt: int) -> float:
        base = TASK_RETRY_BACKOFF_BASE ** attempt
        jitter = random.uniform(0, TASK_RETRY_BACKOFF_JITTER)
        return min(base + jitter, 600.0)

    # ----------------------------- Terminal Check --------------------------------------
    def _check_terminal(self, mission: Mission):
        """
        فحص شامل لتحديد إن كانت الـ Mission يمكن أن تُعلن ناجحة أو فاشلة أو تدخل طور التكيّف.
        """
        pending = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.PENDING).count()
        retry = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.RETRY).count()
        running = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.RUNNING).count()
        failed = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.FAILED).count()

        log_debug(
            mission,
            "Terminal check snapshot",
            pending=pending, retry=retry, running=running, failed=failed, status=str(mission.status)
        )

        if pending == 0 and retry == 0 and running == 0:
            if failed == 0:
                if mission.status != MissionStatus.SUCCESS:
                    update_mission_status(mission, MissionStatus.SUCCESS, note="All tasks completed.")
                    increment_counter("overmind_missions_finished_total", {"result": "success"})
                    log_info(mission, "Mission success")
            else:
                if failed >= REPLAN_FAILURE_THRESHOLD and self._adaptive_cycles_used(mission) < ADAPTIVE_MAX_CYCLES:
                    if mission.status != MissionStatus.ADAPTING:
                        update_mission_status(mission, MissionStatus.ADAPTING, note="Entering adaptive replan.")
                        log_info(mission, "Switching to adaptive replanning", failed=failed)
                else:
                    if mission.status != MissionStatus.FAILED:
                        update_mission_status(mission, MissionStatus.FAILED, note=f"{failed} tasks failed.")
                        increment_counter("overmind_missions_finished_total", {"result": "failed"})
                        log_warn(mission, "Mission failed terminally", failed=failed)
            db.session.commit()

    def _has_open_tasks(self, mission: Mission) -> bool:
        """Return True if there are any tasks still actionable."""
        return db.session.query(
            exists().where(
                Task.mission_id == mission.id,
            ).where(
                Task.status.in_([TaskStatus.PENDING, TaskStatus.RETRY, TaskStatus.RUNNING])
            )
        ).scalar()

    def _adaptive_cycles_used(self, mission: Mission) -> int:
        plan_count = MissionPlan.query.filter_by(mission_id=mission.id).count()
        return max(plan_count - 1, 0)

    # ----------------------------- Adaptive Replan -------------------------------------
    def _adaptive_replan(self, mission: Mission):
        failed_tasks = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.FAILED).all()
        if not failed_tasks:
            update_mission_status(mission, MissionStatus.RUNNING, note="No failed tasks; resume.")
            db.session.commit()
            return

        if self._adaptive_cycles_used(mission) >= ADAPTIVE_MAX_CYCLES:
            update_mission_status(mission, MissionStatus.FAILED, note="Adaptive cycle limit reached.")
            db.session.commit()
            log_warn(mission, "Adaptive limit reached; failing mission.")
            return

        failure_context = {t.task_key: (t.error_text or "unknown") for t in failed_tasks}
        log_info(mission, "Adaptive replanning initiated", failed_tasks=len(failed_tasks))
        log_mission_event(
            mission,
            MissionEventType.REPLAN_TRIGGERED,
            payload={"failed_tasks": list(failure_context.keys())}
        )

        planners = get_all_planners()
        chosen = None
        for p in planners:
            caps = getattr(p, "capabilities", set())
            if "llm" in caps:
                chosen = p
                break
        if not chosen and planners:
            chosen = planners[0]

        if not chosen:
            update_mission_status(mission, MissionStatus.FAILED, note="No planner for adaptive replan.")
            db.session.commit()
            return

        try:
            result = chosen.instrumented_generate(mission.objective)
            schema = result.plan
            version = self._next_plan_version(mission.id)
            candidate = CandidatePlan(
                raw=schema,
                planner_name=result.planner_name,
                score=self._score_plan(schema, result.metadata),
                rationale=f"ADAPTIVE: {self._build_plan_rationale(schema, 0, result.metadata)}",
                telemetry={"duration": result.duration_seconds, **result.metadata}
            )
            self._persist_plan(mission, candidate, version)
            update_mission_status(mission, MissionStatus.PLANNED, note=f"Adaptive plan v{version} prepared.")
            db.session.commit()
            log_mission_event(
                mission,
                MissionEventType.REPLAN_APPLIED,
                payload={"version": version, "planner": candidate.planner_name}
            )
            log_info(mission, "Adaptive plan applied", version=version, planner=candidate.planner_name)
        except Exception as e:
            log_error(mission, "Adaptive replanning failed", error=str(e))
            update_mission_status(mission, MissionStatus.FAILED, note=f"Adaptive failed: {e}")
            db.session.commit()

    # ----------------------------- Internal Helpers -----------------------------------
    def _compute_backoff(self, attempt: int) -> float:
        base = TASK_RETRY_BACKOFF_BASE ** attempt
        jitter = random.uniform(0, TASK_RETRY_BACKOFF_JITTER)
        return min(base + jitter, 600.0)

    def _safe_terminal_event(self, mission: Mission):
        """
        استدعاء آمن للفحص النهائي بعد انتهاء تنفيذ مهمة (نجاح/فشل)
        لتقليل زمن بقائها في RUNNING.
        """
        try:
            self._check_terminal(mission)
        except Exception:
            pass

# ======================================================================================
# Singleton Facade
# ======================================================================================
_overmind_service_singleton = OvermindService()

def start_mission(objective: str, initiator: User) -> Mission:
    return _overmind_service_singleton.start_new_mission(objective, initiator)

def run_mission_lifecycle(mission_id: int):
    return _overmind_service_singleton.run_mission_lifecycle(mission_id)

# ======================================================================================
# END OF FILE
# ======================================================================================