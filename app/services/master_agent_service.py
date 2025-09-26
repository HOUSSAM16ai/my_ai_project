# app/services/master_agent_service.py
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# =================================================================================================
# OVERMIND MASTER ORCHESTRATOR – LEVEL‑4 DEEP SCAN / HYPER EXECUTION CORE
# Version : 10.3.0-l4-pro
# Codename: "AURORA HYPERFLOW PRIME / STRUCTURAL-BOOST / SAFE-ADAPT / TELEMETRY-LITE"
# Status  : Production / Hardened / Deterministic + Adaptive / Observability Enhanced
# Author  : System Orchestrator (Hyper Refined Edition)
# =================================================================================================
# EN OVERVIEW
#   Drives end‑to‑end mission lifecycle:
#     1. Mission creation (natural language objective → persisted Mission).
#     2. Multi-planner candidate generation & deterministic scoring.
#     3. Guarded, canonicalized task execution (tool normalization, autofill, interpolation).
#     4. Optional structural diff augmentation for write_file tasks (bounded).
#     5. Structural index (deep_context) injection for planner signal boosting.
#     6. Stall detection windows + bounded runtime termination.
#     7. Adaptive replanning with controlled cycles & hash convergence guard.
#     8. Semantic event emission (CREATED, PLAN_SELECTED, EXECUTION_STARTED, TASK_*,
#        RISK_SUMMARY, ARCHITECTURE_CLASSIFIED, REPLAN_TRIGGERED, REPLAN_APPLIED,
#        MISSION_COMPLETED, MISSION_FAILED, FINALIZED).
#     9. Light telemetry: execution timing, planner failures, tool success map.
#
# AR OVERVIEW (ملخص عربي)
#   ينفّذ دورة حياة المهمة كاملة:
#     - إنشاء مهمة من هدف نصي.
#     - إنتاج واختيار خطة عبر عدة مخططين.
#     - تنفيذ مهام بأدوات مؤمنة (تطبيع + تعبئة + استبدال قوالب).
#     - دعم فهرس بنيوي عميق اختياري لرفع دقة الاختيار.
#     - إعادة تخطيط تكيفية مضبوطة بعد الإخفاق.
#     - بث أحداث دلالية كاملة وتحليلات خفيفة.
#
# NEW vs 10.2.x
#   + Proper deep_context passing (carried forward).
#   + MAX_PLANNER_CANDIDATES limit (env: OVERMIND_MAX_PLANNER_CANDIDATES).
#   + Safe commit / refresh helpers (_safe_commit / _safe_refresh).
#   + Planner failure ring buffer (bounded).
#   + Tool success metrics aggregation.
#   + Adaptive convergence guard (plan content hash check).
#   + Optional reuse of deep_context in adaptive replan (OVERMIND_ADAPTIVE_DEEP_CONTEXT=1).
#   + Enhanced diff augmentation (ratio_class).
#   + iso_ts on selected logs & events.
#   + Docstrings for public APIs.
#
# SAFETY & CONTRACTS
#   - No DB schema changes.
#   - All terminal endings produce FINALIZED event.
#   - Features degrade gracefully if deep index or diff is unavailable.
#
# EXTENSIBILITY
#   - ToolPolicyEngine.authorize(...) for RBAC / quotas.
#   - VerificationService.verify(...) for domain validation.
#   - _augment_with_diff(...) future richer semantic/AST diff.
#   - _build_deep_index_context(...) future embeddings / advanced scoring.
# =================================================================================================

from __future__ import annotations

import difflib
import hashlib
import json
import os
import random
import re
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Any, Dict, List, Optional, Tuple, Callable, Union

from flask import current_app, has_app_context
from sqlalchemy import select, func, exists
from sqlalchemy.orm import joinedload

from app import db
from app.models import (
    User,
    Mission, MissionPlan, Task,
    MissionStatus, TaskStatus, PlanStatus,
    MissionEventType,
    log_mission_event,
    update_mission_status,
    utc_now
)

# Factory returns planner INSTANCES (legacy shim updated there)
from app.overmind.planning.factory import get_all_planners
from app.overmind.planning.schemas import MissionPlanSchema

# -------------------------------------------------------------------------------------------------
# Planner base errors (graceful fallback)
# -------------------------------------------------------------------------------------------------
try:
    from app.overmind.planning.base_planner import PlannerError, PlanValidationError  # type: ignore
except Exception:  # pragma: no cover
    class PlannerError(Exception): ...
    class PlanValidationError(Exception): ...

# -------------------------------------------------------------------------------------------------
# Optional generation backend
# -------------------------------------------------------------------------------------------------
try:
    from app.services import generation_service as maestro
except Exception:  # pragma: no cover
    class maestro:  # type: ignore
        @staticmethod
        def execute_task(task: Task):
            task.result_text = f"[MOCK EXECUTION] {task.description or ''}"
            task.status = TaskStatus.SUCCESS
            task.finished_at = utc_now()
            db.session.commit()

# -------------------------------------------------------------------------------------------------
# Agent tools registry
# -------------------------------------------------------------------------------------------------
try:
    from app.services import agent_tools
except Exception:  # pragma: no cover
    agent_tools = None  # type: ignore

# -------------------------------------------------------------------------------------------------
# Optional Deep Index
# -------------------------------------------------------------------------------------------------
try:
    from app.overmind.planning.deep_indexer import build_index, summarize_for_prompt
except Exception:  # pragma: no cover
    build_index = None
    summarize_for_prompt = None

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
# Metrics Stubs (integrate externally later)
# =================================================================================================
def increment_counter(name: str, labels: Dict[str, str] | None = None):  # pragma: no cover
    pass
def observe_histogram(name: str, value: float, labels: Dict[str, str] | None = None):  # pragma: no cover
    pass
def set_gauge(name: str, value: float, labels: Dict[str, str] | None = None):  # pragma: no cover
    pass

# =================================================================================================
# Configuration
# =================================================================================================
OVERMIND_VERSION = "10.3.0-l4-pro"

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

# Guard & Hardening
GUARD_ENABLED = os.getenv("OVERMIND_GUARD_ENABLED", "1") == "1"
GUARD_FILE_AUTOFIX = os.getenv("OVERMIND_GUARD_FILE_AUTOFIX", "1") == "1"
GUARD_ACCEPT_DOTTED = os.getenv("OVERMIND_GUARD_ACCEPT_DOTTED", "1") == "1"
GUARD_FORCE_FILE_INTENT = os.getenv("OVERMIND_GUARD_FORCE_FILE_INTENT", "1") == "1"
GUARD_FILE_DEFAULT_EXT = os.getenv("OVERMIND_GUARD_FILE_DEFAULT_EXT", ".md")
GUARD_FILE_DEFAULT_CONTENT = os.getenv("OVERMIND_GUARD_FILE_DEFAULT_CONTENT",
                                       "Auto-generated content placeholder.")
INTERPOLATION_ENABLED = os.getenv("OVERMIND_INTERPOLATION_ENABLED", "1") == "1"
ALLOW_TEMPLATE_FAILURE = os.getenv("OVERMIND_ALLOW_TEMPLATE_FAILURE", "1") == "1"

# Level‑4 Soft Missing Files
L4_SOFT_MISSING_FILES = os.getenv("OVERMIND_L4_SOFT_MISSING_FILES", "1") == "1"
L4_MISSING_FILE_MARKER = os.getenv("OVERMIND_L4_MISSING_FILE_MARKER", "[MISSING]")
L4_EXPECT_ARCH_FILE = os.getenv("OVERMIND_L4_EXPECT_ARCH_FILE", "ARCHITECTURE_PRINCIPLES.md").strip()

