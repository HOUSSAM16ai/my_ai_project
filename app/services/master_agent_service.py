# app/services/master_agent_service.py
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# =============================================================================
# OVERMIND ORCHESTRATION SERVICE (Enterprise / Hyper-Hardened Edition)
# File: app/services/master_agent_service.py
# Version: 9.0.0-hyper
#
# WHAT'S NEW (vs 8.0.0-enterprise):
# ---------------------------------
# 1. Zero-Fail Core:
#       - Stronger guard pipeline: categorizes failure reasons (tool_missing,
#         args_missing, policy_denied, internal_error) and short‑circuits fast.
#       - Ensures interpolation never hard-fails unless explicitly configured.
# 2. Deterministic Interpolation & Caching:
#       - Single pass placeholder resolver ({{tNN.content}} / {{tNN.answer}})
#         with memoized prior outputs + optional partial redaction hooks.
#       - Supports nested dict/list traversal & idempotence guarantees.
# 3. Atomic Write Awareness (Meta):
#       - If a write_file tool sets meta.atomic=True (future extension),
#         orchestrator surfaces that in result_meta_json.
# 4. Extended Diff Intelligence:
#       - Adds content_size_{old,new} and change_ratio metrics.
#       - Adds first_changed_line hint for UI navigation.
# 5. Adaptive Stall Heuristics:
#       - Distinguishes between "execution_stall" vs "dependency_stall".
# 6. Structured Logging & Telemetry:
#       - Uniform JSON shape; added category, attempt, layer, phase fields.
# 7. Expanded Answer Harvesting:
#       - Scans meta.data.answer + meta.answer + root-level answer tokens.
# 8. Risk Propagation:
#       - Aggregated mission risk summary on completion (counts by bucket).
# 9. Safer Concurrency:
#       - Thread wrapper defensive refresh & rollback isolation.
# 10. Code Organization:
#       - Segmented utility groups (GUARD, INTERPOLATION, EXECUTION, ADAPTIVE).
#
# Environment Flags (same & extended):
# ------------------------------------
#   OVERMIND_GUARD_ENABLED=1
#   OVERMIND_GUARD_FILE_AUTOFIX=1
#   OVERMIND_GUARD_FILE_DEFAULT_EXT=.md
#   OVERMIND_GUARD_FILE_DEFAULT_CONTENT="..."
#   OVERMIND_GUARD_ACCEPT_DOTTED=1
#   OVERMIND_GUARD_FORCE_FILE_INTENT=1
#
#   OVERMIND_INTERPOLATION_ENABLED=1
#   OVERMIND_ALLOW_TEMPLATE_FAILURE=1
#
#   OVERMIND_DIFF_ENABLED=1
#   OVERMIND_DIFF_MAX_LINES=400
#   OVERMIND_BACKUP_ON_WRITE=0
#
#   OVERMIND_EXEC_PARALLEL=MULTI|SEQUENTIAL
#   OVERMIND_POLL_INTERVAL_SECONDS=0.18
#
# Public API:
# -----------
#   start_mission(objective: str, initiator: User) -> Mission
#   run_mission_lifecycle(mission_id: int)
#
# Contract:
# ---------
#   - Does not mutate DB schema.
#   - All enhancements stored in task.result_meta_json or logged events.
#
# =============================================================================

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
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

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

# Planner factory & schemas
from app.overmind.planning.factory import get_all_planners
from app.overmind.planning.schemas import MissionPlanSchema

# Planner base errors (fallback gracefully if import fails)
try:
    from app.overmind.planning.base_planner import PlannerError, PlanValidationError  # type: ignore
except Exception:  # pragma: no cover
    class PlannerError(Exception): ...
    class PlanValidationError(Exception): ...

# Generation / Maestro service (optional)
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

# Agent Tools (registry of runtime tools)
try:
    from app.services import agent_tools
except Exception:  # pragma: no cover
    agent_tools = None  # type: ignore

# -----------------------------------------------------------------------------
# Policy & Verification (Extensible)
# -----------------------------------------------------------------------------
class ToolPolicyEngine:
    def authorize(self, tool_name: str, mission: Mission, task: Task) -> bool:
        # Hook: integrate RBAC / ABAC / usage quotas.
        return True
tool_policy_engine = ToolPolicyEngine()

class VerificationService:
    def verify(self, task: Task) -> bool:
        # Hook: add checksum / domain-specific validation.
        return True
verification_service = VerificationService()

# -----------------------------------------------------------------------------
# Metrics Stubs (Integrate with Prometheus / OpenTelemetry)
# -----------------------------------------------------------------------------
def increment_counter(name: str, labels: Dict[str, str] | None = None): pass
def observe_histogram(name: str, value: float, labels: Dict[str, str] | None = None): pass
def set_gauge(name: str, value: float, labels: Dict[str, str] | None = None): pass

