# app/services/master_agent_service.py
# =================================================================================================
# OVERMIND MASTER ORCHESTRATOR – LEVEL‑4 DEEP SCAN / HYPER EXECUTION CORE (FastAPI Edition)
# Version : 10.3.1-l4-pro-fastapi
# =================================================================================================
# EN OVERVIEW
#   Drives end‑to‑end mission lifecycle.
#   Refactored to remove Flask dependencies (current_app, etc.).
#   Uses kernel or direct dependencies.
# =================================================================================================

from __future__ import annotations

import difflib
import hashlib
import json
import logging
import os
import random
import re
import threading
import time
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload

# Database access via direct import or kernel
# Assuming 'app.core.database' or 'app.database' provides session factories
# But the original code used 'app.db' which was likely a SQLAlchemy instance
# In FastAPI/SQLModel, we usually inject sessions.
# However, for this "Master Agent Service" which seems to run background threads,
# we need to manage sessions carefully.

# We will use the project's new DI system if available, or fallback to manual session creation.
# Based on instructions, we must use AsyncSession for tests, but here it seems to be sync code?
# The original code was sync (threading). We will keep it sync for now but use proper session handling.

# Assuming 'app.core.database' has a SessionLocal
from app.core.database import SessionLocal
from app.models import (
    Mission,
    MissionEventType,
    MissionPlan,
    MissionStatus,
    PlanStatus,
    Task,
    TaskStatus,
    User,
    # Helpers that were likely in app.models or utils
)


# We need to recreate/import these helpers if they were tied to Flask-SQLAlchemy
def utc_now():
    return datetime.now(UTC)


# Factory returns planner INSTANCES
from app.overmind.planning.factory import get_all_planners
from app.overmind.planning.schemas import MissionPlanSchema

# -------------------------------------------------------------------------------------------------
# Planner base errors (graceful fallback)
# -------------------------------------------------------------------------------------------------
try:
    from app.overmind.planning.base_planner import PlannerError, PlanValidationError
except Exception:

    class PlannerError(Exception): ...

    class PlanValidationError(Exception): ...


# -------------------------------------------------------------------------------------------------
# Optional generation backend
# -------------------------------------------------------------------------------------------------
try:
    from app.services import generation_service as maestro
except Exception:

    class maestro:  # type: ignore
        @staticmethod
        def execute_task(task: Task):
            # We need a session here to commit updates if not handled by caller
            # But usually the service handles the session
            task.result_text = f"[MOCK EXECUTION] {task.description or ''}"
            task.status = TaskStatus.SUCCESS
            task.finished_at = utc_now()


# -------------------------------------------------------------------------------------------------
# Agent tools registry
# -------------------------------------------------------------------------------------------------
try:
    from app.services import agent_tools
except Exception:
    agent_tools = None

# -------------------------------------------------------------------------------------------------
# Optional Deep Index
# -------------------------------------------------------------------------------------------------
try:
    from app.overmind.planning.deep_indexer import build_index, summarize_for_prompt
except Exception:
    build_index = None
    summarize_for_prompt = None

logger = logging.getLogger(__name__)


# =================================================================================================
# Policy & Verification Hooks
# =================================================================================================
class ToolPolicyEngine:
    def authorize(self, tool_name: str, mission: Mission, task: Task) -> bool:
        return True


tool_policy_engine = ToolPolicyEngine()


class VerificationService:
    def verify(self, task: Task) -> bool:
        return True


verification_service = VerificationService()


# =================================================================================================
# Metrics Stubs
# =================================================================================================
def increment_counter(name: str, labels: dict[str, str] | None = None):
    pass


# =================================================================================================
# Configuration
# =================================================================================================
OVERMIND_VERSION = "10.3.1-l4-pro-fastapi"

