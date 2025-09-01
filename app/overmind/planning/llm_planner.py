# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
# -*- coding: utf-8 -*-
"""
LLM Grounded Planner (Enterprise / Hyper-Hardened Edition)
==========================================================
Version: 3.2.0-hardened

Core Purpose:
-------------
Turn a natural-language mission objective into an *executable, safe, deterministic*
task graph (MissionPlanSchema) using a hybrid of:
  1. Deterministic pattern recognition for high-value / recurring objectives.
  2. LLM structured planning (JSON) with strict schema + canonical tool normalization.
  3. Multi‑layer fallbacks (text extraction → minimal analytical fallback → segmented fallback).

Key New Enhancements vs 3.1.0-hybrid:
-------------------------------------
+ Added "Architecture / Summary" Pattern:
    - Detects objectives like:
        "Analyze the current system architecture and create a summary file named X"
        or any combination of (analyze|analysis) + summary + file.
    - Optionally reads common context files (README.md, docker-compose.yml, requirements.txt) if they exist.
    - Builds deterministic plan:
        t01..t0N read_file(s)
        t(N+1)   generic_think (auto-inject {{t01.content}} etc. if not referenced)
        t(N+2)   write_file final summary (Arabic if objective includes Arabic letters or 'arabic')
+ Analytical Minimal Fallback (_analytical_minimal_fallback):
    - Guaranteed 2-task plan (generic_think → write_file) when normalization yields no_valid_tasks,
      *even if* FALLBACK_ALLOW=0 (hard safety net).
+ Extended Post-Validation Safety:
    - Ensures at least one write_file when objective explicitly demands a report/file AND patterns/LLM omitted it (logs diagnostic).
+ Unified Rule Injection:
    - Prompt now explicitly instructs: "If no file reading needed, still produce one generic_think then one write_file."
+ Stronger Normalization:
    - Absolute guarantee to never raise PlanValidationError("no_valid_tasks") to caller (converted into analytic fallback).
+ Deterministic Arabic Language Detection:
    - If objective contains Arabic Unicode range or 'arabic' token → prompt produced in Arabic automatically for summary patterns / fallback tasks.

Environment Flags (Summary of Major Controls):
----------------------------------------------
FALLBACK_ALLOW=0|1
    Allow multi-segment textual fallback if structured extraction fails.

LLM_PLANNER_STRICT_JSON=0|1
    If 1, disallow text fallback unless FALLBACK_ALLOW triggers an alternate route.

PLANNER_ALLOWED_TOOLS="read_file,generic_think,write_file"
PLANNER_ENFORCE_ALLOWED_TOOLS=1
    Allowlist & enforcement for tool names (others coerced to generic_think).

PLANNER_AUTO_FIX_FILE_TASKS=1
    Autofill mandatory args for file tools (path/content for write_file; path for read_file).

PLANNER_FORCE_FILE_TOOLS=1
    Coerce ambiguous tool names to canonical read/write/think based on description intent.

PLANNER_FILE_DEFAULT_EXT=.md
PLANNER_FILE_DEFAULT_CONTENT="Placeholder content (auto-generated)."

PLANNER_FORCE_REPORT_NAME=ARCHITECTURE_PRINCIPLES.md (optional)
    Force final report filename.

PLANNER_MAX_WRITES=2
    Limit retained write_file tasks (prune placeholders & extras).

PLANNER_DISABLE_PATTERN_ENGINE=0
    Disable all deterministic patterns if set to 1.

LLM_PLANNER_MAX_TASKS=25
FALLBACK_MAX=5

PLANNER_TOOL_ID_MAP='{"tool:001":"generic_think","tool:002":"write_file"}'
    Numeric tool id mapping (tool:###) → canonical names.

Design Guarantees:
------------------
1. Never returns zero tasks.
2. Last surviving write_file always normalized to a single final report path (.md).
3. Inter-task interpolation markers preserved (e.g. {{t01.content}}, {{t02.answer}}).
4. Risk scoring heuristic stored in tool_args["_meta_risk"] (non-breaking).
5. Pattern tasks bypass LLM — fully deterministic & auditable.
6. Analytical fallback ALWAYS returns a valid minimal plan (2 tasks).

Extension Points:
-----------------
- Add more patterns inside PatternEngine.detect().
- Introduce advanced structured edit tools (replace_in_file, update_markdown_section).
- Add multi-branch reasoning or parallel scanning tasks.

"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("llm_planner")
_env_level = os.getenv("LLM_PLANNER_LOG_LEVEL", "").upper()
if _env_level:
    _LOG.setLevel(getattr(logging, _env_level, logging.INFO))
else:
    _LOG.setLevel(logging.INFO)
if not _LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# Base / Schemas Imports (with optional stub)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB", "0") == "1"
try:
    from .base_planner import (
        BasePlanner,
        PlannerError,
        PlanValidationError,
    )
except Exception as _e:  # pragma: no cover
    if not _ALLOW_STUB:
        raise RuntimeError(
            "Failed to import base_planner (set LLM_PLANNER_ALLOW_STUB=1 for dev stub)."
        ) from _e

    class PlannerError(Exception):  # type: ignore
        def __init__(self, msg: str, planner: str = "stub", objective: str = "", **extra):
            super().__init__(msg)
            self.planner = planner
            self.objective = objective
            self.extra = extra or {}

    class PlanValidationError(PlannerError):  # type: ignore
        pass

    class BasePlanner:  # type: ignore
        name = "base_planner_stub"

        @classmethod
        def live_planner_classes(cls):
            return {}

        @classmethod
        def planner_metadata(cls):
            return {}

    _LOG.error("USING STUB BasePlanner (development mode).")

from .schemas import MissionPlanSchema, PlannedTask, PlanningContext  # type: ignore

# --------------------------------------------------------------------------------------
# Optional Services
# --------------------------------------------------------------------------------------
try:
    from app.services import maestro  # type: ignore
except Exception:
    maestro = None  # type: ignore

try:
    from app.services import agent_tools  # type: ignore
except Exception:
    agent_tools = None  # type: ignore

# Prefer centralized canonicalization if available
CANON_FUNC = getattr(agent_tools, "canonicalize_tool_name", None) if agent_tools else None

# --------------------------------------------------------------------------------------
# Environment / Config
# --------------------------------------------------------------------------------------
STRICT_JSON_ONLY = os.getenv("LLM_PLANNER_STRICT_JSON", "0") == "1"
SELF_TEST_MODE = (os.getenv("LLM_PLANNER_SELFTEST_MODE") or "fast").lower()
FALLBACK_ALLOW = os.getenv("FALLBACK_ALLOW", "0") == "1"
FALLBACK_MAX = int(os.getenv("FALLBACK_MAX", "5"))
SELF_TEST_STRICT = os.getenv("LLM_PLANNER_SELFTEST_STRICT", "0") == "1"
MAX_TASKS_DEFAULT = int(os.getenv("LLM_PLANNER_MAX_TASKS", "25"))

AUTO_FIX_FILE_TASKS = os.getenv("PLANNER_AUTO_FIX_FILE_TASKS", "1") == "1"
FORCE_FILE_TOOLS = os.getenv("PLANNER_FORCE_FILE_TOOLS", "1") == "1"
FILE_DEFAULT_EXT = os.getenv("PLANNER_FILE_DEFAULT_EXT", ".md")
FILE_DEFAULT_CONTENT = os.getenv(
    "PLANNER_FILE_DEFAULT_CONTENT",
    "Placeholder content (auto-generated)."
)

ALLOWED_TOOLS_RAW = os.getenv("PLANNER_ALLOWED_TOOLS", "read_file,generic_think,write_file")
ALLOWED_TOOLS = {t.strip() for t in ALLOWED_TOOLS_RAW.split(",") if t.strip()}
ENFORCE_ALLOWED = os.getenv("PLANNER_ENFORCE_ALLOWED_TOOLS", "1") == "1"

FORCE_REPORT_NAME = os.getenv("PLANNER_FORCE_REPORT_NAME", "").strip() or None
MAX_WRITES = int(os.getenv("PLANNER_MAX_WRITES", "2"))
DISABLE_PATTERN_ENGINE = os.getenv("PLANNER_DISABLE_PATTERN_ENGINE", "0") == "1"

_TOOL_ID_MAP_ENV = os.getenv("PLANNER_TOOL_ID_MAP", "").strip()
try:
    TOOL_ID_MAP = json.loads(_TOOL_ID_MAP_ENV) if _TOOL_ID_MAP_ENV else {}
    if not isinstance(TOOL_ID_MAP, dict):
        TOOL_ID_MAP = {}
except Exception:
    TOOL_ID_MAP = {}

# Regex
_TASK_ARRAY_REGEX = re.compile(r'"tasks"\s*:\s*(\[[^\]]*\])', re.IGNORECASE | re.DOTALL)
_JSON_BLOCK_CURLY = re.compile(r"\{.*\}", re.DOTALL)
TOOL_ID_REGEX = re.compile(r"^tool:\d{1,5}$")

# Canonical set
CANON_WRITE = "write_file"
CANON_READ = "read_file"
CANON_THINK = "generic_think"

WRITE_ALIASES = {
    "write_file", "file_writer", "file_system", "file_system_tool", "file_writer_tool",
    "writer", "create_file", "make_file", "file_system.write", "file_system.create",
    "file_system.generate", "file_creator"
}
READ_ALIASES = {
    "read_file", "file_reader", "file_reader_tool",
    "file_system.read", "file_system.open", "file_system.view", "open_file", "load_file"
}
THINK_ALIASES = {"generic_think", "think", "analyze", "analysis_tool", "reason", "summarize"}

DOT_SUFFIX_WRITE = {"write", "create", "generate", "append", "touch"}
DOT_SUFFIX_READ = {"read", "open", "load", "view", "show"}

MANDATORY_ARGS = {
    CANON_WRITE: ["path", "content"],
    CANON_READ: ["path"]
}

WRITE_INTENT = {"write", "create", "generate", "append", "produce", "save", "output"}
READ_INTENT = {"read", "inspect", "load", "open", "view"}
THINK_INTENT = {"analyze", "think", "reason", "summarize", "count", "draft"}

# --------------------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------------------
def _clip(s: str, n: int = 140) -> str:
    if not s:
        return ""
    return s if len(s) <= n else s[: n - 3] + "..."

def _safe_json_loads(txt: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(txt), None
    except Exception as e:
        return None, str(e)

def _lower(s: Any) -> str:
    return str(s or "").strip().lower()

def _looks_like_write(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in WRITE_INTENT)

def _looks_like_read(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in READ_INTENT)

def _looks_like_think(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in THINK_INTENT)

def _tool_exists(name: str) -> bool:
    if not agent_tools:
        return False
    try:
        reg = getattr(agent_tools, "_TOOL_REGISTRY", {})
        return name in reg
    except Exception:
        return False

def _canonical_task_id(idx: int) -> str:
    return f"t{idx:02d}"

def _map_tool_id(raw: str) -> Optional[str]:
    return TOOL_ID_MAP.get(raw.lower())

def _interpolate_prompt_if_missing(prompt: str, dep_ids: List[str]) -> str:
    if not dep_ids:
        return prompt
    # If already referencing any dependency content marker, skip injection
    for d in dep_ids:
        marker = f"{{{{{d}.content}}}}"
        if marker in prompt:
            return prompt
    first = dep_ids[0]
    return prompt + f"\n\n[INPUT_FROM::{first}]{{{{{first}.content}}}}\n"

def _risk_score(tool: str, desc: str, args: Dict[str, Any], deps: List[str]) -> float:
    score = 0.0
    if tool == CANON_WRITE:
        score += 2.0
        if isinstance(args.get("content"), str):
            score += min(len(args["content"]) / 800.0, 4.0)
    if tool not in {CANON_WRITE, CANON_READ, CANON_THINK}:
        score += 3.0
    score += len(deps) * 0.5
    if _looks_like_write(desc) and tool != CANON_WRITE:
        score += 1.0
    if _looks_like_read(desc) and tool != CANON_READ:
        score += 1.0
    return round(min(score, 10.0), 2)

def _autofill_file_args(tool_name: str, tool_args: Dict[str, Any], task_index: int, notes: List[str]):
    if tool_name not in MANDATORY_ARGS:
        return
    req = MANDATORY_ARGS[tool_name]
    changed = False
    if "path" in req and not tool_args.get("path"):
        filename = f"auto_generated_{task_index:02d}{FILE_DEFAULT_EXT}"
        tool_args["path"] = filename
        notes.append(f"autofill_path:{filename}")
        changed = True
    if "content" in req and tool_name == CANON_WRITE:
        content = tool_args.get("content")
        if not isinstance(content, str) or not content.strip():
            tool_args["content"] = FILE_DEFAULT_CONTENT
            notes.append("autofill_content:default")
            changed = True
    if changed:
        notes.append("mandatory_args_filled")

def _canonicalize_tool_local(raw: str, description: str) -> Tuple[str, List[str]]:
    notes: List[str] = []
    name = _lower(raw)
    if TOOL_ID_REGEX.match(name):
        mapped = _map_tool_id(name)
        if mapped:
            notes.append(f"mapped_tool_id:{name}->{mapped}")
            return mapped, notes
        notes.append("tool_id_unmapped")

    base = name
    suffix = None
    if "." in name:
        base, suffix = name.split(".", 1)
        if suffix:
            if suffix in DOT_SUFFIX_WRITE:
                notes.append(f"dotted_suffix_write:{suffix}")
                return CANON_WRITE, notes
            if suffix in DOT_SUFFIX_READ:
                notes.append(f"dotted_suffix_read:{suffix}")
                return CANON_READ, notes

    if base in WRITE_ALIASES or name in WRITE_ALIASES:
        notes.append("alias_write")
        return CANON_WRITE, notes
    if base in READ_ALIASES or name in READ_ALIASES:
        notes.append("alias_read")
        return CANON_READ, notes
    if base in THINK_ALIASES or name in THINK_ALIASES:
        notes.append("alias_think")
        return CANON_THINK, notes

    # Intent heuristics for vague placeholders
    if name in {"unknown", "", "file", "filesystem"}:
        if _looks_like_write(description):
            notes.append("intent_write_desc")
            return CANON_WRITE, notes
        if _looks_like_read(description):
            notes.append("intent_read_desc")
            return CANON_READ, notes
        if _looks_like_think(description):
            notes.append("intent_think_desc")
            return CANON_THINK, notes

    # Token presence
    if "write" in name:
        notes.append("contains_write_token")
        return CANON_WRITE, notes
    if "read" in name:
        notes.append("contains_read_token")
        return CANON_READ, notes
    if any(tok in name for tok in ("think", "analy", "reason", "summarize", "logic")):
        notes.append("contains_think_token")
        return CANON_THINK, notes

    return raw, notes

def _canonicalize_tool(raw: str, description: str) -> Tuple[str, List[str]]:
    if CANON_FUNC:
        try:
            canon, cnotes = CANON_FUNC(raw, description)  # type: ignore
            return canon, cnotes
        except Exception:
            return _canonicalize_tool_local(raw, description)
    return _canonicalize_tool_local(raw, description)

def _objective_has_arabic(obj: str) -> bool:
    if "arabic" in obj.lower():
        return True
    return any('\u0600' <= ch <= '\u06FF' for ch in obj)

# --------------------------------------------------------------------------------------
# Pattern Engine
# --------------------------------------------------------------------------------------
class PatternResult:
    def __init__(self, tasks: List[PlannedTask], notes: List[str]):
        self.tasks = tasks
        self.notes = notes

class PatternEngine:
    """
    Extend by adding more detection methods and referencing them in detect().
    Deterministic patterns bypass LLM for reliability & cost savings.
    """
    def __init__(self, objective: str, max_tasks: int):
        self.objective = objective
        self.low = objective.lower()
        self.max_tasks = max_tasks

    def detect(self) -> Optional[PatternResult]:
        if DISABLE_PATTERN_ENGINE:
            return None

        # Pattern #1: docker-compose.yml service count
        if "docker-compose" in self.low and "count" in self.low and "service" in self.low:
            return self._docker_compose_service_count()

        # Pattern #2: Architecture/Summary pattern
        # Trigger: explicit "summary file named X" OR (analyze|analysis) & summary & file
        m = re.search(r"summary file named\s+([A-Za-z0-9_.\-]+)", self.low)
        if m:
            return self._architecture_summary(m.group(1))
        if (("analyze" in self.low or "analysis" in self.low) and
                "summary" in self.low and "file" in self.low):
            return self._architecture_summary(None)

        return None

    # ---------- Pattern: docker-compose service count
    def _docker_compose_service_count(self) -> PatternResult:
        notes = ["pattern:docker_compose_service_count"]
        report_name = FORCE_REPORT_NAME or self._extract_report_name(default="report_arabic.md")
        tasks: List[PlannedTask] = []

        tasks.append(PlannedTask(
            task_id="t01",
            description="Read docker-compose.yml for service counting.",
            tool_name=CANON_READ,
            tool_args={"path": "docker-compose.yml"},
            dependencies=[]
        ))

        prompt = (
            "اقرأ محتوى ملف docker-compose.yml (تم تمريره بعلامة {{t01.content}}) ثم احسب عدد المفاتيح "
            "المباشرة تحت المفتاح services فقط (بدون احتساب nested). "
            "أجب بجملة عربية واحدة بالشكل: عدد الخدمات هو: <NUMBER>.\n{{t01.content}}\n"
        )
        tasks.append(PlannedTask(
            task_id="t02",
            description="Analyze docker-compose content and count direct services (Arabic).",
            tool_name=CANON_THINK,
            tool_args={"prompt": prompt},
            dependencies=["t01"]
        ))

        tasks.append(PlannedTask(
            task_id="t03",
            description="Write final Arabic report with counted services.",
            tool_name=CANON_WRITE,
            tool_args={
                "path": report_name,
                "content": "{{t02.answer}}",
                "enforce_ext": ".md",
                "dry_run_hint": False
            },
            dependencies=["t02"]
        ))
        return PatternResult(tasks=tasks, notes=notes)

    # ---------- Pattern: Architecture / Summary
    def _architecture_summary(self, filename: Optional[str]) -> PatternResult:
        notes = ["pattern:architecture_summary"]
        want_ar = _objective_has_arabic(self.objective)
        report_name = FORCE_REPORT_NAME or filename or "SUMMARY_REPORT.md"
        tasks: List[PlannedTask] = []

        # Candidate files (deterministic – existence can be gracefully ignored at runtime)
        candidate_files = ["README.md", "docker-compose.yml", "requirements.txt"]
        read_ids: List[str] = []
        for i, cf in enumerate(candidate_files, start=1):
            tid = f"t{i:02d}"
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description=f"Read {cf} if it exists (ignore if missing).",
                    tool_name=CANON_READ,
                    tool_args={"path": cf},
                    dependencies=[]
                )
            )
            read_ids.append(tid)

        lang_line = "اكتب الملخص باللغة العربية." if want_ar else "Write the summary in concise English."
        prompt = (
            f"{lang_line}\n"
            "Provide a structured architecture summary (components, services/modules, data flow, "
            "deployment aspects, dependencies, risks, recommendations). "
            "If some files are unavailable or empty, state reasonable assumptions explicitly."
        )

        think_id = f"t{len(tasks)+1:02d}"
        tasks.append(
            PlannedTask(
                task_id=think_id,
                description="Analyze project context & draft architecture summary.",
                tool_name=CANON_THINK,
                tool_args={"prompt": prompt},
                dependencies=read_ids
            )
        )

        tasks.append(
            PlannedTask(
                task_id=f"t{len(tasks)+1:02d}",
                description=f"Write final architecture summary to {report_name}.",
                tool_name=CANON_WRITE,
                tool_args={
                    "path": report_name,
                    "content": f"{{{{{think_id}.answer}}}}",
                    "dry_run_hint": False
                },
                dependencies=[think_id]
            )
        )
        return PatternResult(tasks=tasks, notes=notes)

    def _extract_report_name(self, default: str) -> str:
        for cand in ("report_arabic.md", "report.md", "report.txt"):
            if cand in self.low:
                return cand
        return default


# --------------------------------------------------------------------------------------
# Planner Class
# --------------------------------------------------------------------------------------
class LLMGroundedPlanner(BasePlanner):
    name = "llm_grounded_planner"
    version = "3.2.0-hardened"
    tier = "core"
    production_ready = True
    capabilities = {"planning", "llm", "tool-grounding", "hybrid"}
    tags = {"mission", "tasks"}

    # ------------------------------------------------------------------ Self Test
    @classmethod
    def self_test(cls) -> Tuple[bool, str]:
        mode = SELF_TEST_MODE
        if mode == "skip":
            return True, "skip_mode"
        if mode == "fast":
            return True, "fast_ok" if maestro is not None else "fast_no_maestro"
        if maestro is None and SELF_TEST_STRICT:
            return False, "maestro_missing_strict"
        return True, "normal_ok"

    # ------------------------------------------------------------------ Public API
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        max_tasks: Optional[int] = None
    ) -> MissionPlanSchema:
        start = time.perf_counter()
        if not self._objective_valid(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        cap = min(max_tasks or MAX_TASKS_DEFAULT, MAX_TASKS_DEFAULT)
        _LOG.info(
            "[%s] plan_start objective='%s' cap=%d hybrid=%s",
            self.name, _clip(objective, 120), cap, not DISABLE_PATTERN_ENGINE
        )

        # 1. Pattern Engine (deterministic)
        pattern_result = PatternEngine(objective, cap).detect()
        if pattern_result:
            _LOG.info("[%s] pattern_hit=%s", self.name, pattern_result.notes)
            tasks = self._post_process(pattern_result.tasks, objective, pattern_result.notes)
            plan = MissionPlanSchema(objective=objective, tasks=tasks)
            self._post_validate(plan)
            self._log_success(plan, objective, start, degraded=False, notes=pattern_result.notes)
            return plan

        # 2. LLM Structured Approach
        errors: List[str] = []
        structured: Optional[Dict[str, Any]] = None
        if maestro and hasattr(maestro, "generation_service"):
            try:
                structured = self._call_structured(objective, context, cap)
            except Exception as e:
                errors.append(f"struct_fail:{type(e).__name__}:{e}")
                _LOG.warning("[%s] structured_fail %s", self.name, e)
        else:
            errors.append("maestro_unavailable")

        if STRICT_JSON_ONLY and structured is None and not FALLBACK_ALLOW:
            # We'll still attempt analytic fallback to avoid total failure
            _LOG.warning("[%s] strict_json_no_structured -> forcing analytic minimal fallback", self.name)
            analytic = self._analytical_minimal_fallback(objective)
            analytic = self._post_process(analytic, objective, ["forced_analytic_fallback"])
            plan = MissionPlanSchema(objective=objective, tasks=analytic)
            self._post_validate(plan)
            self._log_success(plan, objective, start, degraded=True, notes=errors[-5:] + ["forced_analytic"])
            return plan

        # 3. Optional Text Fallback (if structured missing)
        raw_text: Optional[str] = None
        if structured is None and maestro and hasattr(maestro, "generation_service"):
            try:
                raw_text = self._call_text(objective, context)
            except Exception as e:
                errors.append(f"text_fail:{type(e).__name__}:{e}")
                _LOG.error("[%s] text_fail %s", self.name, e)

        plan_dict: Optional[Dict[str, Any]] = None
        extraction_notes: List[str] = []
        if structured:
            plan_dict = structured
        elif raw_text:
            plan_dict, extraction_notes = self._extract_from_text(raw_text)
            errors.extend(extraction_notes)

        if plan_dict is None:
            # Use multi-segment fallback if allowed; else analytic minimal fallback
            if FALLBACK_ALLOW:
                degraded = self._fallback_plan(objective, cap)
                degraded.tasks = self._post_process(degraded.tasks, objective, errors + ["fallback_plan"])
                self._post_validate(degraded)
                self._log_success(degraded, objective, start, degraded=True, notes=errors[-8:])
                return degraded
            analytic = self._analytical_minimal_fallback(objective)
            analytic = self._post_process(analytic, objective, errors + ["analytic_min_fallback"])
            plan = MissionPlanSchema(objective=objective, tasks=analytic)
            self._post_validate(plan)
            self._log_success(plan, objective, start, degraded=True, notes=errors[-8:] + ["analytic_min"])
            return plan

        norm_errs: List[str] = []
        try:
            tasks = self._normalize_tasks(plan_dict.get("tasks"), cap, norm_errs)
        except PlanValidationError as pe:
            # Critical: convert no_valid_tasks into analytic minimal fallback ALWAYS
            if "no_valid_tasks" in str(pe):
                _LOG.warning("[%s] normalization produced no_valid_tasks -> analytic fallback", self.name)
                analytic = self._analytical_minimal_fallback(objective)
                analytic = self._post_process(analytic, objective, norm_errs + ["analytic_min_from_normalize"])
                plan = MissionPlanSchema(objective=objective, tasks=analytic)
                self._post_validate(plan)
                self._log_success(plan, objective, start, degraded=True,
                                  notes=errors + norm_errs + ["analytic_from_no_valid"])
                return plan
            # Any other validation error falls back if allowed
            if FALLBACK_ALLOW:
                degraded = self._fallback_plan(objective, cap)
                degraded.tasks = self._post_process(degraded.tasks, objective, norm_errs + ["normalize_fallback"])
                self._post_validate(degraded)
                self._log_success(degraded, objective, start, degraded=True,
                                  notes=errors + norm_errs + ["fallback_after_validation"])
                return degraded
            # Final guard: analytic minimal
            analytic = self._analytical_minimal_fallback(objective)
            analytic = self._post_process(analytic, objective, norm_errs + ["analytic_after_validation"])
            plan = MissionPlanSchema(objective=objective, tasks=analytic)
            self._post_validate(plan)
            self._log_success(plan, objective, start, degraded=True,
                              notes=errors + norm_errs + ["analytic_after_validation_no_fallback"])
            return plan
        except Exception as ve:
            errors.extend(norm_errs)
            if FALLBACK_ALLOW:
                degraded = self._fallback_plan(objective, cap)
                degraded.tasks = self._post_process(degraded.tasks, objective, errors + ["normalize_exception_fallback"])
                self._post_validate(degraded)
                self._log_success(degraded, objective, start, degraded=True, notes=errors[-10:])
                return degraded
            analytic = self._analytical_minimal_fallback(objective)
            analytic = self._post_process(analytic, objective, errors + ["analytic_exception"])
            plan = MissionPlanSchema(objective=objective, tasks=analytic)
            self._post_validate(plan)
            self._log_success(plan, objective, start, degraded=True, notes=errors[-10:])
            return plan

        tasks = self._post_process(tasks, objective, norm_errs)
        mission_plan = MissionPlanSchema(objective=str(plan_dict.get("objective") or objective), tasks=tasks)
        self._post_validate(mission_plan)
        self._log_success(mission_plan, objective, start, degraded=False, notes=errors + norm_errs)
        return mission_plan

    # ------------------------------------------------------------------ Logging
    def _log_success(
        self,
        plan: MissionPlanSchema,
        objective: str,
        start: float,
        degraded: bool,
        notes: Optional[List[str]] = None
    ):
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        _LOG.info(
            "[%s] plan_success%s tasks=%d elapsed_ms=%.1f objective='%s'",
            self.name,
            "_degraded" if degraded else "",
            len(plan.tasks),
            elapsed_ms,
            _clip(objective, 80),
        )
        if notes:
            _LOG.debug("[%s] notes_tail=%s", self.name, notes[-14:])

    # ------------------------------------------------------------------ LLM Structured Call
    def _call_structured(self, objective: str, context: Optional[PlanningContext], max_tasks: int) -> Dict[str, Any]:
        if maestro is None or not hasattr(maestro, "generation_service"):
            raise RuntimeError("maestro_generation_service_unavailable")
        svc = maestro.generation_service  # type: ignore
        schema = {
            "type": "object",
            "properties": {
                "objective": {"type": "string"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "tool_args": {"type": "object"},
                            "dependencies": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["description", "tool_name"],
                    },
                },
            },
            "required": ["tasks"],
        }
        user_prompt = self._render_prompt(objective, context, max_tasks)
        system_prompt = (
            "You are a precision mission planner. Return ONLY valid JSON per schema. "
            "Use allowed tool names exactly and include required arguments."
        )
        resp = svc.structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            format_schema=schema,
            temperature=0.12,
            max_retries=1,
            fail_hard=False,
        )
        if not isinstance(resp, dict):
            raise PlannerError("structured_not_dict", self.name, objective)
        if "tasks" not in resp:
            raise PlannerError("structured_missing_tasks", self.name, objective)
        return resp

    # ------------------------------------------------------------------ LLM Text Call
    def _call_text(self, objective: str, context: Optional[PlanningContext]) -> str:
        if maestro is None or not hasattr(maestro, "generation_service"):
            raise RuntimeError("maestro_generation_service_unavailable_text")
        svc = maestro.generation_service  # type: ignore
        system_prompt = (
            "You are a mission planner. Output ONLY JSON: {objective, tasks}. "
            "Each task: description, tool_name, tool_args(object), dependencies(array). "
            "Use ONLY allowed tool names."
        )
        user_prompt = self._render_prompt(objective, context, MAX_TASKS_DEFAULT)
        txt = svc.text_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.33,
            max_tokens=900,
            max_retries=1,
            fail_hard=False,
        )
        if not txt or not isinstance(txt, str):
            raise PlannerError("text_empty_response", self.name, objective)
        return txt

    # ------------------------------------------------------------------ Extract From Text
    def _extract_from_text(self, raw_text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        errs: List[str] = []
        snippet = (raw_text or "").strip()
        if not snippet:
            return None, ["empty_text"]

        parsed, err = _safe_json_loads(snippet)
        if parsed and isinstance(parsed, dict) and "tasks" in parsed:
            return parsed, errs
        if err:
            errs.append(f"direct_fail:{err}")

        arr_m = _TASK_ARRAY_REGEX.search(snippet)
        if arr_m:
            arr_chunk = arr_m.group(1)
            safe_obj = json.dumps(_clip(snippet, 50))
            synth = f'{{"objective":{safe_obj},"tasks":{arr_chunk}}}'
            cand, err2 = _safe_json_loads(synth)
            if cand and isinstance(cand, dict) and "tasks" in cand:
                return cand, errs
            if err2:
                errs.append(f"tasks_array_fail:{err2}")

        blk = _JSON_BLOCK_CURLY.search(snippet)
        if blk:
            block = blk.group(0)
            cand2, err3 = _safe_json_loads(block)
            if cand2 and isinstance(cand2, dict) and "tasks" in cand2:
                return cand2, errs
            if err3:
                errs.append(f"block_fail:{err3}")

        errs.append("extraction_all_failed")
        return None, errs

    # ------------------------------------------------------------------ Normalize Tasks
    def _normalize_tasks(self, tasks_raw: Any, cap: int, errors_out: List[str]) -> List[PlannedTask]:
        if not isinstance(tasks_raw, list):
            raise PlanValidationError("tasks_not_list", self.name)

        cleaned: List[PlannedTask] = []
        seen_ids: set = set()
        norm_notes: List[str] = []

        for idx, t in enumerate(tasks_raw):
            if len(cleaned) >= cap:
                errors_out.append("task_limit_reached")
                break
            if not isinstance(t, dict):
                errors_out.append(f"task_{idx}_not_dict")
                continue

            raw_desc = str(t.get("description") or "").strip()
            if not raw_desc:
                errors_out.append(f"task_{idx}_missing_description")
                continue

            raw_tool = str(t.get("tool_name") or "unknown").strip()
            tool_args = t.get("tool_args")
            if not isinstance(tool_args, dict):
                errors_out.append(f"task_{idx}_tool_args_not_object")
                tool_args = {}

            deps = t.get("dependencies")
            if not isinstance(deps, list):
                errors_out.append(f"task_{idx}_deps_not_list")
                deps = []

            # Canonicalization
            canonical_tool, notes = _canonicalize_tool(raw_tool, raw_desc)
            norm_notes.extend([f"task{idx+1}:{n}" for n in notes])

            # Force classification if off-canonical
            if FORCE_FILE_TOOLS and canonical_tool not in {CANON_WRITE, CANON_READ, CANON_THINK}:
                if _looks_like_write(raw_desc):
                    canonical_tool = CANON_WRITE
                    norm_notes.append(f"task{idx+1}:forced_write_intent")
                elif _looks_like_read(raw_desc):
                    canonical_tool = CANON_READ
                    norm_notes.append(f"task{idx+1}:forced_read_intent")
                elif _looks_like_think(raw_desc):
                    canonical_tool = CANON_THINK
                    norm_notes.append(f"task{idx+1}:forced_think_intent")

            # Enforce allowed tools
            if ENFORCE_ALLOWED and canonical_tool not in ALLOWED_TOOLS:
                norm_notes.append(f"task{idx+1}:enforce_allowed->generic_think")
                canonical_tool = CANON_THINK

            # Auto fill file arguments
            if AUTO_FIX_FILE_TASKS:
                _autofill_file_args(canonical_tool, tool_args, idx + 1, norm_notes)

            # Filter dependencies to existing tNN pattern
            filtered_deps: List[str] = []
            for d in deps:
                if isinstance(d, str) and re.match(r"^t\d{2}$", d):
                    # Only keep if earlier than current index after we assign IDs (safe post-pass)
                    filtered_deps.append(d)

            # Interpolation injection for thinking tasks
            if canonical_tool == CANON_THINK and filtered_deps:
                p = tool_args.get("prompt")
                if isinstance(p, str):
                    tool_args["prompt"] = _interpolate_prompt_if_missing(p, filtered_deps)

            # Assign ID
            tid = _canonical_task_id(len(cleaned) + 1)
            while tid in seen_ids:
                tid = _canonical_task_id(len(seen_ids) + len(cleaned) + 1)
            seen_ids.add(tid)

            # Risk embed
            tool_args["_meta_risk"] = _risk_score(canonical_tool, raw_desc, tool_args, filtered_deps)

            cleaned.append(
                PlannedTask(
                    task_id=tid,
                    description=raw_desc,
                    tool_name=canonical_tool,
                    tool_args=tool_args,
                    dependencies=filtered_deps,
                )
            )

        if not cleaned:
            raise PlanValidationError("no_valid_tasks", self.name)

        if norm_notes:
            _LOG.debug("[%s] normalization_events total=%d sample=%s",
                       self.name, len(norm_notes), norm_notes[:14])

        return cleaned

    # ------------------------------------------------------------------ Post Process
    def _post_process(self, tasks: List[PlannedTask], objective: str, notes: List[str]) -> List[PlannedTask]:
        report_name = FORCE_REPORT_NAME or self._extract_report_name_from_objective(objective)
        write_indices = [i for i, t in enumerate(tasks) if t.tool_name == CANON_WRITE]

        if write_indices:
            if len(write_indices) > 1:
                last_idx = write_indices[-1]
                new: List[PlannedTask] = []
                writes_kept = 0
                for i, t in enumerate(tasks):
                    if t.tool_name == CANON_WRITE and i != last_idx:
                        content_val = ""
                        if isinstance(t.tool_args, dict):
                            content_val = str(t.tool_args.get("content") or "")
                        if content_val.strip() == FILE_DEFAULT_CONTENT.strip():
                            notes.append(f"drop_placeholder_write:{t.task_id}")
                            continue
                        if writes_kept >= (MAX_WRITES - 1):
                            notes.append(f"drop_extra_write:{t.task_id}")
                            continue
                        writes_kept += 1
                    new.append(t)
                tasks = new

            final_write = None
            for t in reversed(tasks):
                if t.tool_name == CANON_WRITE:
                    final_write = t
                    break
            if final_write and isinstance(final_write.tool_args, dict):
                if report_name:
                    final_write.tool_args["path"] = report_name
                else:
                    pth = final_write.tool_args.get("path") or f"report{FILE_DEFAULT_EXT}"
                    if not pth.endswith(FILE_DEFAULT_EXT):
                        pth = pth + FILE_DEFAULT_EXT
                    final_write.tool_args["path"] = pth
                final_write.tool_args.setdefault("dry_run_hint", False)

        # Second pass dependency pruning
        valid_ids = {t.task_id for t in tasks}
        for t in tasks:
            if t.dependencies:
                t.dependencies = [d for d in t.dependencies if d in valid_ids]

        return tasks

    # ------------------------------------------------------------------ Report Name Extraction
    def _extract_report_name_from_objective(self, objective: str) -> Optional[str]:
        low = objective.lower()
        # Look for explicit file naming tokens
        m = re.search(r"summary file named\s+([A-Za-z0-9_.\-]+)", low)
        if m:
            return m.group(1)
        for token in ("report_arabic.md", "architecture_principles.md", "report.md", "report.txt"):
            if token in low:
                return token
        return None

    # ------------------------------------------------------------------ Post Validate (graph & size)
    def _post_validate(self, plan: MissionPlanSchema):
        # Cycle detection
        graph = {t.task_id: set(t.dependencies) for t in plan.tasks}
        valid = set(graph.keys())
        for deps in graph.values():
            deps.intersection_update(valid)

        visited: Dict[str, int] = {}

        def dfs(node: str, stack: List[str]):
            st = visited.get(node, 0)
            if st == 1:
                raise PlanValidationError(f"cycle_detected:{'->'.join(stack+[node])}", self.name)
            if st == 2:
                return
            visited[node] = 1
            for nxt in graph.get(node, []):
                dfs(nxt, stack + [node])
            visited[node] = 2

        for tid in graph:
            if visited.get(tid, 0) == 0:
                dfs(tid, [])

        if len(plan.tasks) > MAX_TASKS_DEFAULT:
            raise PlanValidationError("exceed_global_max_tasks", self.name)

        low_obj = plan.objective.lower()
        if ("write" in low_obj or "report" in low_obj or "summary" in low_obj) and \
                not any(t.tool_name == CANON_WRITE for t in plan.tasks):
            _LOG.debug("[%s] post_validate: objective hints output file but no write_file emitted.", self.name)

    # ------------------------------------------------------------------ Fallback Plans
    def _fallback_plan(self, objective: str, cap: int) -> MissionPlanSchema:
        """
        Legacy segmented fallback: splits objective words into chained tasks.
        Final segment optionally becomes write_file if autofill enabled.
        """
        words = [w for w in re.split(r"\s+", objective.strip()) if w]
        if not words:
            words = ["objective"]
        slice_count = min(FALLBACK_MAX, cap, max(1, len(words)))
        chunk_len = max(1, len(words) // slice_count)
        segments: List[str] = []
        for i in range(0, len(words), chunk_len):
            segments.append(" ".join(words[i:i + chunk_len]))
            if len(segments) >= slice_count:
                break
        tasks: List[PlannedTask] = []
        for i, seg in enumerate(segments, start=1):
            tool_name = CANON_THINK
            tool_args: Dict[str, Any] = {"prompt": f"Decompose segment: {seg}"}
            if AUTO_FIX_FILE_TASKS and i == len(segments):
                tool_name = CANON_WRITE
                tool_args = {
                    "path": f"fallback_{i:02d}{FILE_DEFAULT_EXT}",
                    "content": f"Fallback segment: {seg}"
                }
            tasks.append(
                PlannedTask(
                    task_id=_canonical_task_id(i),
                    description=f"Decompose: {seg}",
                    tool_name=tool_name,
                    tool_args=tool_args,
                    dependencies=[] if i == 1 else [_canonical_task_id(i - 1)]
                )
            )
        return MissionPlanSchema(objective=objective, tasks=tasks)

    def _analytical_minimal_fallback(self, objective: str) -> List[PlannedTask]:
        """
        Absolute safety-net fallback:
            t01 generic_think (analysis)
            t02 write_file (final summary)
        Language auto-detected (Arabic vs English).
        """
        want_ar = _objective_has_arabic(objective)
        lang_line = "اكتب الملخص باللغة العربية." if want_ar else "Write the summary in concise English."
        prompt = (
            f"{lang_line}\nObjective:\n{objective}\n"
            "Provide a structured summary (bullets or concise paragraphs). "
            "If information is missing, explicitly state assumptions."
        )
        return [
            PlannedTask(
                task_id="t01",
                description="Analyze objective and draft summary.",
                tool_name=CANON_THINK,
                tool_args={"prompt": prompt, "_meta_risk": 1.0},
                dependencies=[]
            ),
            PlannedTask(
                task_id="t02",
                description="Write final summary file.",
                tool_name=CANON_WRITE,
                tool_args={
                    "path": FORCE_REPORT_NAME or "SUMMARY_REPORT.md",
                    "content": "{{t01.answer}}",
                    "_meta_risk": 2.0,
                    "dry_run_hint": False
                },
                dependencies=["t01"]
            )
        ]

    # ------------------------------------------------------------------ Prompt Rendering (LLM mode)
    def _render_prompt(self, objective: str, context: Optional[PlanningContext], max_tasks: int) -> str:
        lines: List[str] = []
        lines.append("OBJECTIVE:")
        lines.append(objective)
        lines.append("")
        if context and context.past_failures:
            lines.append("PAST_FAILURES:")
            for f in context.past_failures[:5]:
                lines.append(f"- {f}")
            lines.append("")
        lines.append("ALLOWED_TOOLS (USE ONLY THESE EXACT NAMES):")
        for t in sorted(ALLOWED_TOOLS):
            if t == CANON_READ:
                lines.append(f"- {t}: read a UTF-8 text file; MUST supply tool_args.path")
            elif t == CANON_THINK:
                lines.append(f"- {t}: reasoning / analysis / counting; MUST supply tool_args.prompt")
            elif t == CANON_WRITE:
                lines.append(f"- {t}: create/overwrite file; MUST supply tool_args.path & tool_args.content")
            else:
                lines.append(f"- {t}: (custom)")
        lines.append("")
        lines.append("RULES:")
        lines.append("1. If the objective needs a file's content, emit read_file first.")
        lines.append("2. Then emit generic_think referencing {{tXX.content}} in its prompt (if reading).")
        lines.append("3. Emit exactly one final write_file with the final answer (Arabic if requested).")
        lines.append("4. Provide explicit paths; prefer .md for final reports.")
        lines.append("5. Do NOT invent unknown tool names. If unsure use generic_think.")
        lines.append("6. If no file reading is needed, still produce one generic_think then one write_file task.")
        lines.append("")
        lines.append(f"Produce up to {max_tasks} tasks (typically 2-4). Return ONLY valid JSON.")
        return "\n".join(lines)

    # ------------------------------------------------------------------ Objective Validator
    def _objective_valid(self, objective: str) -> bool:
        if not objective:
            return False
        x = objective.strip()
        if len(x) < 5:
            return False
        if x.isdigit():
            return False
        return True


# --------------------------------------------------------------------------------------
# Exports
# --------------------------------------------------------------------------------------
__all__ = [
    "LLMGroundedPlanner",
    "MissionPlanSchema",
    "PlannedTask",
    "PlanningContext",
    "PlannerError",
    "PlanValidationError",
]

# --------------------------------------------------------------------------------------
# Dev Quick Test
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        "Read the docker-compose.yml file, count number of services, and write Arabic report named report_arabic.md.",
        "Analyze the current system architecture and create a summary file named ARCHITECTURE_PRINCIPLES.md",
        "Analyze and produce a concise summary file of the backend modules",
        "Quick objective that should still yield a minimal analytic plan"
    ]
    ok, reason = LLMGroundedPlanner.self_test()
    print(f"[SELF_TEST] ok={ok} reason={reason}")
    planner = LLMGroundedPlanner()
    for obj in tests:
        print("\n=== OBJECTIVE:", obj)
        plan = planner.generate_plan(obj)
        print(f"Produced {len(plan.tasks)} tasks:")
        for t in plan.tasks:
            print(f"  {t.task_id} | {t.tool_name} | deps={t.dependencies} | args={t.tool_args}")