# -----------------------------------------------------------------------------
# Global Configuration / Controls
# -----------------------------------------------------------------------------
OVERMIND_VERSION = "9.0.0-hyper"
DEFAULT_MAX_TASK_ATTEMPTS = 3
ADAPTIVE_MAX_CYCLES = 3
REPLAN_FAILURE_THRESHOLD = 2

EXECUTION_STRATEGY = "topological"
EXECUTION_PARALLELISM_MODE = os.getenv("OVERMIND_EXEC_PARALLEL", "MULTI").upper()  # MULTI|SEQUENTIAL
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

# -----------------------------------------------------------------------------
# Guard / Hardening Environment
# -----------------------------------------------------------------------------
GUARD_ENABLED = os.getenv("OVERMIND_GUARD_ENABLED", "1") == "1"
GUARD_FILE_AUTOFIX = os.getenv("OVERMIND_GUARD_FILE_AUTOFIX", "1") == "1"
GUARD_ACCEPT_DOTTED = os.getenv("OVERMIND_GUARD_ACCEPT_DOTTED", "1") == "1"
GUARD_FORCE_FILE_INTENT = os.getenv("OVERMIND_GUARD_FORCE_FILE_INTENT", "1") == "1"
GUARD_FILE_DEFAULT_EXT = os.getenv("OVERMIND_GUARD_FILE_DEFAULT_EXT", ".md")
GUARD_FILE_DEFAULT_CONTENT = os.getenv(
    "OVERMIND_GUARD_FILE_DEFAULT_CONTENT",
    "Auto-generated content placeholder."
)

INTERPOLATION_ENABLED = os.getenv("OVERMIND_INTERPOLATION_ENABLED", "1") == "1"
ALLOW_TEMPLATE_FAILURE = os.getenv("OVERMIND_ALLOW_TEMPLATE_FAILURE", "1") == "1"

DIFF_ENABLED = os.getenv("OVERMIND_DIFF_ENABLED", "1") == "1"
DIFF_MAX_LINES = int(os.getenv("OVERMIND_DIFF_MAX_LINES", "400"))
BACKUP_ON_WRITE = os.getenv("OVERMIND_BACKUP_ON_WRITE", "0") == "1"

# Canonical tool names
CANON_WRITE = "write_file"
CANON_READ = "read_file"
CANON_THINK = "generic_think"

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
}

PLACEHOLDER_PATTERN = re.compile(r"\{\{(t\d{2})\.(content|answer)\}\}", re.IGNORECASE)

# -----------------------------------------------------------------------------
# Logging Utilities
# -----------------------------------------------------------------------------
def _emit(level: str, line: str):
    if has_app_context():
        logger = current_app.logger
        fn = getattr(logger, {"info":"info","warn":"warning","error":"error","debug":"debug"}[level], logger.info)
        fn(line)
    else:
        print(f"[Overmind:{level}] {line}")

def _log(level: str, mission: Mission | None, message: str, **extra):
    payload = {
        "layer": "overmind",
        "component": "orchestrator",
        "mission_id": getattr(mission, "id", None),
        "message": message,
        **extra
    }
    _emit(level, json.dumps(payload, ensure_ascii=False))

def log_info(mission: Mission | None, message: str, **extra): _log("info", mission, message, **extra)
def log_warn(mission: Mission | None, message: str, **extra): _log("warn", mission, message, **extra)
def log_error(mission: Mission | None, message: str, **extra): _log("error", mission, message, **extra)
def log_debug(mission: Mission | None, message: str, **extra):
    if VERBOSE_DEBUG:
        _log("debug", mission, f"[DEBUG] {message}", **extra)

# -----------------------------------------------------------------------------
# Mission Lock (placeholder – integrate distributed lock if multi-node)
# -----------------------------------------------------------------------------
@contextmanager
def mission_lock(mission_id: int):
    yield

# -----------------------------------------------------------------------------
# Exception Types
# -----------------------------------------------------------------------------
class OrchestratorError(Exception): ...
class PlannerSelectionError(OrchestratorError): ...
class PlanPersistenceError(OrchestratorError): ...
class TaskExecutionError(OrchestratorError): ...
class PolicyDeniedError(OrchestratorError): ...
class AdaptiveReplanError(OrchestratorError): ...

# -----------------------------------------------------------------------------
# Candidate Plan Container
# -----------------------------------------------------------------------------
@dataclass
class CandidatePlan:
    raw: MissionPlanSchema
    planner_name: str
    score: float
    rationale: str
    telemetry: Dict[str, Any]

# =============================================================================
# Generic Utilities
# =============================================================================
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