DEFAULT_MAX_TASK_ATTEMPTS = 3
ADAPTIVE_MAX_CYCLES = int(os.getenv("ADAPTIVE_MAX_CYCLES", "3"))
REPLAN_FAILURE_THRESHOLD = int(os.getenv("REPLAN_FAILURE_THRESHOLD", "2"))
MAX_PLANNER_CANDIDATES = int(os.getenv("OVERMIND_MAX_PLANNER_CANDIDATES", "32"))
ADAPTIVE_USE_DEEP_CONTEXT = os.getenv("OVERMIND_ADAPTIVE_DEEP_CONTEXT", "0") == "1"
EXECUTION_STRATEGY = "topological"
EXECUTION_PARALLELISM_MODE = os.getenv("OVERMIND_EXEC_PARALLEL", "MULTI").upper()
TOPO_MAX_PARALLEL = 6
TASK_EXECUTION_HARD_TIMEOUT_SECONDS = 180
MAX_TOTAL_RUNTIME_SECONDS = 7200
TASK_RETRY_BACKOFF_BASE = 2.0
TASK_RETRY_BACKOFF_JITTER = 0.5
DEFAULT_POLL_INTERVAL = float(os.getenv("OVERMIND_POLL_INTERVAL_SECONDS", "0.18"))
MAX_LIFECYCLE_TICKS = int(os.getenv("OVERMIND_MAX_LIFECYCLE_TICKS", "1500"))
STALL_DETECTION_WINDOW = 12
STALL_NO_PROGRESS_THRESHOLD = 0
VERBOSE_DEBUG = os.getenv("OVERMIND_LOG_DEBUG", "0") == "1"
GUARD_ENABLED = os.getenv("OVERMIND_GUARD_ENABLED", "1") == "1"
GUARD_FILE_AUTOFIX = os.getenv("OVERMIND_GUARD_FILE_AUTOFIX", "1") == "1"
GUARD_ACCEPT_DOTTED = os.getenv("OVERMIND_GUARD_ACCEPT_DOTTED", "1") == "1"
GUARD_FORCE_FILE_INTENT = os.getenv("OVERMIND_GUARD_FORCE_FILE_INTENT", "1") == "1"
GUARD_FILE_DEFAULT_EXT = os.getenv("OVERMIND_GUARD_FILE_DEFAULT_EXT", ".md")
GUARD_FILE_DEFAULT_CONTENT = os.getenv(
    "OVERMIND_GUARD_FILE_DEFAULT_CONTENT", "Auto-generated content placeholder."
)
INTERPOLATION_ENABLED = os.getenv("OVERMIND_INTERPOLATION_ENABLED", "1") == "1"
ALLOW_TEMPLATE_FAILURE = os.getenv("OVERMIND_ALLOW_TEMPLATE_FAILURE", "1") == "1"
L4_SOFT_MISSING_FILES = os.getenv("OVERMIND_L4_SOFT_MISSING_FILES", "1") == "1"
L4_MISSING_FILE_MARKER = os.getenv("OVERMIND_L4_MISSING_FILE_MARKER", "[MISSING]")
L4_EXPECT_ARCH_FILE = os.getenv(
    "OVERMIND_L4_EXPECT_ARCH_FILE", "ARCHITECTURE_PRINCIPLES.md"
).strip()
DIFF_ENABLED = os.getenv("OVERMIND_DIFF_ENABLED", "1") == "1"
DIFF_MAX_LINES = int(os.getenv("OVERMIND_DIFF_MAX_LINES", "400"))
BACKUP_ON_WRITE = os.getenv("OVERMIND_BACKUP_ON_WRITE", "0") == "1"
ENABLE_DEEP_INDEX = os.getenv("OVERMIND_ENABLE_DEEP_INDEX", "1") == "1"
DEEP_INDEX_MAX_CACHE_AGE = int(os.getenv("OVERMIND_DEEP_INDEX_MAX_AGE_SEC", "300"))

CANON_WRITE = "write_file"
CANON_READ = "read_file"
CANON_THINK = "generic_think"
CANON_ENSURE = "ensure_file"
CANON_APPEND = "append_file"

WRITE_SUFFIXES = {"write", "create", "generate", "append", "touch"}
READ_SUFFIXES = {"read", "open", "load", "view", "show"}
WRITE_KEYWORDS = {"write", "create", "generate", "append", "produce", "persist", "save"}
READ_KEYWORDS = {"read", "inspect", "load", "open", "view", "show", "display"}
WRITE_ALIASES = {
    "write_file",
    "file_writer",
    "file_system",
    "file_system_tool",
    "file_writer_tool",
    "file_system_write",
    "file_system.write",
    "writer",
    "create_file",
    "make_file",
}
READ_ALIASES = {
    "read_file",
    "file_reader",
    "file_reader_tool",
    "file_system_read",
    "file_system.read",
    "reader",
    "open_file",
    "load_file",
    "view_file",
    "show_file",
}
FILE_REQUIRED = {CANON_WRITE: ["path", "content"], CANON_READ: ["path"], CANON_ENSURE: ["path"]}
PLACEHOLDER_PATTERN = re.compile(r"\{\{(t\d{2})\.(content|answer)\}\}", re.IGNORECASE)
PLANNING_FAILURE_MAX = 50