# Diff
DIFF_ENABLED = os.getenv("OVERMIND_DIFF_ENABLED", "1") == "1"
DIFF_MAX_LINES = int(os.getenv("OVERMIND_DIFF_MAX_LINES", "400"))
BACKUP_ON_WRITE = os.getenv("OVERMIND_BACKUP_ON_WRITE", "0") == "1"

# Deep Index
ENABLE_DEEP_INDEX = os.getenv("OVERMIND_ENABLE_DEEP_INDEX", "1") == "1"
DEEP_INDEX_MAX_CACHE_AGE = int(os.getenv("OVERMIND_DEEP_INDEX_MAX_AGE_SEC", "300"))

# Canonical tool names
CANON_WRITE = "write_file"
CANON_READ = "read_file"
CANON_THINK = "generic_think"
CANON_ENSURE = "ensure_file"
CANON_APPEND = "append_file"

# Heuristics / Aliases
WRITE_SUFFIXES = {"write", "create", "generate", "append", "touch"}
READ_SUFFIXES = {"read", "open", "load", "view", "show"}
WRITE_KEYWORDS = {"write", "create", "generate", "append", "produce", "persist", "save"}
READ_KEYWORDS = {"read", "inspect", "load", "open", "view", "show", "display"}
WRITE_ALIASES = {
    "write_file", "file_writer", "file_system", "file_system_tool",
    "file_writer_tool", "file_system_write", "file_system.write",
    "writer", "create_file", "make_file"
}
READ_ALIASES = {
    "read_file", "file_reader", "file_reader_tool",
    "file_system_read", "file_system.read", "reader",
    "open_file", "load_file", "view_file", "show_file"
}
FILE_REQUIRED = {
    CANON_WRITE: ["path", "content"],
    CANON_READ: ["path"],
    CANON_ENSURE: ["path"]
}
PLACEHOLDER_PATTERN = re.compile(r"\{\{(t\d{2})\.(content|answer)\}\}", re.IGNORECASE)

# Limits
PLANNING_FAILURE_MAX = 50

# =================================================================================================
# Logging Helpers
# =================================================================================================
def _emit(level: str, line: str):
    if has_app_context():
        logger = current_app.logger
        fn = getattr(logger, {"info": "info", "warn": "warning",
                              "error": "error", "debug": "debug"}[level], logger.info)
        fn(line)
    else:
        print(f"[Overmind:{level}] {line}")

def _log(level: str, mission: Mission | None, message: str, **extra):
    payload = {
        "layer": "overmind",
        "component": "orchestrator",
        "mission_id": getattr(mission, "id", None),
        "message": message,
        "iso_ts": datetime.utcnow().isoformat() + "Z",
        **extra
    }
    _emit(level, json.dumps(payload, ensure_ascii=False))

def log_info(mission: Mission | None, message: str, **extra): _log("info", mission, message, **extra)
def log_warn(mission: Mission | None, message: str, **extra): _log("warn", mission, message, **extra)
def log_error(mission: Mission | None, message: str, **extra): _log("error", mission, message, **extra)
def log_debug(mission: Mission | None, message: str, **extra):
    if VERBOSE_DEBUG:
        _log("debug", mission, f"[DEBUG] {message}", **extra)

# =================================================================================================
# Mission Lock (placeholder)
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
    telemetry: Dict[str, Any]

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

def _read_file_safe(path: str) -> Tuple[bool, str]:
    try:
        if not os.path.isfile(path):
            return False, ""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return True, f.read()
    except Exception:
        return False, ""

def _compute_diff(old: str, new: str, max_lines: int) -> Dict[str, Any]:
    diff_lines = list(difflib.unified_diff(
        old.splitlines(), new.splitlines(),
        fromfile="original", tofile="modified", lineterm=""
    ))
    truncated = len(diff_lines) > max_lines
    if truncated:
        diff_display = diff_lines[:max_lines] + ["... (diff truncated)"]
    else:
        diff_display = diff_lines
    added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    first_changed = 0
    for i, l in enumerate(diff_lines):
        if (l.startswith("+") and not l.startswith("+++")) or (l.startswith("-") and not l.startswith("---")):
            first_changed = i + 1
            break
    old_sz = len(old)
    new_sz = len(new)
    change_ratio = 0.0
    if old != new:
        denom = max(old_sz, 1)
        change_ratio = min(1.0, (abs(new_sz - old_sz) + added + removed) / (denom + added + removed))
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
        "change_ratio_class": ratio_class
    }