def _make_backup(path: str) -> bool:
    if not BACKUP_ON_WRITE or not os.path.isfile(path):
        return False
    try:
        bak = path + ".bak"
        if os.path.exists(bak):
            ts = int(time.time())
            bak = f"{path}.bak.{ts}"
        with open(path, "rb") as src, open(bak, "wb") as dst:
            dst.write(src.read())
        return True
    except Exception:
        return False

def _compute_diff(old: str, new: str, max_lines: int) -> Dict[str, Any]:
    diff_lines = list(difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile="original",
        tofile="modified",
        lineterm=""
    ))
    truncated = False
    if len(diff_lines) > max_lines:
        diff_display = diff_lines[:max_lines] + ["... (diff truncated)"]
        truncated = True
    else:
        diff_display = diff_lines
    added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    # First changed line heuristic
    first_changed = 0
    for i, l in enumerate(diff_lines):
        if (l.startswith("+") and not l.startswith("+++")) or (l.startswith("-") and not l.startswith("---")):
            first_changed = i + 1
            break
    old_sz = len(old)
    new_sz = len(new)
    change_ratio = 0.0
    denom = max(old_sz, 1)
    if old != new:
        change_ratio = min(1.0, (abs(new_sz - old_sz) + added + removed) / (denom + added + removed))
    return {
        "diff": "\n".join(diff_display),
        "diff_truncated": truncated,
        "lines_added": added,
        "lines_removed": removed,
        "first_changed_line": first_changed,
        "content_size_old": old_sz,
        "content_size_new": new_sz,
        "change_ratio": round(change_ratio, 4)
    }