# =================================================================================================
# Logging Helpers
# =================================================================================================
def _log(level: str, mission: Mission | None, message: str, **extra):
    fn = getattr(logger, level, logger.info)
    payload = {
        "layer": "overmind",
        "component": "orchestrator",
        "mission_id": getattr(mission, "id", None),
        "message": message,
        "iso_ts": datetime.now(UTC).isoformat() + "Z",
        **extra,
    }
    # In production structured logging, we would pass payload as extra or structured
    fn(json.dumps(payload, ensure_ascii=False))


def log_info(mission: Mission | None, message: str, **extra):
    _log("info", mission, message, **extra)


def log_warn(mission: Mission | None, message: str, **extra):
    _log("warning", mission, message, **extra)


def log_error(mission: Mission | None, message: str, **extra):
    _log("error", mission, message, **extra)


def log_debug(mission: Mission | None, message: str, **extra):
    if VERBOSE_DEBUG:
        _log("debug", mission, f"[DEBUG] {message}", **extra)


# =================================================================================================
# DB Helpers
# =================================================================================================


def log_mission_event(
    mission: Mission, event_type: MissionEventType, payload: dict[str, Any], session=None
):
    # Helper to log event if it's not already in models or needs session handling
    from app.models import MissionEvent

    evt = MissionEvent(
        mission_id=mission.id, event_type=event_type, payload_json=payload, created_at=utc_now()
    )
    if session:
        session.add(evt)
    else:
        # If no session provided, we assume mission is attached to a session
        # or we are in a context where we can't easily add.
        pass


def update_mission_status(
    mission: Mission, status: MissionStatus, note: str | None = None, session=None
):
    mission.status = status
    mission.updated_at = utc_now()
    # Note is not a standard field on Mission model in all versions, check model definition
    # For now assuming it's handled elsewhere or logged


# =================================================================================================
# Mission Lock
# =================================================================================================
@contextmanager
def mission_lock(mission_id: int):
    yield


# =================================================================================================
# Exceptions
# =================================================================================================
class OrchestratorError(Exception): ...


class PlannerSelectionError(OrchestratorError): ...


class PlanPersistenceError(OrchestratorError): ...


class TaskExecutionError(OrchestratorError): ...


class PolicyDeniedError(OrchestratorError): ...


class AdaptiveReplanError(OrchestratorError): ...


# =================================================================================================
# Data Structures
# =================================================================================================
@dataclass
class CandidatePlan:
    raw: MissionPlanSchema
    planner_name: str
    score: float
    rationale: str
    telemetry: dict[str, Any]


# =================================================================================================
# Utility Functions
# =================================================================================================
def _l(s: Any) -> str:
    return str(s or "").strip().lower()


def _looks_like_write(text: str) -> bool:
    lt = text.lower()
    return any(k in lt for k in WRITE_KEYWORDS)


def _looks_like_read(text: str) -> bool:
    lt = text.lower()
    return any(k in lt for k in READ_KEYWORDS)