def _extract_answer_from_data(data: Any) -> Optional[str]:
    if isinstance(data, dict):
        for k in ("answer", "output", "result", "text", "content"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    if isinstance(data, str) and data.strip():
        return data.strip()
    return None

def _ensure_dict(v: Any) -> Dict[str, Any]:
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

# Canonicalization -----------------------------------------------------------
def _canonicalize_tool_name(raw_name: str, description: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
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

def _autofill_file_args(tool: str, tool_args: Dict[str, Any], mission: Mission, task: Task, notes: List[str]):
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

# Interpolation --------------------------------------------------------------
def _collect_prior_outputs(mission_id: int) -> Dict[str, Dict[str, str]]:
    rows: List[Task] = db.session.query(Task).filter(
        Task.mission_id == mission_id,
        Task.status == TaskStatus.SUCCESS
    ).options(joinedload(Task.mission)).all()
    out: Dict[str, Dict[str, str]] = {}
    for t in rows:
        bucket: Dict[str, str] = {}
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

def _render_template_in_args(args: Dict[str, Any], mission_id: int) -> Tuple[Dict[str, Any], List[str]]:
    if not INTERPOLATION_ENABLED:
        return args, []
    notes: List[str] = []
    prior = _collect_prior_outputs(mission_id)

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
    """
    Mission orchestration:
      - Planning (multi-planner selection + structural context).
      - Guarded topological execution.
      - Adaptive replanning with convergence guard.
      - Emission of semantic & risk events.
    """

    def __init__(self):
        self._app_ref = None
        self._deep_index_cache: Optional[Dict[str, Any]] = None  # {sig, ts, context}
        self._planner_failure_samples: List[Dict[str, Any]] = []
        self._last_plan_hash: Optional[str] = None
        self._tool_success_map: Dict[str, int] = {}
        self._tool_fail_map: Dict[str, int] = {}
        self._task_exec_metrics: Dict[str, Any] = {
            "start_ts": time.time(),
            "total_tasks": 0,
            "success": 0,
            "failed": 0,
            "retry": 0
        }

    # ------------------------------ Public API --------------------------------
    def start_new_mission(self, objective: str, initiator: User) -> Mission:
        """Create a mission and run lifecycle immediately."""
        self._ensure_app_ref()
        mission = Mission(objective=objective, initiator=initiator, status=MissionStatus.PENDING)
        db.session.add(mission)
        self._safe_commit("mission_create")
        log_mission_event(mission, MissionEventType.CREATED,
                          payload={"objective": objective,
                                   "version": OVERMIND_VERSION,
                                   "iso_ts": datetime.utcnow().isoformat() + "Z"})
        self._safe_commit("mission_created_event")
        log_info(mission, "Mission created; starting lifecycle", objective=objective)
        self.run_mission_lifecycle(mission.id)
        return mission

    def run_mission_lifecycle(self, mission_id: int):
        """Drive mission through states until terminal."""
        self._ensure_app_ref()
        mission = Mission.query.options(joinedload(Mission.tasks)).get(mission_id)
        if not mission:
            log_error(None, f"Mission {mission_id} not found.")
            return
        started = time.perf_counter()
        with mission_lock(mission.id):
            try:
                self._tick(mission, overall_start_perf=started)
            except Exception as e:
                log_error(mission, "Lifecycle catastrophic failure", error=str(e))
                update_mission_status(mission, MissionStatus.FAILED, note=f"Fatal: {e}")
                self._safe_commit("catastrophic_fail")
                self._emit_terminal_events(mission, success=False,
                                           reason="catastrophic_failure", error=str(e))

    # ------------------------------ Internal Helpers --------------------------
    def _safe_commit(self, tag: str):
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            log_warn(None, "Commit failed; rolled back", tag=tag, error=str(e))

    def _safe_refresh(self, obj: Any, tag: str):
        try:
            db.session.refresh(obj)
        except Exception:
            db.session.rollback()
            log_debug(None, f"Refresh failed ({tag})")

    # ------------------------------ Core Loop ---------------------------------
    def _tick(self, mission: Mission, overall_start_perf: float):
        loops = 0
        while loops < MAX_LIFECYCLE_TICKS:
            loops += 1
            if (time.perf_counter() - overall_start_perf) > MAX_TOTAL_RUNTIME_SECONDS:
                update_mission_status(mission, MissionStatus.FAILED, note="Total runtime limit exceeded.")
                self._safe_commit("runtime_limit")
                log_warn(mission, "Mission aborted by total runtime limit.")
                self._emit_terminal_events(mission, success=False, reason="runtime_limit")
                break

            log_debug(mission, "Lifecycle tick", loop=loops, status=str(mission.status))

            state = mission.status
            if state == MissionStatus.PENDING:
                self._plan_phase(mission)
            elif state == MissionStatus.PLANNING:
                time.sleep(0.05)
            elif state == MissionStatus.PLANNED:
                self._prepare_execution(mission)
            elif state == MissionStatus.RUNNING:
                if EXECUTION_STRATEGY == "topological":
                    self._execution_phase(mission)
                else:
                    self._execution_wave_legacy(mission)
                self._check_terminal(mission)
                if mission.status == MissionStatus.RUNNING and self._has_open_tasks(mission):
                    time.sleep(DEFAULT_POLL_INTERVAL)
            elif state == MissionStatus.ADAPTING:
                self._adaptive_replan(mission)
            elif state in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                log_debug(mission, "Terminal state reached; exiting.")
                break

            self._safe_refresh(mission, "post_tick_refresh")

            if mission.status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                break

            if mission.status == MissionStatus.RUNNING and not self._has_open_tasks(mission):
                self._check_terminal(mission)
                self._safe_refresh(mission, "post_terminal_check")
                if mission.status in (MissionStatus.SUCCESS, MissionStatus.FAILED):
                    break
                time.sleep(0.05)
        else:
            if mission.status == MissionStatus.RUNNING:
                log_warn(mission, "Lifecycle tick limit reached while RUNNING.")
                self._check_terminal(mission)
                self._safe_commit("tick_limit")

    # ------------------------------ Planning Phase ----------------------------
    def _plan_phase(self, mission: Mission):
        update_mission_status(mission, MissionStatus.PLANNING, note="Planning started.")
        self._safe_commit("enter_planning")
        log_info(mission, "Planning phase started.")

        deep_context = self._build_deep_index_context()
        if deep_context:
            log_info(mission, "Deep index context ready",
                     files=deep_context["files_scanned"],
                     hotspots=deep_context["hotspots_count"],
                     layers=len(deep_context["layers"]),
                     build_ms=deep_context["build_ms"])
            try:
                log_mission_event(
                    mission,
                    MissionEventType.ARCHITECTURE_CLASSIFIED,
                    payload={
                        "index_version": deep_context["index_version"],
                        "files_scanned": deep_context["files_scanned"],
                        "hotspots": deep_context["hotspots_count"],
                        "layers_detected": len(deep_context["layers"]),
                        "build_ms": deep_context["build_ms"],
                        "iso_ts": datetime.utcnow().isoformat() + "Z"
                    }
                )
                self._safe_commit("arch_classified")
            except Exception:
                pass
        else:
            log_debug(mission, "Deep index context skipped or unavailable.")

        planners = get_all_planners()
        if not planners:
            update_mission_status(mission, MissionStatus.FAILED, note="No planners available.")
            self._safe_commit("no_planners")
            self._emit_terminal_events(mission, success=False, reason="no_planners")
            return

        # Limit candidate planners if too many
        if len(planners) > MAX_PLANNER_CANDIDATES:
            planners = planners[:MAX_PLANNER_CANDIDATES]

        candidates: List[CandidatePlan] = []
        for planner in planners:
            pname = getattr(planner, "name", "unknown")
            try:
                result_dict = planner.instrumented_generate(
                    mission.objective,
                    context=None,
                    deep_context=deep_context
                )
                if (not isinstance(result_dict, dict)
                        or "plan" not in result_dict
                        or "meta" not in result_dict):
                    raise PlannerError("instrumented_generate invalid structure",
                                       pname, mission.objective)  # type: ignore

                plan_obj: MissionPlanSchema = result_dict["plan"]
                meta: Dict[str, Any] = result_dict["meta"]
                planner_name = meta.get("planner") or pname
                score = self._score_plan(plan_obj, meta)
                rationale = self._build_plan_rationale(plan_obj, score, meta)
                candidates.append(CandidatePlan(
                    raw=plan_obj,
                    planner_name=planner_name,
                    score=score,
                    rationale=rationale,
                    telemetry={"duration_ms": meta.get("duration_ms"),
                               "node_count": meta.get("node_count"), **meta}
                ))
                log_info(mission, "Planner candidate",
                         planner=planner_name,
                         score=score,
                         duration_ms=meta.get("duration_ms"),
                         node_count=meta.get("node_count"))
            except Exception as e:
                sample = {"planner": pname, "error": str(e)[:160], "ts": time.time()}
                self._planner_failure_samples.append(sample)
                if len(self._planner_failure_samples) > PLANNING_FAILURE_MAX:
                    self._planner_failure_samples = self._planner_failure_samples[-PLANNING_FAILURE_MAX:]
                log_warn(mission, "Planner failed",
                         planner=pname, error=str(e))

        if not candidates:
            update_mission_status(mission, MissionStatus.FAILED, note="All planners failed.")
            self._safe_commit("all_planners_failed")
            self._emit_terminal_events(mission, success=False, reason="all_planners_failed")
            return

        best = max(candidates, key=lambda c: c.score)
        version = self._next_plan_version(mission.id)

        # Convergence guard (hash)
        new_hash = self._hash_plan(best.raw)
        if self._last_plan_hash and self._last_plan_hash == new_hash:
            log_warn(mission, "Convergence guard triggered: identical plan hash",
                     version=version, hash=new_hash)
        self._last_plan_hash = new_hash

        try:
            self._persist_plan(mission, best, version)
        except Exception as e:
            update_mission_status(mission, MissionStatus.FAILED, note=f"Persist error: {e}")
            self._safe_commit("persist_error")
            self._emit_terminal_events(mission, success=False, reason="persist_error")
            return

        update_mission_status(mission, MissionStatus.PLANNED, note=f"Plan v{version} selected.")
        self._safe_commit("plan_selected")
        log_mission_event(
            mission,
            MissionEventType.PLAN_SELECTED,
            payload={
                "version": version,
                "planner": best.planner_name,
                "score": best.score,
                "plan_hash": new_hash,
                "iso_ts": datetime.utcnow().isoformat() + "Z"
            }
        )
        self._safe_commit("plan_selected_event")
        log_info(mission, "Plan selected",
                 version=version, planner=best.planner_name, score=best.score)

    # ------------------------------ Deep Index Builder -----------------------
    def _build_deep_index_context(self) -> Optional[Dict[str, Any]]:
        if not ENABLE_DEEP_INDEX or not (build_index and summarize_for_prompt):
            return None

        def dir_signature(root: str = ".") -> str:
            acc = 0
            for base, _, files in os.walk(root):
                if any(skip in base for skip in (".git", "__pycache__", "venv", ".venv", "node_modules")):
                    continue
                for f in files:
                    if f.endswith(".py"):
                        p = os.path.join(base, f)
                        try:
                            st = os.stat(p)
                            acc ^= int(st.st_mtime_ns) & 0xFFFFFFFFFFFF
                        except Exception:
                            continue
            return f"{acc:012x}"

        now = time.time()
        sig = dir_signature()

        if self._deep_index_cache:
            c_sig = self._deep_index_cache.get("sig")
            ts = self._deep_index_cache.get("ts", 0)
            if c_sig == sig and (now - ts) < DEEP_INDEX_MAX_CACHE_AGE:
                ctx_cached = self._deep_index_cache.get("context")
                if ctx_cached:
                    ctx_cached["cache_hit"] = True
                    return ctx_cached

        try:
            t0 = time.perf_counter()
            idx = build_index(".")
            summary = summarize_for_prompt(idx, max_len=4000)
            ctx = {
                "deep_index_summary": summary,
                "files_scanned": idx.get("files_scanned"),
                "hotspots_count": len(idx.get("complexity_hotspots_top50", [])),
                "duplicate_groups": len(idx.get("duplicate_function_bodies", {})),
                "layers": list(idx.get("layers", {}).keys()),
                "services": idx.get("service_candidates", [])[:12],
                "entrypoints": idx.get("entrypoints", []),
                "index_version": idx.get("index_version"),
                "build_ms": int((time.perf_counter() - t0) * 1000),
                "cache_hit": False
            }
            self._deep_index_cache = {"sig": sig, "ts": now, "context": ctx}
            return ctx
        except Exception as e:
            log_warn(None, "Deep index build failed", error=str(e))
            return None

    # ------------------------------ Plan Scoring / Hash ----------------------
    def _score_plan(self, plan: MissionPlanSchema, metadata: Dict[str, Any]) -> float:
        tasks_list = getattr(plan, "tasks", []) or []
        count = len(tasks_list)
        if count == 0:
            return 0.0
        base = 100.0 - max(count - 40, 0) * 0.5
        return round(base, 2)

    def _build_plan_rationale(self, plan: MissionPlanSchema, score: float, metadata: Dict[str, Any]) -> str:
        return f"score={score}; tasks={len(getattr(plan, 'tasks', []))}"

    def _hash_plan(self, plan_schema: MissionPlanSchema) -> str:
        js = json.dumps({
            "objective": getattr(plan_schema, "objective", ""),
            "tasks": [
                (t.task_id, sorted(getattr(t, "dependencies", [])), t.tool_name)
                for t in getattr(plan_schema, "tasks", [])
            ]
        }, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(js.encode("utf-8")).hexdigest()

    def _next_plan_version(self, mission_id: int) -> int:
        max_version = db.session.scalar(
            select(func.max(MissionPlan.version)).where(MissionPlan.mission_id == mission_id)
        )
        return (max_version or 0) + 1

    # ------------------------------ Persistence ------------------------------
    def _persist_plan(self, mission: Mission, candidate: CandidatePlan, version: int):
        schema = candidate.raw
        plan_signature = json.dumps({
            "objective": getattr(schema, "objective", ""),
            "tasks": [
                (t.task_id, sorted(getattr(t, "dependencies", [])), getattr(t, "tool_name", "") or "")
                for t in getattr(schema, "tasks", [])
            ]
        }, ensure_ascii=False)
        content_hash = hashlib.sha256(plan_signature.encode("utf-8")).hexdigest()
        raw_json = json.dumps({
            "objective": getattr(schema, "objective", ""),
            "tasks_meta": len(getattr(schema, "tasks", []))
        }, ensure_ascii=False)
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
            content_hash=content_hash
        )
        db.session.add(mp)
        db.session.flush()
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
                risk_level="",
                criticality="",
                depends_on_json=t.dependencies
            )
            db.session.add(task_row)
        mission.active_plan_id = mp.id
        self._safe_commit("persist_plan")
        increment_counter("overmind_plans_created_total", {"planner": candidate.planner_name})

    # ------------------------------ Execution Prep ---------------------------
    def _prepare_execution(self, mission: Mission):
        update_mission_status(mission, MissionStatus.RUNNING, note="Execution started.")
        self._safe_commit("enter_execution")
        log_mission_event(mission, MissionEventType.EXECUTION_STARTED,
                          payload={"plan_id": mission.active_plan_id,
                                   "strategy": EXECUTION_STRATEGY,
                                   "iso_ts": datetime.utcnow().isoformat() + "Z"})
        self._safe_commit("exec_started_event")
        log_info(mission, "Execution phase entered.", strategy=EXECUTION_STRATEGY)
        increment_counter("overmind_missions_started_total")

    # ------------------------------ Execution (Topological) ------------------
    def _execution_phase(self, mission: Mission):
        plan = MissionPlan.query.get(mission.active_plan_id)
        if not plan:
            log_error(mission, "Active plan not found.")
            update_mission_status(mission, MissionStatus.FAILED, note="No plan.")
            self._safe_commit("no_plan_fail")
            self._emit_terminal_events(mission, success=False, reason="missing_plan")
            return

        task_index: Dict[str, Task] = {t.task_key: t for t in mission.tasks}
        ordered_keys = sorted(task_index.keys())
        layers = [ordered_keys]

        total_success_before = Task.query.filter_by(mission_id=mission.id,
                                                    status=TaskStatus.SUCCESS).count()
        progress_attempted = False

        for layer_idx, layer_keys in enumerate(layers):
            layer_tasks = [task_index[k] for k in layer_keys]
            pending_or_retry = [t for t in layer_tasks if t.status in (TaskStatus.PENDING, TaskStatus.RETRY)]
            if not pending_or_retry:
                continue
            ready: List[Task] = []
            for t in pending_or_retry:
                deps = t.depends_on_json or []
                if all(task_index[d].status == TaskStatus.SUCCESS for d in deps):
                    ready.append(t)
            if not ready:
                continue
            if len(ready) > TOPO_MAX_PARALLEL:
                ready = ready[:TOPO_MAX_PARALLEL]
            log_info(mission, "Executing layer batch",
                     layer=layer_idx, batch_size=len(ready), layer_total=len(layer_tasks))
            progress_attempted = True
            if EXECUTION_PARALLELISM_MODE == "MULTI":
                app_obj = self._app_ref
                threads: List[threading.Thread] = []
                for tk in ready:
                    th = threading.Thread(
                        target=self._thread_task_wrapper,
                        args=(app_obj, mission.id, tk.id, layer_idx),
                        daemon=True
                    )
                    th.start()
                    threads.append(th)
                for th in threads:
                    th.join(timeout=TASK_EXECUTION_HARD_TIMEOUT_SECONDS)
            else:
                for tk in ready:
                    self._execute_task_with_retry_topological(mission.id, tk.id, layer_idx)

        total_success_after = Task.query.filter_by(mission_id=mission.id,
                                                   status=TaskStatus.SUCCESS).count()
        newly = total_success_after - total_success_before
        self._update_stall_metrics(mission.id, newly, progress_attempted)
        self._safe_commit("post_execution_batch")

    # ------------------------------ Legacy Wave Execution --------------------
    def _execution_wave_legacy(self, mission: Mission):
        ready = self._find_ready_tasks(mission)
        if not ready:
            failed_count = Task.query.filter_by(mission_id=mission.id,
                                                status=TaskStatus.FAILED).count()
            pending_count = Task.query.filter_by(mission_id=mission.id,
                                                 status=TaskStatus.PENDING).count()
            retry_count = Task.query.filter_by(mission_id=mission.id,
                                               status=TaskStatus.RETRY).count()
            if pending_count == 0 and retry_count == 0 and failed_count > 0:
                if failed_count >= REPLAN_FAILURE_THRESHOLD:
                    update_mission_status(mission, MissionStatus.ADAPTING,
                                          note="Adaptive replan trigger (wave).")
                    self._safe_commit("wave_adapt_trigger")
            time.sleep(0.05)
            return
        for t in ready[:TOPO_MAX_PARALLEL]:
            self._execute_task_with_retry_topological(mission.id, t.id, layer_index=-1)

    # ------------------------------ Stall Detection --------------------------
    def _update_stall_metrics(self, mission_id: int, newly_success: int, attempted: bool):
        key = f"_stall_state_{mission_id}"
        state = getattr(self, key, {"window": [], "cycles": 0, "attempts": 0})
        state["window"].append(newly_success)
        state["attempts"] += 1 if attempted else 0
        if len(state["window"]) > STALL_DETECTION_WINDOW:
            state["window"].pop(0)
        if newly_success <= STALL_NO_PROGRESS_THRESHOLD and not attempted:
            state["cycles"] += 1
        else:
            if newly_success > 0:
                state["cycles"] = 0
        setattr(self, key, state)
        if state["cycles"] > STALL_DETECTION_WINDOW:
            log_warn(None, "Potential execution stall",
                     mission_id=mission_id,
                     window=state["window"], cycles=state["cycles"])

    # ------------------------------ Ready Task Discovery ---------------------
    def _find_ready_tasks(self, mission: Mission) -> List[Task]:
        candidates: List[Task] = db.session.query(Task).filter(
            Task.mission_id == mission.id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.RETRY])
        ).options(joinedload(Task.mission)).all()
        
        all_deps = set()
        for t in candidates:
            deps = t.depends_on_json or []
            all_deps.update(deps)
        
        if all_deps:
            dep_rows_dict = {
                task.task_key: task for task in db.session.query(Task).filter(
                    Task.mission_id == mission.id,
                    Task.task_key.in_(all_deps)
                ).all()
            }
        else:
            dep_rows_dict = {}
        
        ready: List[Task] = []
        for t in candidates:
            deps = t.depends_on_json or []
            if not deps:
                ready.append(t)
                continue
            
            missing_deps = [dep for dep in deps if dep not in dep_rows_dict]
            if missing_deps:
                log_warn(mission, "Task missing dependency", task_key=t.task_key)
                continue
                
            all_done = all(
                dep_rows_dict[dep].status == TaskStatus.SUCCESS 
                for dep in deps
            )
            if all_done:
                ready.append(t)
        return ready

    # ------------------------------ Thread Wrapper ---------------------------
    def _thread_task_wrapper(self, app_obj, mission_id: int, task_id: int, layer_index: int):
        try:
            with app_obj.app_context():
                mission = Mission.query.get(mission_id)
                if not mission:
                    log_warn(None, "Mission disappeared in thread", mission_id=mission_id)
                    return
                self._execute_task_with_retry_topological(mission_id, task_id, layer_index)
        except Exception as e:
            print(f"[Overmind][thread][ERROR] mission={mission_id} task={task_id} {e}")

    # ------------------------------ Guard + Execution ------------------------
    def _precheck_and_autofix_task(self, mission: Mission, task: Task) -> Dict[str, Any]:
        outcome = {"ok": True, "action": "pass", "notes": [], "error": None, "category": "ok"}
        if not GUARD_ENABLED:
            return outcome
        raw_tool = task.tool_name or ""
        description = task.description or ""
        notes = outcome["notes"]
        canon, cnotes = _canonicalize_tool_name(raw_tool, description)
        notes.extend(cnotes)
        if canon != raw_tool:
            task.tool_name = canon
        args = _ensure_dict(task.tool_args_json)
        task.tool_args_json = args
        if canon in (CANON_WRITE, CANON_READ, CANON_ENSURE):
            if GUARD_FILE_AUTOFIX:
                _autofill_file_args(canon, args, mission, task, notes)
            else:
                missing = [k for k in FILE_REQUIRED.get(canon, []) if not args.get(k)]
                if missing:
                    outcome.update(ok=False, action="early_fail",
                                   error=f"Missing file args: {missing}",
                                   category="args_missing")
                    return outcome
        if canon in FILE_REQUIRED:
            missing2 = [k for k in FILE_REQUIRED[canon] if not args.get(k)]
            if missing2:
                outcome.update(ok=False, action="early_fail",
                               error=f"Missing file args after autofix: {missing2}",
                               category="args_missing")
                return outcome
        if not _tool_exists(task.tool_name):
            if canon in (CANON_WRITE, CANON_READ):
                notes.append("tool_absent_but_forced_file")
            else:
                if GUARD_FORCE_FILE_INTENT:
                    if _looks_like_write(description):
                        task.tool_name = CANON_WRITE
                        notes.append("fallback_forced_write")
                        if GUARD_FILE_AUTOFIX:
                            _autofill_file_args(CANON_WRITE, args, mission, task, notes)
                    elif _looks_like_read(description):
                        task.tool_name = CANON_READ
                        notes.append("fallback_forced_read")
                        if GUARD_FILE_AUTOFIX:
                            _autofill_file_args(CANON_READ, args, mission, task, notes)
            if not _tool_exists(task.tool_name):
                outcome.update(ok=False, action="early_fail",
                               error=f"ToolNotFound: {task.tool_name}",
                               category="tool_missing")
                notes.append("tool_unresolvable")
                return outcome
        if outcome["ok"]:
            if any(n.startswith("autofill_") for n in notes):
                outcome["action"] = "autofilled"
            elif canon != raw_tool:
                outcome["action"] = "normalized"
        return outcome

    def _execute_task_with_retry_topological(self, mission_id: int, task_id: int, layer_index: int):
        mission = Mission.query.get(mission_id)
        if not mission:
            return
        task = Task.query.get(task_id)
        if not task or task.status not in (TaskStatus.PENDING, TaskStatus.RETRY):
            return
        nxt = getattr(task, "next_retry_at", None)
        if nxt and utc_now() < nxt:
            return

        guard_result = self._precheck_and_autofix_task(mission, task)
        if guard_result["action"] != "pass":
            log_info(mission, "Guard processed task",
                     task_key=task.task_key,
                     action=guard_result["action"],
                     notes="|".join(guard_result["notes"][:10]),
                     category=guard_result.get("category"),
                     error=guard_result["error"])
        if not guard_result["ok"]:
            self._finalize_failed_task(mission, task,
                                       guard_result["error"] or "GuardFailed",
                                       layer_index, retry=False)
            return

        if task.tool_name and not tool_policy_engine.authorize(task.tool_name, mission, task):
            self._finalize_failed_task(mission, task, "PolicyDenied", layer_index, retry=False)
            return

        original_args = _ensure_dict(task.tool_args_json)
        if INTERPOLATION_ENABLED and task.tool_name in (CANON_THINK, CANON_WRITE, CANON_APPEND):
            new_args, interp_notes = _render_template_in_args(original_args, mission_id)
            task.tool_args_json = new_args
            if interp_notes:
                log_info(mission, "Template interpolation",
                         task_key=task.task_key,
                         placeholders="|".join(interp_notes[:12]))
            self._safe_commit("template_interp")

        attempt_index = task.attempt_count + 1
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        self._safe_commit("task_start")
        log_mission_event(mission, MissionEventType.TASK_STARTED, payload={
            "task_id": task.id, "task_key": task.task_key,
            "layer": layer_index, "attempt": attempt_index, "tool": task.tool_name,
            "iso_ts": datetime.utcnow().isoformat() + "Z"
        })
        log_debug(mission, "Task started", task_key=task.task_key,
                  attempt=attempt_index, layer=layer_index, tool=task.tool_name)

        perf_start = time.perf_counter()
        self._task_exec_metrics["total_tasks"] += 1
        tool_key = task.tool_name or "unknown_tool"

        try:
            result_payload = self._execute_tool(task) if task.tool_name else self._fallback_maestro(task)
            if L4_SOFT_MISSING_FILES and task.tool_name == CANON_READ:
                data = result_payload.get("data") or {}
                if isinstance(data, dict) and not data.get("exists", True):
                    if not data.get("content"):
                        data["content"] = f"{L4_MISSING_FILE_MARKER} {data.get('path','')}"
                        result_payload["result_text"] = data["content"]

            if not verification_service.verify(task):
                raise TaskExecutionError("Verification failed.")

            data_payload = result_payload.get("data")
            answer = _extract_answer_from_data(data_payload)
            meta_update = result_payload.get("meta") or {}
            if answer and "answer" not in meta_update:
                meta_update["answer"] = answer

            arg_risk = None
            if isinstance(task.tool_args_json, dict):
                arg_risk = task.tool_args_json.get("_meta_risk")
            if arg_risk is not None:
                meta_update["risk_score"] = arg_risk

            if DIFF_ENABLED and task.tool_name == CANON_WRITE:
                path = (task.tool_args_json or {}).get("path")
                if isinstance(path, str) and path.strip():
                    self._augment_with_diff(task, path, meta_update)

            task.result_text = (result_payload.get("result_text") or "")[:16000]
            if answer and not task.result_text:
                task.result_text = answer[:16000]
            if hasattr(task, "result_meta_json"):
                cur = getattr(task, "result_meta_json") or {}
                if not isinstance(cur, dict):
                    cur = {}
                cur.update(meta_update)
                task.result_meta_json = cur  # type: ignore

            task.status = TaskStatus.SUCCESS
            task.attempt_count = attempt_index
            task.finished_at = utc_now()
            task.duration_ms = int((time.perf_counter() - perf_start) * 1000)
            self._safe_commit("task_success")
            self._task_exec_metrics["success"] += 1
            self._tool_success_map[tool_key] = self._tool_success_map.get(tool_key, 0) + 1

            increment_counter("overmind_tasks_executed_total", {"result": "success"})
            log_mission_event(mission, MissionEventType.TASK_COMPLETED, payload={
                "task_id": task.id, "attempt": attempt_index, "layer": layer_index,
                "duration_ms": task.duration_ms, "iso_ts": datetime.utcnow().isoformat() + "Z"
            })
            log_info(mission, "Task success", task_key=task.task_key,
                     attempt=attempt_index, layer=layer_index, duration_ms=task.duration_ms)
        except Exception as e:
            self._handle_task_failure(mission, task, e, attempt_index, layer_index, perf_start, tool_key)

        self._safe_terminal_event(mission_id)

    def _finalize_failed_task(self, mission: Mission, task: Task, error_text: str,
                              layer_index: int, retry: bool):
        task.status = TaskStatus.FAILED
        task.error_text = error_text[:500]
        task.attempt_count += 1
        task.finished_at = utc_now()
        task.duration_ms = 0
        self._safe_commit("task_fail_early")
        self._task_exec_metrics["failed"] += 1
        log_warn(mission, "Task failed early", task_key=task.task_key, error=task.error_text)
        log_mission_event(mission, MissionEventType.TASK_FAILED, payload={
            "task_id": task.id, "attempt": task.attempt_count, "retry": retry,
            "layer": layer_index, "error": task.error_text,
            "iso_ts": datetime.utcnow().isoformat() + "Z"
        })
        increment_counter("overmind_tasks_executed_total", {"result": "failed_early"})

    def _handle_task_failure(self, mission: Mission, task: Task, exc: Exception,
                             attempt_index: int, layer_index: int, perf_start: float, tool_key: str):
        try:
            db.session.refresh(task)
        except Exception:
            pass
        task.attempt_count = attempt_index
        task.error_text = str(exc)[:500]
        task.finished_at = utc_now()
        task.duration_ms = int((time.perf_counter() - perf_start) * 1000)
        allow_retry = task.attempt_count < task.max_attempts
        if allow_retry:
            task.status = TaskStatus.RETRY
            backoff = self._compute_backoff(task.attempt_count)
            if hasattr(task, "next_retry_at"):
                task.next_retry_at = utc_now() + timedelta(seconds=backoff)
            self._task_exec_metrics["retry"] += 1
            log_warn(mission, "Task failed; scheduling retry",
                     task_key=task.task_key, attempt=task.attempt_count,
                     backoff_s=round(backoff, 2), error=str(exc))
            log_mission_event(mission, MissionEventType.TASK_FAILED, payload={
                "task_id": task.id, "attempt": task.attempt_count, "retry": True,
                "layer": layer_index, "error": str(exc)[:200],
                "iso_ts": datetime.utcnow().isoformat() + "Z"
            })
            increment_counter("overmind_tasks_executed_total", {"result": "retry"})
        else:
            task.status = TaskStatus.FAILED
            self._task_exec_metrics["failed"] += 1
            log_warn(mission, "Task failed permanently",
                     task_key=task.task_key, attempt=task.attempt_count, error=str(exc))
            log_mission_event(mission, MissionEventType.TASK_FAILED, payload={
                "task_id": task.id, "attempt": task.attempt_count, "retry": False,
                "layer": layer_index, "error": str(exc)[:200],
                "iso_ts": datetime.utcnow().isoformat() + "Z"
            })
            increment_counter("overmind_tasks_executed_total", {"result": "failed"})
        self._tool_fail_map[tool_key] = self._tool_fail_map.get(tool_key, 0) + 1
        self._safe_commit("task_failure_commit")

    def _fallback_maestro(self, task: Task):
        if hasattr(maestro, "execute_task"):
            maestro.execute_task(task)
            db.session.refresh(task)
        return {"status": "success", "result_text": task.result_text or "[Fallback Execution]", "meta": {}}

    # ------------------------------ Diff Augmentation ------------------------
    def _augment_with_diff(self, task: Task, path: str, meta_update: Dict[str, Any]):
        try:
            if BACKUP_ON_WRITE:
                old_exists, old_content = _read_file_safe(path + ".bak")
            else:
                old_exists, old_content = _read_file_safe(path)
            old_hash = _sha256_text(old_content) if old_exists else ""
            new_exists, new_content = _read_file_safe(path)
            if not new_exists:
                return
            new_hash = _sha256_text(new_content)
            if not old_exists:
                diff_data = _compute_diff("", new_content, DIFF_MAX_LINES)
                diff_data.update({
                    "old_sha256": "", "new_sha256": new_hash,
                    "no_op": False, "backup_created": False
                })
                meta_update.update(diff_data)
                return
            if old_content == new_content:
                meta_update.update({
                    "diff": "", "diff_truncated": False,
                    "old_sha256": old_hash, "new_sha256": new_hash,
                    "lines_added": 0, "lines_removed": 0,
                    "first_changed_line": 0,
                    "content_size_old": len(old_content),
                    "content_size_new": len(new_content),
                    "change_ratio": 0.0,
                    "change_ratio_class": "stable",
                    "no_op": True,
                    "backup_created": False
                })
                return
            diff_data = _compute_diff(old_content, new_content, DIFF_MAX_LINES)
            diff_data.update({
                "old_sha256": old_hash, "new_sha256": new_hash,
                "no_op": False, "backup_created": False
            })
            meta_update.update(diff_data)
        except Exception as e:
            meta_update.setdefault("diff_error", str(e)[:120])

    # ------------------------------ Tool Execution ---------------------------
    def _execute_tool(self, task: Task) -> Dict[str, Any]:
        if agent_tools is None:
            raise TaskExecutionError("Agent tools module not available.")
        tool_name_raw = task.tool_name or ""
        if not tool_name_raw:
            raise TaskExecutionError("Empty tool_name.")
        canonical = tool_name_raw
        if hasattr(agent_tools, "resolve_tool_name"):
            try:
                canonical = agent_tools.resolve_tool_name(tool_name_raw) or tool_name_raw
            except Exception:
                pass
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

        status_ok = True
        result_text = ""
        meta_payload = {
            "canonical_tool": canonical,
            "invocation_tool_name": tool_name_raw
        }
        data_payload = None
        if hasattr(result_obj, "ok"):
            status_ok = getattr(result_obj, "ok", True)
            for attr in ("data", "result", "content", "_content"):
                if hasattr(result_obj, attr):
                    val = getattr(result_obj, attr)
                    if val is not None:
                        data_payload = val
                        break
            err_attr = getattr(result_obj, "error", None)
            if not status_ok and err_attr:
                if L4_SOFT_MISSING_FILES and tool_name_raw == CANON_READ and "FILE_NOT_FOUND" in str(err_attr):
                    status_ok = True
                    data_payload = {"content": "", "exists": False, "missing": True, "soft_missing": True}
                    meta_payload["soft_missing"] = True
                else:
                    raise TaskExecutionError(f"ToolFailed: {err_attr}")
            if hasattr(result_obj, "meta"):
                try:
                    mf = getattr(result_obj, "meta")
                    if isinstance(mf, dict):
                        meta_payload.update(mf)
                except Exception:
                    pass
        else:
            data_payload = result_obj

        if isinstance(data_payload, dict):
            if "content" in data_payload and isinstance(data_payload["content"], str):
                result_text = data_payload["content"]
            else:
                try:
                    result_text = json.dumps(data_payload, ensure_ascii=False)[:4000]
                except Exception:
                    result_text = str(data_payload)[:4000]
        elif isinstance(data_payload, str):
            result_text = data_payload[:4000]
        elif data_payload is not None:
            result_text = str(data_payload)[:4000]
        else:
            result_text = "[NO TOOL OUTPUT]"

        return {
            "status": "success" if status_ok else "error",
            "result_text": result_text,
            "data": data_payload,
            "meta": meta_payload
        }

    # ------------------------------ Backoff ----------------------------------
    def _compute_backoff(self, attempt: int) -> float:
        base = TASK_RETRY_BACKOFF_BASE ** attempt
        jitter = random.uniform(0, TASK_RETRY_BACKOFF_JITTER)
        return min(base + jitter, 600.0)

    # ------------------------------ Terminal Check ---------------------------
    def _check_terminal(self, mission: Mission):
        pending = Task.query.filter_by(mission_id=mission.id,
                                       status=TaskStatus.PENDING).count()
        retry = Task.query.filter_by(mission_id=mission.id,
                                     status=TaskStatus.RETRY).count()
        running = Task.query.filter_by(mission_id=mission.id,
                                       status=TaskStatus.RUNNING).count()
        failed = Task.query.filter_by(mission_id=mission.id,
                                      status=TaskStatus.FAILED).count()
        log_debug(mission, "Terminal snapshot",
                  pending=pending, retry=retry, running=running, failed=failed,
                  status=str(mission.status))
        if pending == 0 and retry == 0 and running == 0:
            if failed == 0:
                if mission.status != MissionStatus.SUCCESS:
                    self._finalize_mission_risk(mission)
                    self._classify_architecture_outcome(mission)
                    update_mission_status(mission, MissionStatus.SUCCESS,
                                          note="All tasks completed.")
                    increment_counter("overmind_missions_finished_total", {"result": "success"})
                    log_info(mission, "Mission success")
                    self._emit_terminal_events(mission, success=True, reason="all_tasks_success")
            else:
                if failed >= REPLAN_FAILURE_THRESHOLD and self._adaptive_cycles_used(mission) < ADAPTIVE_MAX_CYCLES:
                    if mission.status != MissionStatus.ADAPTING:
                        update_mission_status(mission, MissionStatus.ADAPTING,
                                              note="Entering adaptive replan.")
                        log_info(mission, "Switching to adaptive replan", failed=failed)
                else:
                    if mission.status != MissionStatus.FAILED:
                        update_mission_status(mission, MissionStatus.FAILED,
                                              note=f"{failed} tasks failed.")
                        increment_counter("overmind_missions_finished_total", {"result": "failed"})
                        log_warn(mission, "Mission failed terminally", failed=failed)
                        self._emit_terminal_events(mission, success=False, reason="tasks_failed")
            self._safe_commit("terminal_transition")

    # ------------------------------ Risk Summary -----------------------------
    def _finalize_mission_risk(self, mission: Mission):
        tasks = db.session.query(Task).filter_by(mission_id=mission.id).options(joinedload(Task.mission)).all()
        buckets = {"low": 0, "mid": 0, "high": 0}
        for t in tasks:
            rs = None
            if isinstance(t.tool_args_json, dict):
                rs = t.tool_args_json.get("_meta_risk")
            if not rs and isinstance(getattr(t, "result_meta_json", None), dict):
                rs = t.result_meta_json.get("risk_score")
            try:
                val = float(rs)
            except Exception:
                continue
            if val < 2.5:
                buckets["low"] += 1
            elif val < 5.5:
                buckets["mid"] += 1
            else:
                buckets["high"] += 1
        log_info(mission, "Mission risk summary", **buckets)
        log_mission_event(mission, MissionEventType.RISK_SUMMARY,
                          payload={"risk_summary": buckets})
        self._safe_commit("risk_summary")

    # ------------------------------ Architecture Outcome ---------------------
    def _classify_architecture_outcome(self, mission: Mission):
        arch_tasks = db.session.query(Task).filter_by(
            mission_id=mission.id,
            status=TaskStatus.SUCCESS
        ).options(joinedload(Task.mission)).all()
        produced = False
        target = L4_EXPECT_ARCH_FILE.lower()
        for t in arch_tasks:
            if t.tool_name == CANON_WRITE and isinstance(t.tool_args_json, dict):
                path = (t.tool_args_json or {}).get("path", "")
                if isinstance(path, str) and path.lower().endswith(target):
                    produced = True
                    break
        log_mission_event(
            mission,
            MissionEventType.ARCHITECTURE_CLASSIFIED,
            payload={"architecture_artifact": produced, "expected": target}
        )
        log_info(mission, "Architecture artifact classification",
                 produced=produced, expected=target)
        self._safe_commit("arch_outcome")

    # ------------------------------ Helpers ----------------------------------
    def _has_open_tasks(self, mission: Mission) -> bool:
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

    # ------------------------------ Adaptive Replan --------------------------
    def _adaptive_replan(self, mission: Mission):
        failed_tasks = Task.query.filter_by(mission_id=mission.id,
                                            status=TaskStatus.FAILED).all()
        if not failed_tasks:
            update_mission_status(mission, MissionStatus.RUNNING,
                                  note="No failed tasks; resume execution.")
            self._safe_commit("adapt_no_failed")
            return
        if self._adaptive_cycles_used(mission) >= ADAPTIVE_MAX_CYCLES:
            update_mission_status(mission, MissionStatus.FAILED,
                                  note="Adaptive cycle limit reached.")
            self._safe_commit("adapt_limit")
            log_warn(mission, "Adaptive cycle limit reached -> Mission FAILED.")
            self._emit_terminal_events(mission, success=False,
                                       reason="adaptive_cycle_limit")
            return

        failure_context = {t.task_key: (t.error_text or "unknown") for t in failed_tasks}
        log_info(mission, "Adaptive replanning start", failed_tasks=len(failure_context))
        log_mission_event(
            mission,
            MissionEventType.REPLAN_TRIGGERED,
            payload={"failed_tasks": list(failure_context.keys()),
                     "iso_ts": datetime.utcnow().isoformat() + "Z"}
        )
        self._safe_commit("replan_triggered")

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
            update_mission_status(mission, MissionStatus.FAILED,
                                  note="No planner for adaptive replan.")
            self._safe_commit("no_planner_adapt")
            self._emit_terminal_events(mission, success=False, reason="no_planner_adaptive")
            return

        adaptive_deep_ctx = None
        if ADAPTIVE_USE_DEEP_CONTEXT:
            adaptive_deep_ctx = self._build_deep_index_context()

        try:
            result = chosen.instrumented_generate(mission.objective,
                                                  context=None,
                                                  deep_context=adaptive_deep_ctx)
            plan_obj: MissionPlanSchema = result["plan"]
            meta = result["meta"]
            version = self._next_plan_version(mission.id)
            candidate = CandidatePlan(
                raw=plan_obj,
                planner_name=meta.get("planner") or getattr(chosen, "name", "unknown"),
                score=self._score_plan(plan_obj, meta),
                rationale=f"ADAPTIVE: {self._build_plan_rationale(plan_obj, 0, meta)}",
                telemetry={"duration_ms": meta.get("duration_ms"), **meta}
            )
            new_hash = self._hash_plan(plan_obj)
            if self._last_plan_hash and self._last_plan_hash == new_hash:
                log_warn(mission, "Adaptive convergence guard: plan hash unchanged",
                         version=version, hash=new_hash)
            self._last_plan_hash = new_hash
            self._persist_plan(mission, candidate, version)
            update_mission_status(mission, MissionStatus.PLANNED,
                                  note=f"Adaptive plan v{version} ready.")
            self._safe_commit("adaptive_plan_ready")
            log_mission_event(
                mission,
                MissionEventType.REPLAN_APPLIED,
                payload={"version": version,
                         "planner": candidate.planner_name,
                         "plan_hash": new_hash,
                         "iso_ts": datetime.utcnow().isoformat() + "Z"}
            )
            self._safe_commit("replan_applied_event")
            log_info(mission, "Adaptive plan applied",
                     version=version, planner=candidate.planner_name)
        except Exception as e:
            log_error(mission, "Adaptive replanning failed", error=str(e))
            update_mission_status(mission, MissionStatus.FAILED,
                                  note=f"Adaptive failed: {e}")
            self._safe_commit("adaptive_failed")
            self._emit_terminal_events(mission, success=False,
                                       reason="adaptive_replan_failed", error=str(e))

    # ------------------------------ Terminal Events --------------------------
    def _emit_terminal_events(self, mission: Mission, success: bool,
                              reason: str, error: Optional[str] = None):
        if mission.status not in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
            return
        last_event = mission.events[-1].event_type if mission.events else None
        if last_event == MissionEventType.FINALIZED:
            return
        if success:
            log_mission_event(mission, MissionEventType.MISSION_COMPLETED,
                              payload={"reason": reason,
                                       "iso_ts": datetime.utcnow().isoformat() + "Z"})
        else:
            log_mission_event(mission, MissionEventType.MISSION_FAILED,
                              payload={"reason": reason,
                                       "error": error,
                                       "iso_ts": datetime.utcnow().isoformat() + "Z"})
        log_mission_event(mission, MissionEventType.FINALIZED,
                          payload={
                              "status": mission.status.value,
                              "reason": reason,
                              "tool_success_map": self._tool_success_map,
                              "tool_fail_map": self._tool_fail_map,
                              "task_exec_metrics": self._task_exec_metrics,
                              "planner_failures_sample": self._planner_failure_samples[-10:],
                              "iso_ts": datetime.utcnow().isoformat() + "Z"
                          })
        self._safe_commit("mission_finalized")
        log_info(mission, "Terminal mission events emitted",
                 success=success, reason=reason, status=mission.status.value)

    def _safe_terminal_event(self, mission_id: int):
        mission = Mission.query.get(mission_id)
        if not mission:
            return
        try:
            self._check_terminal(mission)
            if mission.status == MissionStatus.SUCCESS:
                self._emit_terminal_events(mission, success=True, reason="post_check")
            elif mission.status == MissionStatus.FAILED:
                self._emit_terminal_events(mission, success=False, reason="post_check")
        except Exception:
            pass

    # ------------------------------ App Context ------------------------------
    def _ensure_app_ref(self):
        if self._app_ref is None:
            if not has_app_context():
                raise RuntimeError("No application context; call inside Flask app context.")
            self._app_ref = current_app._get_current_object()


# =================================================================================================
# Singleton Facade
# =================================================================================================
_overmind_service_singleton = OvermindService()

def start_mission(objective: str, initiator: User) -> Mission:
    """Facade: create and execute a mission."""
    return _overmind_service_singleton.start_new_mission(objective, initiator)

def run_mission_lifecycle(mission_id: int):
    """Facade: run lifecycle for an existing mission id."""
    return _overmind_service_singleton.run_mission_lifecycle(mission_id)

# =================================================================================================
# END OF FILE (v10.3.0-l4-pro)
# =================================================================================================