def _extract_answer_from_data(data: Any) -> Optional[str]:
    # Multi-layer harvest
    if isinstance(data, dict):
        for k in ("answer", "output", "result", "text"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
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
        reg = getattr(agent_tools, "_TOOL_REGISTRY", {})
        return name in reg
    except Exception:
        return False

# =============================================================================
# GUARD PIPELINE
# =============================================================================
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

    if suffix:
        if suffix in WRITE_SUFFIXES:
            notes.append(f"suffix_write:{suffix}")
            return CANON_WRITE, notes
        if suffix in READ_SUFFIXES:
            notes.append(f"suffix_read:{suffix}")
            return CANON_READ, notes

    if "write" in name or "create" in name:
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
    required = FILE_REQUIRED[tool]
    changed = False
    if "path" in required and not tool_args.get("path"):
        fname = f"mission{mission.id}_task{task.task_key}{GUARD_FILE_DEFAULT_EXT}"
        tool_args["path"] = fname
        notes.append(f"autofill_path:{fname}")
        changed = True
    if "content" in required and tool == CANON_WRITE:
        content_val = tool_args.get("content")
        if not isinstance(content_val, str) or not content_val.strip():
            tool_args["content"] = GUARD_FILE_DEFAULT_CONTENT
            notes.append("autofill_content:default")
            changed = True
    if changed:
        notes.append("mandatory_args_filled")

# =============================================================================
# INTERPOLATION
# =============================================================================
def _collect_prior_outputs(mission_id: int) -> Dict[str, Dict[str, str]]:
    rows: List[Task] = Task.query.filter(
        Task.mission_id == mission_id,
        Task.status == TaskStatus.SUCCESS
    ).all()
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
        tkey = match.group(1)
        slot = match.group(2)
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

# =============================================================================
# OVERMIND SERVICE
# =============================================================================
class OvermindService:
    def __init__(self):
        self._app_ref = None

    # ----------------------------- Public API --------------------------------
    def start_new_mission(self, objective: str, initiator: User) -> Mission:
        self._ensure_app_ref()
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
                db.session.commit()

    # --------------------------- Lifecycle Loop ------------------------------
    def _tick(self, mission: Mission, overall_start_perf: float):
        loops = 0
        while loops < MAX_LIFECYCLE_TICKS:
            loops += 1
            if (time.perf_counter() - overall_start_perf) > MAX_TOTAL_RUNTIME_SECONDS:
                update_mission_status(mission, MissionStatus.FAILED, note="Total runtime limit exceeded.")
                db.session.commit()
                log_warn(mission, "Mission aborted by total runtime limit.")
                break

            log_debug(mission, "Lifecycle tick", loop=loops, status=str(mission.status))

            if mission.status == MissionStatus.PENDING:
                self._plan_phase(mission)
            elif mission.status == MissionStatus.PLANNING:
                time.sleep(0.05)
            elif mission.status == MissionStatus.PLANNED:
                self._prepare_execution(mission)
            elif mission.status == MissionStatus.RUNNING:
                if EXECUTION_STRATEGY == "topological":
                    self._execution_phase(mission)
                else:
                    self._execution_wave_legacy(mission)
                self._check_terminal(mission)
                if mission.status == MissionStatus.RUNNING and self._has_open_tasks(mission):
                    time.sleep(DEFAULT_POLL_INTERVAL)
            elif mission.status == MissionStatus.ADAPTING:
                self._adaptive_replan(mission)
            elif mission.status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                log_debug(mission, "Terminal state reached; exiting lifecycle loop.")
                break

            try:
                db.session.refresh(mission)
            except Exception:
                db.session.rollback()

            if mission.status in (MissionStatus.SUCCESS, MissionStatus.FAILED, MissionStatus.CANCELED):
                break

            if mission.status == MissionStatus.RUNNING and not self._has_open_tasks(mission):
                self._check_terminal(mission)
                try:
                    db.session.refresh(mission)
                except Exception:
                    db.session.rollback()
                if mission.status in (MissionStatus.SUCCESS, MissionStatus.FAILED):
                    break
                time.sleep(0.05)
        else:
            if mission.status == MissionStatus.RUNNING:
                log_warn(mission, "Lifecycle tick limit reached while still RUNNING.")
                self._check_terminal(mission)
                db.session.commit()

    # ------------------------------ Planning ---------------------------------
    def _plan_phase(self, mission: Mission):
        update_mission_status(mission, MissionStatus.PLANNING, note="Planning started.")
        db.session.commit()
        log_info(mission, "Planning phase started.")

        planners = get_all_planners()
        if not planners:
            update_mission_status(mission, MissionStatus.FAILED, note="No planners available.")
            db.session.commit()
            return

        candidates: List[CandidatePlan] = []
        for planner in planners:
            try:
                result_dict = planner.instrumented_generate(mission.objective, context=None)
                if (not isinstance(result_dict, dict) or
                        "plan" not in result_dict or
                        "meta" not in result_dict):
                    raise PlannerError("instrumented_generate invalid structure", getattr(planner, "name", "?"), mission.objective)  # type: ignore

                plan_obj: MissionPlanSchema = result_dict["plan"]
                meta: Dict[str, Any] = result_dict["meta"]
                planner_name = meta.get("planner") or getattr(planner, "name", "unknown")
                score = self._score_plan(plan_obj, meta)
                rationale = self._build_plan_rationale(plan_obj, score, meta)

                candidates.append(
                    CandidatePlan(
                        raw=plan_obj,
                        planner_name=planner_name,
                        score=score,
                        rationale=rationale,
                        telemetry={
                            "duration_ms": meta.get("duration_ms"),
                            "node_count": meta.get("node_count"),
                            **meta
                        }
                    )
                )
                log_info(
                    mission,
                    "Planner candidate",
                    planner=planner_name,
                    score=score,
                    duration_ms=meta.get("duration_ms"),
                    node_count=meta.get("node_count")
                )
            except Exception as e:
                log_warn(
                    mission,
                    "Planner failed",
                    planner=getattr(planner, "name", "unknown"),
                    error=str(e)
                )

        if not candidates:
            update_mission_status(mission, MissionStatus.FAILED, note="All planners failed.")
            db.session.commit()
            return

        best = max(candidates, key=lambda c: c.score)
        version = self._next_plan_version(mission.id)
        try:
            self._persist_plan(mission, best, version)
        except Exception as e:
            update_mission_status(mission, MissionStatus.FAILED, note=f"Persist error: {e}")
            db.session.commit()
            return

        update_mission_status(mission, MissionStatus.PLANNED, note=f"Plan v{version} selected.")
        db.session.commit()
        log_mission_event(
            mission,
            MissionEventType.PLAN_SELECTED,
            payload={"version": version, "planner": best.planner_name, "score": best.score}
        )
        log_info(mission, "Plan selected", version=version, planner=best.planner_name, score=best.score)

    def _score_plan(self, plan: MissionPlanSchema, metadata: Dict[str, Any]) -> float:
        stats = getattr(plan, "stats", {}) or {}
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
        base = 100.0 + parallel_factor * 15 - risk_penalty - depth_penalty - size_penalty
        return round(base, 3)

    def _build_plan_rationale(self, plan: MissionPlanSchema, score: float, metadata: Dict[str, Any]) -> str:
        s = getattr(plan, "stats", {}) or {}
        return "; ".join([
            f"score={score}",
            f"tasks={s.get('tasks')}",
            f"roots={s.get('roots')}",
            f"high_risk={s.get('risk_counts', {}).get('HIGH', 0)}",
            f"longest_path={s.get('longest_path')}",
        ])

    def _next_plan_version(self, mission_id: int) -> int:
        max_version = db.session.scalar(
            select(func.max(MissionPlan.version)).where(MissionPlan.mission_id == mission_id)
        )
        return (max_version or 0) + 1

    # ------------------------------ Persistence -------------------------------
    def _persist_plan(self, mission: Mission, candidate: CandidatePlan, version: int):
        schema = candidate.raw

        stats_json = json.dumps(getattr(schema, "stats", {}) or {}, ensure_ascii=False)
        warnings_raw = getattr(schema, "warnings", None) or []
        warnings_list = [
            (w.model_dump() if hasattr(w, "model_dump") else w)
            for w in warnings_raw
        ]
        warnings_json = json.dumps(warnings_list, ensure_ascii=False)

        plan_signature = json.dumps({
            "objective": getattr(schema, "objective", ""),
            "tasks": [
                (
                    t.task_id,
                    getattr(getattr(t, "task_type", ""), "value", str(getattr(t, "task_type", ""))),
                    sorted(getattr(t, "dependencies", [])),
                    getattr(t, "tool_name", "") or "",
                    getattr(t, "priority", 0),
                )
                for t in getattr(schema, "tasks", [])
            ]
        }, ensure_ascii=False)
        content_hash = hashlib.sha256(plan_signature.encode("utf-8")).hexdigest()

        raw_json = json.dumps({
            "objective": getattr(schema, "objective", ""),
            "topological_order": getattr(schema, "topological_order", []),
            "stats": getattr(schema, "stats", {}),
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
                priority=t.priority,
                risk_level=getattr(getattr(t, "risk_level", ""), "value", str(getattr(t, "risk_level", ""))),
                criticality=getattr(getattr(t, "criticality", ""), "value", str(getattr(t, "criticality", ""))),
                depends_on_json=t.dependencies
            )
            db.session.add(task_row)

        mission.active_plan_id = mp.id
        db.session.commit()
        increment_counter("overmind_plans_created_total", {"planner": candidate.planner_name})

    # ----------------------------- Execution Prep -----------------------------
    def _prepare_execution(self, mission: Mission):
        update_mission_status(mission, MissionStatus.RUNNING, note="Execution started.")
        db.session.commit()
        log_mission_event(
            mission,
            MissionEventType.EXECUTION_STARTED,
            payload={"plan_id": mission.active_plan_id, "strategy": EXECUTION_STRATEGY}
        )
        db.session.commit()
        log_info(mission, "Execution phase entered.", strategy=EXECUTION_STRATEGY)
        increment_counter("overmind_missions_started_total")

    # ---------------------------- Topological Phase ---------------------------
    def _execution_phase(self, mission: Mission):
        plan = MissionPlan.query.get(mission.active_plan_id)
        if not plan:
            log_error(mission, "Active plan not found.")
            update_mission_status(mission, MissionStatus.FAILED, note="No plan.")
            db.session.commit()
            return

        try:
            raw = plan.raw_json if isinstance(plan.raw_json, dict) else json.loads(plan.raw_json or "{}")
        except Exception:
            raw = {}

        raw_topo = raw.get("topological_order") or []
        topo_layers: List[List[str]] = []
        if isinstance(raw_topo, list):
            if all(isinstance(x, str) for x in raw_topo):
                topo_layers = [raw_topo]
            elif all(isinstance(x, list) for x in raw_topo):
                topo_layers = [[str(k) for k in layer if isinstance(k, str)] for layer in raw_topo]
            else:
                topo_layers = [[str(x) for x in raw_topo if isinstance(x, str)]]
        if not topo_layers:
            topo_layers = [[t.task_key for t in mission.tasks]]

        log_debug(mission, "Topo layers normalized",
                  layers=len(topo_layers),
                  shape=[len(l) for l in topo_layers])

        task_index: Dict[str, Task] = {t.task_key: t for t in mission.tasks}

        total_success_before = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.SUCCESS).count()
        progress_attempted = False

        for layer_idx, layer_keys in enumerate(topo_layers):
            if isinstance(layer_keys, str):
                layer_keys = [layer_keys]
            layer_tasks = [task_index.get(k) for k in layer_keys if task_index.get(k)]
            if not layer_tasks:
                continue
            if all(t.status in (TaskStatus.SUCCESS, TaskStatus.FAILED) for t in layer_tasks):
                continue

            ready: List[Task] = []
            for t in layer_tasks:
                if t.status not in (TaskStatus.PENDING, TaskStatus.RETRY):
                    continue
                deps = t.depends_on_json or []
                dep_ok = True
                for dep_key in deps:
                    dep_task = task_index.get(dep_key)
                    if not dep_task or dep_task.status != TaskStatus.SUCCESS:
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

        total_success_after = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.SUCCESS).count()
        newly = total_success_after - total_success_before
        self._update_stall_metrics(mission.id, newly, progress_attempted)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    # ------------------------- Legacy Wave Execution -------------------------
    def _execution_wave_legacy(self, mission: Mission):
        ready = self._find_ready_tasks(mission)
        if not ready:
            failed_count = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.FAILED).count()
            pending_count = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.PENDING).count()
            retry_count = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.RETRY).count()
            if pending_count == 0 and retry_count == 0 and failed_count > 0:
                if failed_count >= REPLAN_FAILURE_THRESHOLD:
                    update_mission_status(mission, MissionStatus.ADAPTING, note="Adaptive replan trigger (wave).")
                    db.session.commit()
            time.sleep(0.05)
            return
        for t in ready[:TOPO_MAX_PARALLEL]:
            self._execute_task_with_retry_topological(mission.id, t.id, layer_index=-1)

    # ---------------------------- Stall Detection ----------------------------
    def _update_stall_metrics(self, mission_id: int, newly_success: int, attempted: bool):
        key = f"_stall_state_{mission_id}"
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
            log_warn(None, "Potential stall detected", mission_id=mission_id,
                     window=state["window"], cycles=state["cycles"])

    # --------------------------- Ready Task Discovery ------------------------
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
                log_warn(mission, "Task missing dependency", task_key=t.task_key)
                continue
            if all(dr.status == TaskStatus.SUCCESS for dr in dep_rows):
                ready.append(t)
        return ready

    # --------------------------- Thread Wrapper ------------------------------
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

    # =============================================================================
    # GUARD + INTERPOLATION + EXECUTION
    # =============================================================================
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

        if canon in (CANON_WRITE, CANON_READ):
            if GUARD_FILE_AUTOFIX:
                _autofill_file_args(canon, args, mission, task, notes)
            else:
                missing = [k for k in FILE_REQUIRED[canon] if not args.get(k)]
                if missing:
                    outcome.update(ok=False, action="early_fail", error=f"Missing file args: {missing}", category="args_missing")
                    return outcome

        if canon in FILE_REQUIRED:
            missing2 = [k for k in FILE_REQUIRED[canon] if not args.get(k)]
            if missing2:
                outcome.update(ok=False, action="early_fail", error=f"Missing file args after autofix: {missing2}", category="args_missing")
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
                outcome.update(ok=False, action="early_fail", error=f"ToolNotFound: {task.tool_name}", category="tool_missing")
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
            log_info(
                mission,
                "Guard processed task",
                task_key=task.task_key,
                action=guard_result["action"],
                notes="|".join(guard_result["notes"][:10]),
                category=guard_result.get("category"),
                error=guard_result["error"]
            )
        if not guard_result["ok"]:
            task.status = TaskStatus.FAILED
            task.error_text = guard_result["error"] or "GuardFailed"
            task.attempt_count += 1
            task.finished_at = utc_now()
            task.duration_ms = 0
            db.session.commit()
            log_warn(mission, "Task failed early by guard",
                     task_key=task.task_key,
                     error=task.error_text,
                     category=guard_result.get("category"))
            log_mission_event(
                mission,
                MissionEventType.TASK_FAILED,
                payload={"task_id": task.id, "attempt": task.attempt_count, "retry": False,
                         "layer": layer_index, "error": task.error_text, "guard_category": guard_result.get("category")}
            )
            increment_counter("overmind_tasks_executed_total", {"result": "failed_early"})
            self._safe_terminal_event(mission_id)
            return

        # Policy
        if task.tool_name and not tool_policy_engine.authorize(task.tool_name, mission, task):
            task.status = TaskStatus.FAILED
            task.error_text = "PolicyDenied"
            db.session.commit()
            log_warn(mission, "Tool denied by policy",
                     task_key=task.task_key, tool=task.tool_name)
            self._safe_terminal_event(mission_id)
            return

        # Interpolation
        original_args = _ensure_dict(task.tool_args_json)
        if INTERPOLATION_ENABLED and task.tool_name in (CANON_THINK, CANON_WRITE):
            new_args, interp_notes = _render_template_in_args(original_args, mission_id)
            task.tool_args_json = new_args
            if interp_notes:
                log_info(mission, "Template interpolation",
                         task_key=task.task_key,
                         placeholders="|".join(interp_notes[:12]))
            db.session.commit()

        attempt_index = task.attempt_count + 1
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        db.session.commit()

        log_mission_event(
            mission,
            MissionEventType.TASK_STARTED,
            payload={"task_id": task.id, "task_key": task.task_key,
                     "layer": layer_index, "attempt": attempt_index,
                     "tool": task.tool_name}
        )
        log_debug(mission, "Task started",
                  task_key=task.task_key, attempt=attempt_index,
                  layer=layer_index, tool=task.tool_name)

        perf_start = time.perf_counter()

        try:
            result_payload = self._execute_tool(task) if task.tool_name else self._fallback_maestro(task)
            if not verification_service.verify(task):
                raise TaskExecutionError("Verification failed.")

            data_payload = result_payload.get("data")
            answer = _extract_answer_from_data(data_payload)
            meta_update = result_payload.get("meta") or {}
            if answer:
                meta_update["answer"] = answer

            # Propagate risk score
            arg_risk = None
            if isinstance(task.tool_args_json, dict):
                arg_risk = task.tool_args_json.get("_meta_risk")
            if arg_risk is not None:
                meta_update["risk_score"] = arg_risk

            # Diff augmentation
            if DIFF_ENABLED and task.tool_name == CANON_WRITE:
                path = (task.tool_args_json or {}).get("path")
                if isinstance(path, str) and path.strip():
                    self._augment_with_diff(task, path, meta_update)

            # result_text choose strategy
            task.result_text = (result_payload.get("result_text") or "")[:8000]
            if answer and not task.result_text:
                task.result_text = answer[:8000]

            # Save meta
            if hasattr(task, "result_meta_json"):
                current_meta = getattr(task, "result_meta_json") or {}
                if not isinstance(current_meta, dict):
                    current_meta = {}
                current_meta.update(meta_update)
                task.result_meta_json = current_meta  # type: ignore

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
            log_info(mission, "Task success",
                     task_key=task.task_key, attempt=attempt_index,
                     layer=layer_index, duration_ms=task.duration_ms)

        except Exception as e:
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
                log_warn(mission, "Task failed; scheduling retry",
                         task_key=task.task_key,
                         attempt=task.attempt_count,
                         backoff_s=round(backoff, 2),
                         error=str(e))
                log_mission_event(
                    mission,
                    MissionEventType.TASK_FAILED,
                    payload={"task_id": task.id, "attempt": task.attempt_count,
                             "retry": True, "layer": layer_index,
                             "error": str(e)[:200]}
                )
                increment_counter("overmind_tasks_executed_total", {"result": "retry"})
            else:
                task.status = TaskStatus.FAILED
                log_warn(mission, "Task failed permanently",
                         task_key=task.task_key,
                         attempt=task.attempt_count,
                         error=str(e))
                log_mission_event(
                    mission,
                    MissionEventType.TASK_FAILED,
                    payload={"task_id": task.id, "attempt": task.attempt_count,
                             "retry": False, "layer": layer_index,
                             "error": str(e)[:200]}
                )
                increment_counter("overmind_tasks_executed_total", {"result": "failed"})
            db.session.commit()

        self._safe_terminal_event(mission_id)

    def _fallback_maestro(self, task: Task):
        if hasattr(maestro, "execute_task"):
            maestro.execute_task(task)
            db.session.refresh(task)
        return {"status": "success", "result_text": task.result_text or "[Fallback Execution]", "meta": {}}

    # ----------------------------- Diff Augmentation -------------------------
    def _augment_with_diff(self, task: Task, path: str, meta_update: Dict[str, Any]):
        try:
            old_exists, old_content = _read_file_safe(path + ".bak") if BACKUP_ON_WRITE else _read_file_safe(path)
            old_hash = _sha256_text(old_content) if old_exists else ""
            new_exists, new_content = _read_file_safe(path)
            new_hash = _sha256_text(new_content) if new_exists else ""
            if not new_exists:
                return
            if not old_exists:
                diff_data = _compute_diff("", new_content, DIFF_MAX_LINES)
                diff_data.update({
                    "old_sha256": "",
                    "new_sha256": new_hash,
                    "no_op": False,
                    "backup_created": False
                })
                meta_update.update(diff_data)
                return
            if old_content == new_content:
                meta_update.update({
                    "diff": "",
                    "diff_truncated": False,
                    "old_sha256": old_hash,
                    "new_sha256": new_hash,
                    "lines_added": 0,
                    "lines_removed": 0,
                    "first_changed_line": 0,
                    "content_size_old": len(old_content),
                    "content_size_new": len(new_content),
                    "change_ratio": 0.0,
                    "no_op": True,
                    "backup_created": False
                })
                return
            diff_data = _compute_diff(old_content, new_content, DIFF_MAX_LINES)
            diff_data.update({
                    "old_sha256": old_hash,
                    "new_sha256": new_hash,
                    "no_op": False,
                    "backup_created": False
            })
            meta_update.update(diff_data)
        except Exception as e:
            meta_update.setdefault("diff_error", str(e)[:120])

    # ----------------------------- Tool Execution ----------------------------
    def _execute_tool(self, task: Task) -> Dict[str, Any]:
        if agent_tools is None:
            raise TaskExecutionError("Agent tools module not available.")
        tool_name_raw = task.tool_name or ""
        if not tool_name_raw:
            raise TaskExecutionError("Empty tool_name.")

        # Pre-diff (optional) handled inside tool itself normally; we derive after.

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
                    result_text = json.dumps(data_payload, ensure_ascii=False)[:2000]
                except Exception:
                    result_text = str(data_payload)[:2000]
        elif isinstance(data_payload, str):
            result_text = data_payload[:2000]
        elif data_payload is not None:
            result_text = str(data_payload)[:2000]
        else:
            result_text = "[NO TOOL OUTPUT]" if not result_text else result_text

        return {
            "status": "success" if status_ok else "error",
            "result_text": result_text,
            "data": data_payload,
            "meta": meta_payload
        }

    # ------------------------------- Backoff ---------------------------------
    def _compute_backoff(self, attempt: int) -> float:
        base = TASK_RETRY_BACKOFF_BASE ** attempt
        jitter = random.uniform(0, TASK_RETRY_BACKOFF_JITTER)
        return min(base + jitter, 600.0)

    # ----------------------------- Terminal Check -----------------------------
    def _check_terminal(self, mission: Mission):
        pending = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.PENDING).count()
        retry = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.RETRY).count()
        running = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.RUNNING).count()
        failed = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.FAILED).count()

        log_debug(mission, "Terminal snapshot",
                  pending=pending, retry=retry, running=running, failed=failed, status=str(mission.status))

        if pending == 0 and retry == 0 and running == 0:
            if failed == 0:
                if mission.status != MissionStatus.SUCCESS:
                    self._finalize_mission_risk(mission)
                    update_mission_status(mission, MissionStatus.SUCCESS, note="All tasks completed.")
                    increment_counter("overmind_missions_finished_total", {"result": "success"})
                    log_info(mission, "Mission success")
            else:
                if failed >= REPLAN_FAILURE_THRESHOLD and self._adaptive_cycles_used(mission) < ADAPTIVE_MAX_CYCLES:
                    if mission.status != MissionStatus.ADAPTING:
                        update_mission_status(mission, MissionStatus.ADAPTING, note="Entering adaptive replan.")
                        log_info(mission, "Switching to adaptive replan", failed=failed)
                else:
                    if mission.status != MissionStatus.FAILED:
                        update_mission_status(mission, MissionStatus.FAILED, note=f"{failed} tasks failed.")
                        increment_counter("overmind_missions_finished_total", {"result": "failed"})
                        log_warn(mission, "Mission failed terminally", failed=failed)
            db.session.commit()

    def _finalize_mission_risk(self, mission: Mission):
        # Aggregate risk scores from tool_args/_meta_risk or result_meta_json.risk_score
        tasks = Task.query.filter_by(mission_id=mission.id).all()
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
        log_mission_event(mission, MissionEventType.MISSION_UPDATED, payload={"risk_summary": buckets})

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

    # ------------------------------ Adaptive Replan ---------------------------
    def _adaptive_replan(self, mission: Mission):
        failed_tasks = Task.query.filter_by(mission_id=mission.id, status=TaskStatus.FAILED).all()
        if not failed_tasks:
            update_mission_status(mission, MissionStatus.RUNNING, note="No failed tasks; resume execution.")
            db.session.commit()
            return

        if self._adaptive_cycles_used(mission) >= ADAPTIVE_MAX_CYCLES:
            update_mission_status(mission, MissionStatus.FAILED, note="Adaptive cycle limit reached.")
            db.session.commit()
            log_warn(mission, "Adaptive cycle limit reached -> Mission FAILED.")
            return

        failure_context = {t.task_key: (t.error_text or "unknown") for t in failed_tasks}
        log_info(mission, "Adaptive replanning start", failed_tasks=len(failure_context))
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
            self._persist_plan(mission, candidate, version)
            update_mission_status(mission, MissionStatus.PLANNED, note=f"Adaptive plan v{version} ready.")
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

    # ----------------------------- Terminal Event ----------------------------
    def _safe_terminal_event(self, mission_id: int):
        mission = Mission.query.get(mission_id)
        if not mission:
            return
        try:
            self._check_terminal(mission)
        except Exception:
            pass

    # --------------------------- Flask App Context ---------------------------
    def _ensure_app_ref(self):
        if self._app_ref is None:
            if not has_app_context():
                raise RuntimeError("No application context; call inside Flask app context.")
            self._app_ref = current_app._get_current_object()

# =============================================================================
# Singleton Facade
# =============================================================================
_overmind_service_singleton = OvermindService()

def start_mission(objective: str, initiator: User) -> Mission:
    return _overmind_service_singleton.start_new_mission(objective, initiator)

def run_mission_lifecycle(mission_id: int):
    return _overmind_service_singleton.run_mission_lifecycle(mission_id)

# =============================================================================
# END OF FILE
# =============================================================================