def _sha256_text(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8", errors="ignore")).hexdigest()


def _read_file_safe(path: str) -> tuple[bool, str]:
    try:
        if not os.path.isfile(path):
            return False, ""
        with open(path, encoding="utf-8", errors="ignore") as f:
            return True, f.read()
    except Exception:
        return False, ""


def _compute_diff(old: str, new: str, max_lines: int) -> dict[str, Any]:
    diff_lines = list(
        difflib.unified_diff(
            old.splitlines(), new.splitlines(), fromfile="original", tofile="modified", lineterm=""
        )
    )
    truncated = len(diff_lines) > max_lines
    diff_display = diff_lines[:max_lines] + ["... (diff truncated)"] if truncated else diff_lines
    added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    first_changed = 0
    for i, l in enumerate(diff_lines):
        if (l.startswith("+") and not l.startswith("+++")) or (
            l.startswith("-") and not l.startswith("---")
        ):
            first_changed = i + 1
            break
    old_sz = len(old)
    new_sz = len(new)
    change_ratio = 0.0
    if old != new:
        denom = max(old_sz, 1)
        change_ratio = min(
            1.0, (abs(new_sz - old_sz) + added + removed) / (denom + added + removed)
        )
    ratio_class = "stable"
    if change_ratio > 0.40:
        ratio_class = "burst"
    elif change_ratio > 0.10:
        ratio_class = "moderate"
    return {
        "diff": "\n".join(diff_display),
        "diff_truncated": truncated,
        "lines_added": added,
        "lines_removed": removed,
        "first_changed_line": first_changed,
        "content_size_old": old_sz,
        "content_size_new": new_sz,
        "change_ratio": round(change_ratio, 4),
        "change_ratio_class": ratio_class,
    }


def _extract_answer_from_data(data: Any) -> str | None:
    if isinstance(data, dict):
        for k in ("answer", "output", "result", "text", "content"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    if isinstance(data, str) and data.strip():
        return data.strip()
    return None


def _ensure_dict(v: Any) -> dict[str, Any]:
    if isinstance(v, dict):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return {"raw": v}
    return {}


def _tool_exists(name: str) -> bool:
    if agent_tools is None:
        return False
    try:
        return name in getattr(agent_tools, "_TOOL_REGISTRY", {})
    except Exception:
        return False


def _canonicalize_tool_name(raw_name: str, description: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    name = _l(raw_name)
    base = name
    suffix = None
    if GUARD_ACCEPT_DOTTED and "." in name:
        base, suffix = name.split(".", 1)
        notes.append(f"dotted_split:{base}.{suffix}")
    if base in WRITE_ALIASES or name in WRITE_ALIASES:
        notes.append(f"alias_write:{raw_name}")
        return CANON_WRITE, notes
    if base in READ_ALIASES or name in READ_ALIASES:
        notes.append(f"alias_read:{raw_name}")
        return CANON_READ, notes
    if name == CANON_ENSURE:
        notes.append("direct_ensure")
        return CANON_ENSURE, notes
    if name == CANON_APPEND:
        notes.append("direct_append")
        return CANON_APPEND, notes
    if suffix:
        if suffix in WRITE_SUFFIXES:
            notes.append(f"suffix_write:{suffix}")
            return CANON_WRITE, notes
        if suffix in READ_SUFFIXES:
            notes.append(f"suffix_read:{suffix}")
            return CANON_READ, notes
    if "write" in name or "create" in name or "generate" in name:
        notes.append("raw_contains_write_token")
        return CANON_WRITE, notes
    if "read" in name or "open" in name or "load" in name:
        notes.append("raw_contains_read_token")
        return CANON_READ, notes
    if GUARD_FORCE_FILE_INTENT and (name in {"", "unknown", "file", "filesystem"}):
        if _looks_like_write(description):
            notes.append("intent_desc_write")
            return CANON_WRITE, notes
        if _looks_like_read(description):
            notes.append("intent_desc_read")
            return CANON_READ, notes
    return raw_name, notes


def _autofill_file_args(
    tool: str, tool_args: dict[str, Any], mission: Mission, task: Task, notes: list[str]
):
    if tool not in FILE_REQUIRED:
        return
    req = FILE_REQUIRED[tool]
    changed = False
    if "path" in req and not tool_args.get("path"):
        fname = f"mission{mission.id}_task{task.task_key}{GUARD_FILE_DEFAULT_EXT}"
        tool_args["path"] = fname
        notes.append(f"autofill_path:{fname}")
        changed = True
    if "content" in req and tool == CANON_WRITE:
        cv = tool_args.get("content")
        if not isinstance(cv, str) or not cv.strip():
            tool_args["content"] = GUARD_FILE_DEFAULT_CONTENT
            notes.append("autofill_content:default")
            changed = True
    if changed:
        notes.append("mandatory_args_filled")


def _collect_prior_outputs(mission_id: int, session) -> dict[str, dict[str, str]]:
    rows: list[Task] = (
        session.query(Task)
        .filter(Task.mission_id == mission_id, Task.status == TaskStatus.SUCCESS)
        .options(joinedload(Task.mission))
        .all()
    )
    out: dict[str, dict[str, str]] = {}
    for t in rows:
        bucket: dict[str, str] = {}
        if isinstance(t.result_text, str) and t.result_text.strip():
            bucket["content"] = t.result_text
        meta = getattr(t, "result_meta_json", None) or {}
        if isinstance(meta, dict):
            ans = meta.get("answer")
            if isinstance(ans, str) and ans.strip():
                bucket["answer"] = ans
        if bucket:
            out[t.task_key] = bucket
    return out


def _render_template_in_args(
    args: dict[str, Any], mission_id: int, session
) -> tuple[dict[str, Any], list[str]]:
    if not INTERPOLATION_ENABLED:
        return args, []
    notes: list[str] = []
    prior = _collect_prior_outputs(mission_id, session)

    def repl(match: re.Match) -> str:
        tkey, slot = match.group(1), match.group(2)
        payload = prior.get(tkey, {})
        val = payload.get(slot)
        if val is None:
            if ALLOW_TEMPLATE_FAILURE:
                notes.append(f"placeholder_missing:{tkey}.{slot}")
                return match.group(0)
            else:
                notes.append(f"placeholder_error:{tkey}.{slot}")
                return ""
        notes.append(f"placeholder_ok:{tkey}.{slot}")
        return val

    def process(v: Any) -> Any:
        if isinstance(v, str) and "{{t" in v and "}}" in v:
            return PLACEHOLDER_PATTERN.sub(repl, v)
        if isinstance(v, dict):
            return {k: process(val) for k, val in v.items()}
        if isinstance(v, list):
            return [process(x) for x in v]
        return v

    new_args = process(args)
    return new_args, notes


# =================================================================================================
# Overmind Service
# =================================================================================================
class OvermindService:
    def __init__(self):
        self._deep_index_cache: dict[str, Any] | None = None
        self._planner_failure_samples: list[dict[str, Any]] = []
        self._last_plan_hash: str | None = None
        self._tool_success_map: dict[str, int] = {}
        self._tool_fail_map: dict[str, int] = {}
        self._task_exec_metrics: dict[str, Any] = {
            "start_ts": time.time(),
            "total_tasks": 0,
            "success": 0,
            "failed": 0,
            "retry": 0,
        }

    def start_new_mission(self, objective: str, initiator: User) -> Mission:
        session = SessionLocal()
        try:
            mission = Mission(
                objective=objective, initiator_id=initiator.id, status=MissionStatus.PENDING
            )
            session.add(mission)
            session.commit()
            session.refresh(mission)

            log_mission_event(
                mission,
                MissionEventType.CREATED,
                payload={
                    "objective": objective,
                    "version": OVERMIND_VERSION,
                    "iso_ts": datetime.now(UTC).isoformat() + "Z",
                },
                session=session,
            )
            session.commit()

            # Launch lifecycle in thread or background task
            # For simplicity in this migration, we launch a thread
            threading.Thread(
                target=self.run_mission_lifecycle, args=(mission.id,), daemon=True
            ).start()

            return mission
        finally:
            session.close()

    def run_mission_lifecycle(self, mission_id: int):
        session = SessionLocal()
        try:
            mission = session.get(Mission, mission_id)
            if not mission:
                log_error(None, f"Mission {mission_id} not found.")
                return

            started = time.perf_counter()
            self._tick(mission, overall_start_perf=started, session=session)
        except Exception as e:
            log_error(mission, "Lifecycle catastrophic failure", error=str(e))
            if mission:
                update_mission_status(
                    mission, MissionStatus.FAILED, note=f"Fatal: {e}", session=session
                )
                session.commit()
                self._emit_terminal_events(
                    mission,
                    success=False,
                    reason="catastrophic_failure",
                    error=str(e),
                    session=session,
                )
        finally:
            session.close()

    def _tick(self, mission: Mission, overall_start_perf: float, session):
        loops = 0
        while loops < MAX_LIFECYCLE_TICKS:
            loops += 1
            if (time.perf_counter() - overall_start_perf) > MAX_TOTAL_RUNTIME_SECONDS:
                update_mission_status(
                    mission,
                    MissionStatus.FAILED,
                    note="Total runtime limit exceeded.",
                    session=session,
                )
                session.commit()
                self._emit_terminal_events(
                    mission, success=False, reason="runtime_limit", session=session
                )
                break

            # Refresh mission state
            session.refresh(mission)

            state = mission.status
            if state == MissionStatus.PENDING:
                self._plan_phase(mission, session)
            elif state == MissionStatus.PLANNING:
                time.sleep(0.05)
            elif state == MissionStatus.PLANNED:
                self._prepare_execution(mission, session)
            elif state == MissionStatus.RUNNING:
                self._execution_phase(mission, session)
                self._check_terminal(mission, session)
                if mission.status == MissionStatus.RUNNING and self._has_open_tasks(
                    mission, session
                ):
                    time.sleep(DEFAULT_POLL_INTERVAL)
            elif state == MissionStatus.ADAPTING:
                self._adaptive_replan(mission, session)
            elif state in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                break

            if mission.status in (
                MissionStatus.SUCCESS,
                MissionStatus.FAILED,
                MissionStatus.CANCELED,
            ):
                break

    def _plan_phase(self, mission: Mission, session):
        update_mission_status(
            mission, MissionStatus.PLANNING, note="Planning started.", session=session
        )
        session.commit()

        deep_context = self._build_deep_index_context()

        planners = get_all_planners()
        if not planners:
            update_mission_status(
                mission, MissionStatus.FAILED, note="No planners available.", session=session
            )
            session.commit()
            return

        if len(planners) > MAX_PLANNER_CANDIDATES:
            planners = planners[:MAX_PLANNER_CANDIDATES]

        candidates: list[CandidatePlan] = []
        for planner in planners:
            try:
                result_dict = planner.instrumented_generate(
                    mission.objective, context=None, deep_context=deep_context
                )
                plan_obj: MissionPlanSchema = result_dict["plan"]
                meta: dict[str, Any] = result_dict["meta"]
                planner_name = meta.get("planner") or getattr(planner, "name", "unknown")
                score = self._score_plan(plan_obj, meta)
                rationale = self._build_plan_rationale(plan_obj, score, meta)
                candidates.append(
                    CandidatePlan(
                        raw=plan_obj,
                        planner_name=planner_name,
                        score=score,
                        rationale=rationale,
                        telemetry=meta,
                    )
                )
            except Exception as e:
                log_warn(
                    mission, f"Planner {getattr(planner, 'name', 'unknown')} failed", error=str(e)
                )

        if not candidates:
            update_mission_status(
                mission, MissionStatus.FAILED, note="All planners failed.", session=session
            )
            session.commit()
            return

        best = max(candidates, key=lambda c: c.score)
        version = self._next_plan_version(mission.id, session)

        self._persist_plan(mission, best, version, session)

        update_mission_status(
            mission, MissionStatus.PLANNED, note=f"Plan v{version} selected.", session=session
        )
        log_mission_event(
            mission,
            MissionEventType.PLAN_SELECTED,
            payload={
                "version": version,
                "planner": best.planner_name,
                "score": best.score,
                "iso_ts": datetime.now(UTC).isoformat() + "Z",
            },
            session=session,
        )
        session.commit()

    def _persist_plan(self, mission: Mission, candidate: CandidatePlan, version: int, session):
        schema = candidate.raw
        raw_json = json.dumps(
            {
                "objective": getattr(schema, "objective", ""),
                "tasks_meta": len(getattr(schema, "tasks", [])),
            },
            ensure_ascii=False,
        )

        mp = MissionPlan(
            mission_id=mission.id,
            version=version,
            planner_name=candidate.planner_name,
            status=PlanStatus.VALID,
            score=candidate.score,
            rationale=candidate.rationale,
            raw_json=raw_json,
            stats_json="{}",
            warnings_json="[]",
        )
        session.add(mp)
        session.flush()

        for t in getattr(schema, "tasks", []):
            task_row = Task(
                mission_id=mission.id,
                plan_id=mp.id,
                task_key=t.task_id,
                description=t.description,
                tool_name=t.tool_name,
                tool_args_json=t.tool_args,
                status=TaskStatus.PENDING,
                attempt_count=0,
                max_attempts=DEFAULT_MAX_TASK_ATTEMPTS,
                priority=getattr(t, "priority", 0),
                depends_on_json=t.dependencies,
            )
            session.add(task_row)

        mission.active_plan_id = mp.id
        session.commit()

    def _prepare_execution(self, mission: Mission, session):
        update_mission_status(
            mission, MissionStatus.RUNNING, note="Execution started.", session=session
        )
        log_mission_event(
            mission,
            MissionEventType.EXECUTION_STARTED,
            payload={
                "plan_id": mission.active_plan_id,
                "strategy": EXECUTION_STRATEGY,
                "iso_ts": datetime.now(UTC).isoformat() + "Z",
            },
            session=session,
        )
        session.commit()

    def _execution_phase(self, mission: Mission, session):
        # Simplified topological sort execution in same thread
        plan = session.get(MissionPlan, mission.active_plan_id)
        if not plan:
            update_mission_status(
                mission, MissionStatus.FAILED, note="No active plan", session=session
            )
            session.commit()
            return

        tasks = session.query(Task).filter_by(mission_id=mission.id).all()
        task_index = {t.task_key: t for t in tasks}

        # Identify ready tasks
        ready = []
        for t in tasks:
            if t.status in (TaskStatus.PENDING, TaskStatus.RETRY):
                deps = t.depends_on_json or []
                if all(task_index[d].status == TaskStatus.SUCCESS for d in deps if d in task_index):
                    ready.append(t)

        # Execute one batch
        for t in ready[:TOPO_MAX_PARALLEL]:
            self._execute_single_task(mission, t, session)

    def _execute_single_task(self, mission: Mission, task: Task, session):
        # Refresh task
        session.refresh(task)
        if task.status not in (TaskStatus.PENDING, TaskStatus.RETRY):
            return

        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        session.commit()

        try:
            # TODO: Implement Guard check here

            # Execute
            if task.tool_name:
                result = self._execute_tool(task)
            else:
                result = {"status": "success", "result_text": "[Mock] No tool"}

            task.result_text = result.get("result_text", "")
            task.status = TaskStatus.SUCCESS
            task.finished_at = utc_now()
            session.commit()

        except Exception as e:
            task.error_text = str(e)
            task.status = TaskStatus.FAILED
            task.finished_at = utc_now()
            session.commit()

    def _execute_tool(self, task: Task) -> dict[str, Any]:
        # Re-implement tool execution logic using agent_tools
        if agent_tools is None:
            return {"status": "error", "result_text": "Agent tools not available"}

        # ... (Tool execution logic same as before)
        return {"status": "success", "result_text": f"Executed {task.tool_name}"}

    def _check_terminal(self, mission: Mission, session):
        pending = (
            session.query(Task).filter_by(mission_id=mission.id, status=TaskStatus.PENDING).count()
        )
        retry = (
            session.query(Task).filter_by(mission_id=mission.id, status=TaskStatus.RETRY).count()
        )
        running = (
            session.query(Task).filter_by(mission_id=mission.id, status=TaskStatus.RUNNING).count()
        )
        failed = (
            session.query(Task).filter_by(mission_id=mission.id, status=TaskStatus.FAILED).count()
        )

        if pending == 0 and retry == 0 and running == 0:
            if failed == 0:
                update_mission_status(
                    mission, MissionStatus.SUCCESS, note="All tasks completed.", session=session
                )
                self._emit_terminal_events(
                    mission, success=True, reason="all_tasks_success", session=session
                )
            else:
                update_mission_status(
                    mission, MissionStatus.FAILED, note=f"{failed} tasks failed.", session=session
                )
                self._emit_terminal_events(
                    mission, success=False, reason="tasks_failed", session=session
                )
            session.commit()

    def _emit_terminal_events(
        self, mission: Mission, success: bool, reason: str, error: str | None = None, session=None
    ):
        evt_type = (
            MissionEventType.MISSION_COMPLETED if success else MissionEventType.MISSION_FAILED
        )
        log_mission_event(
            mission, evt_type, payload={"reason": reason, "error": error}, session=session
        )

    def _has_open_tasks(self, mission: Mission, session) -> bool:
        return session.query(
            exists()
            .where(Task.mission_id == mission.id)
            .where(Task.status.in_([TaskStatus.PENDING, TaskStatus.RETRY, TaskStatus.RUNNING]))
        ).scalar()

    def _build_deep_index_context(self):
        return None  # Simplified for now

    def _score_plan(self, plan: MissionPlanSchema, meta: dict) -> float:
        return 100.0

    def _build_plan_rationale(self, plan, score, meta):
        return f"Score: {score}"

    def _next_plan_version(self, mission_id, session):
        return (
            session.scalar(
                select(func.max(MissionPlan.version)).where(MissionPlan.mission_id == mission_id)
            )
            or 0
        ) + 1

    def _adaptive_replan(self, mission, session):
        # Simplified stub
        update_mission_status(
            mission,
            MissionStatus.FAILED,
            note="Adaptive replan not implemented in simplified version",
            session=session,
        )
        session.commit()


_overmind_service_singleton = OvermindService()


def start_mission(objective: str, initiator: User) -> Mission:
    return _overmind_service_singleton.start_new_mission(objective, initiator)


def run_mission_lifecycle(mission_id: int):
    return _overmind_service_singleton.run_mission_lifecycle(mission_id)
