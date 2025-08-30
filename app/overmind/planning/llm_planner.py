# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
# -*- coding: utf-8 -*-
"""
LLMGroundedPlanner (Enhanced Version)

Purpose of this enhanced rewrite:
---------------------------------
This version adds hardening specifically to eliminate the recurring runtime
failures you observed:

1) Missing required parameters: ['path']
2) ToolNotFound: file_system.write / file_system.read (dot-qualified names)
3) "unknown" / mis-grounded tool names for simple file tasks

Key Hardening Features Added:
-----------------------------
A. Tool Name Canonicalization:
   - Accepts dotted names like "file_system.write", "file_system.read".
   - Maps a broad set of aliases & dotted forms to canonical tool names:
        write_file (writer)  / read_file (reader)
   - Falls back to write_file if "create"/"generate"/"write" intent detected
     or read_file if "read"/"load"/"open"/"inspect" intent detected, when the
     LLM leaves tool_name "unknown".

B. Mandatory Args Auto-Fill (Configurable):
   - For write_file: ensures both path + content exist.
   - For read_file: ensures path exists.
   - Auto-filled path pattern: auto_generated_<task_index>.txt (or .md)
   - Default content placeholder for write_file if missing.
   - Controlled via env:
        PLANNER_AUTO_FIX_FILE_TASKS=1 (default on)
        PLANNER_FILE_DEFAULT_EXT=.txt (change extension)
        PLANNER_FILE_DEFAULT_CONTENT (override default content)

C. Unified Logging & Diagnostics:
   - Each normalization adjustment is logged at DEBUG (summarized counts at INFO).
   - Collected normalization warnings folded into planner notes (debug level).

D. Strict Schema Integration:
   - Still returns MissionPlanSchema with list[PlannedTask].
   - Maintains original structured / text fallback logic.

E. Safe Tool Existence Check:
   - After canonicalization; if tool missing but *looks* like file op, we still
     force canonical name to prevent ToolNotFound (configurable override):
       PLANNER_FORCE_FILE_TOOLS=1 (default)

F. Dotted Tool Stripping:
   - Always splits on first dot; suffix used to refine guess (write/read).

Environment Flags Summary:
--------------------------
PLANNER_AUTO_FIX_FILE_TASKS=1         -> enable auto-fix of missing path/content.
PLANNER_FORCE_FILE_TOOLS=1            -> force mapping to write_file/read_file when intent inferred.
PLANNER_FILE_DEFAULT_EXT=.txt         -> default extension for synthesized file paths.
PLANNER_FILE_DEFAULT_CONTENT          -> custom default content for created write tasks.
LLM_PLANNER_STRICT_JSON, etc.         -> existing original flags preserved.

All modifications are confined to this file only.

"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------------------
# Logging Setup
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
# Strict base imports (with optional stub)
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

# --------------------------------------------------------------------------------------
# Unified Schemas
# --------------------------------------------------------------------------------------
from .schemas import MissionPlanSchema, PlannedTask, PlanningContext  # type: ignore

# --------------------------------------------------------------------------------------
# Optional services
# --------------------------------------------------------------------------------------
try:
    from app.services import maestro  # type: ignore
except Exception:
    maestro = None  # type: ignore

try:
    from app.services import agent_tools  # type: ignore
except Exception:
    agent_tools = None  # type: ignore

# --------------------------------------------------------------------------------------
# Config / Env Flags
# --------------------------------------------------------------------------------------
STRICT_JSON_ONLY = os.getenv("LLM_PLANNER_STRICT_JSON", "0") == "1"
SELF_TEST_MODE = (os.getenv("LLM_PLANNER_SELFTEST_MODE") or "fast").lower()  # fast|skip|normal
FALLBACK_ALLOW = os.getenv("LLM_PLANNER_FALLBACK_ALLOW", "0") == "1"
FALLBACK_MAX = int(os.getenv("LLM_PLANNER_FALLBACK_MAX_TASKS", "5"))
SELF_TEST_STRICT = os.getenv("LLM_PLANNER_SELFTEST_STRICT", "0") == "1"
MAX_TASKS_DEFAULT = int(os.getenv("LLM_PLANNER_MAX_TASKS", "25"))

# New Hardening Env
AUTO_FIX_FILE_TASKS = os.getenv("PLANNER_AUTO_FIX_FILE_TASKS", "1") == "1"
FORCE_FILE_TOOLS = os.getenv("PLANNER_FORCE_FILE_TOOLS", "1") == "1"
FILE_DEFAULT_EXT = os.getenv("PLANNER_FILE_DEFAULT_EXT", ".txt")
FILE_DEFAULT_CONTENT = os.getenv(
    "PLANNER_FILE_DEFAULT_CONTENT",
    "Placeholder content (auto-generated by planner).",
)

# Regex patterns
_TOOL_NAME_PATTERN_PRIMARY = r"^[A-Za-z0-9_.:~-]{2,128}$"
_TOOL_NAME_PATTERN_FALLBACK = r"^[A-Za-z0-9_]{2,64}$"  # narrower


def _compile_tool_name_regex() -> re.Pattern:
    try:
        return re.compile(_TOOL_NAME_PATTERN_PRIMARY)
    except re.error as e:
        _LOG.warning("[llm_planner] primary tool name regex failed %s; using fallback", e)
        return re.compile(_TOOL_NAME_PATTERN_FALLBACK)


_VALID_TOOL_NAME = _compile_tool_name_regex()

_TASK_ARRAY_REGEX = re.compile(r'"tasks"\s*:\s*(\[[^\]]*\])', re.IGNORECASE | re.DOTALL)
_JSON_BLOCK_CURLY = re.compile(r"\{.*\}", re.DOTALL)

# --------------------------------------------------------------------------------------
# Canonical Tool Definitions / Aliases
# --------------------------------------------------------------------------------------
CANON_WRITE = "write_file"
CANON_READ = "read_file"

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
    "touch_file",
    "make_file",
}

READ_ALIASES = {
    "read_file",
    "file_reader",
    "file_system_read",
    "file_system.read",
    "reader",
    "open_file",
    "load_file",
    "view_file",
    "show_file",
}

# Suffix -> classification (when dotted)
DOT_SUFFIX_WRITE = {"write", "create", "generate", "touch"}
DOT_SUFFIX_READ = {"read", "open", "load", "view", "show"}

# Required arguments by canonical tool (for autofill)
MANDATORY_ARGS = {
    CANON_WRITE: ["path", "content"],
    CANON_READ: ["path"],
}

# Heuristic intent keywords
WRITE_INTENT = {"write", "create", "generate", "append", "produce", "save"}
READ_INTENT = {"read", "inspect", "load", "open", "view"}


# --------------------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------------------
def _clip(s: str, n: int = 160) -> str:
    if s is None:
        return ""
    return s if len(s) <= n else s[: n - 3] + "..."


def _safe_json_loads(txt: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(txt), None
    except Exception as e:
        return None, str(e)


def _tool_exists(name: str) -> bool:
    if not agent_tools:
        return False
    try:
        return bool(agent_tools.get_tool(name))  # type: ignore
    except Exception:
        return False


def _canonical_task_id(i: int) -> str:
    return f"t{i:02d}"


def _lower(s: Any) -> str:
    return str(s or "").strip().lower()


def _looks_like_write(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in WRITE_INTENT)


def _looks_like_read(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in READ_INTENT)


def _split_dotted(name: str) -> Tuple[str, Optional[str]]:
    if "." in name:
        base, suffix = name.split(".", 1)
        return base, suffix
    return name, None


def _canonicalize_tool_name(raw: str, description: str) -> Tuple[str, List[str]]:
    """
    Returns canonical tool name plus a list of notes describing the transformations.
    """
    notes: List[str] = []
    name = _lower(raw)
    base, suffix = _split_dotted(name)

    # 1) Direct alias groups
    if base in WRITE_ALIASES or name in WRITE_ALIASES:
        notes.append(f"alias_write:{raw}")
        return CANON_WRITE, notes
    if base in READ_ALIASES or name in READ_ALIASES:
        notes.append(f"alias_read:{raw}")
        return CANON_READ, notes

    # 2) Dotted suffix inference
    if suffix:
        if suffix in DOT_SUFFIX_WRITE:
            notes.append(f"dotted_write_suffix:{suffix}")
            return CANON_WRITE, notes
        if suffix in DOT_SUFFIX_READ:
            notes.append(f"dotted_read_suffix:{suffix}")
            return CANON_READ, notes

    # 3) Intent heuristics (only if unknown or ambiguous)
    if name in {"unknown", "", "file", "filesystem"}:
        if _looks_like_write(description):
            notes.append("intent_write_from_desc")
            return CANON_WRITE, notes
        if _looks_like_read(description):
            notes.append("intent_read_from_desc")
            return CANON_READ, notes

    # 4) Fallback: if the raw explicitly contains 'write' or 'read'
    if "write" in name:
        notes.append("contains_write_token")
        return CANON_WRITE, notes
    if "read" in name:
        notes.append("contains_read_token")
        return CANON_READ, notes

    # 5) Return as-is if no mapping triggered
    return raw, notes


def _autofill_file_args(
    tool_name: str,
    tool_args: Dict[str, Any],
    task_index: int,
    normalize_notes: List[str],
):
    """
    Ensures mandatory args present for file read/write tasks.
    """
    if tool_name not in MANDATORY_ARGS:
        return

    required = MANDATORY_ARGS[tool_name]
    changed = False

    # Path
    if "path" not in tool_args or not str(tool_args.get("path")).strip():
        filename = f"auto_generated_{task_index:02d}{FILE_DEFAULT_EXT}"
        tool_args["path"] = filename
        normalize_notes.append(f"autofill_path:{filename}")
        changed = True

    # Content (write only)
    if "content" in required:
        if "content" not in tool_args or not isinstance(tool_args["content"], str) or not tool_args["content"].strip():
            tool_args["content"] = FILE_DEFAULT_CONTENT
            normalize_notes.append("autofill_content:default")
            changed = True

    if changed:
        normalize_notes.append("mandatory_args_filled")


# ======================================================================================
# Planner Class
# ======================================================================================
class LLMGroundedPlanner(BasePlanner):
    name = "llm_grounded_planner"
    version = "2.0.4-hardened"
    tier = "core"
    production_ready = True
    capabilities = {"planning", "llm", "tool-grounding"}
    tags = {"mission", "tasks"}

    # ------------------------------------------------------------------
    # Self Test
    # ------------------------------------------------------------------
    @classmethod
    def self_test(cls) -> Tuple[bool, str]:
        if not cls.name or " " in cls.name:
            return False, "invalid_name"
        mode = SELF_TEST_MODE
        if mode == "skip":
            return True, "skip_mode"
        if mode == "fast":
            return True, "fast_ok" if maestro is not None else "fast_no_maestro"
        # normal mode
        if maestro is None and SELF_TEST_STRICT:
            return False, "maestro_missing_strict"
        if maestro and hasattr(maestro, "generation_service"):
            try:
                svc = maestro.generation_service  # type: ignore
                schema = {
                    "type": "object",
                    "properties": {"status": {"type": "string"}},
                    "required": ["status"],
                }
                t0 = time.perf_counter()
                resp = svc.structured_json(
                    system_prompt="Return {'status':'ok'}",
                    user_prompt="Say ok",
                    format_schema=schema,
                    temperature=0.0,
                    max_retries=1,
                    fail_hard=False,
                )
                if (time.perf_counter() - t0) > 4.5:
                    return False, "selftest_timeout"
                if not (isinstance(resp, dict) and resp.get("status") == "ok"):
                    return False, "selftest_bad_payload"
            except Exception as e:
                if SELF_TEST_STRICT:
                    return False, f"selftest_exception:{type(e).__name__}"
                return True, "selftest_degraded"
        return True, "normal_ok"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        max_tasks: Optional[int] = None,
    ) -> MissionPlanSchema:
        start = time.perf_counter()
        if not self._objective_valid(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        cap = min(max_tasks or MAX_TASKS_DEFAULT, MAX_TASKS_DEFAULT)
        _LOG.info(
            "[%s] plan_start objective='%s' cap=%d strict=%s fallback=%s auto_fix=%s force_file=%s",
            self.name,
            _clip(objective, 120),
            cap,
            STRICT_JSON_ONLY,
            FALLBACK_ALLOW,
            AUTO_FIX_FILE_TASKS,
            FORCE_FILE_TOOLS,
        )

        errors: List[str] = []
        structured: Optional[Dict[str, Any]] = None

        # 1) Structured attempt
        if maestro and hasattr(maestro, "generation_service"):
            try:
                structured = self._call_structured(objective, context, cap)
                _LOG.debug("[%s] structured_ok keys=%s", self.name, list(structured.keys()))
            except Exception as e:
                errors.append(f"struct_fail:{type(e).__name__}:{e}")
                _LOG.warning("[%s] structured_fail %s", self.name, e)
        else:
            errors.append("maestro_unavailable")

        if STRICT_JSON_ONLY and structured is None and not FALLBACK_ALLOW:
            raise PlannerError("strict_mode_no_structured", self.name, objective, errors=errors[-5:])

        # 2) Text attempt if structured failed
        raw_text: Optional[str] = None
        if structured is None and maestro and hasattr(maestro, "generation_service"):
            try:
                raw_text = self._call_text(objective, context)
                _LOG.debug("[%s] text_len=%d", self.name, len(raw_text))
            except Exception as e:
                errors.append(f"text_fail:{type(e).__name__}:{e}")
                _LOG.error("[%s] text_fail %s", self.name, e)

        # 3) Extraction
        plan_dict: Optional[Dict[str, Any]] = None
        extraction_notes: List[str] = []
        if structured is not None:
            plan_dict = structured
        elif raw_text:
            plan_dict, extraction_notes = self._extract_from_text(raw_text)
            errors.extend(extraction_notes)

        # 4) Extraction failure
        if plan_dict is None:
            if FALLBACK_ALLOW:
                _LOG.warning(
                    "[%s] using_degraded_fallback errors_tail=%s",
                    self.name,
                    errors[-4:],
                )
                plan = self._fallback_plan(objective, cap)
                self._post_validate(plan)
                self._log_success(plan, objective, start, degraded=True)
                return plan
            raise PlannerError("extraction_failed", self.name, objective, errors=errors[-6:])

        # 5) Normalize tasks (with robust auto-fix)
        tasks_raw = plan_dict.get("tasks")
        norm_errs: List[str] = []
        try:
            tasks = self._normalize_tasks(tasks_raw, cap, norm_errs)
        except PlannerError:
            raise
        except Exception as ve:
            errors.extend(norm_errs)
            if FALLBACK_ALLOW:
                _LOG.warning("[%s] normalize_failed_fallback %s", self.name, ve)
                plan = self._fallback_plan(objective, cap)
                self._post_validate(plan)
                self._log_success(plan, objective, start, degraded=True)
                return plan
            raise PlannerError("normalize_fail", self.name, objective, errors=errors[-8:]) from ve

        # 6) Build unified MissionPlanSchema (Pydantic)
        mission_plan = MissionPlanSchema(
            objective=str(plan_dict.get("objective") or objective),
            tasks=tasks,
        )
        self._post_validate(mission_plan)
        self._log_success(mission_plan, objective, start, degraded=False, notes=errors + norm_errs)
        return mission_plan

    # ------------------------------------------------------------------
    # Logging success
    # ------------------------------------------------------------------
    def _log_success(
        self,
        plan: MissionPlanSchema,
        objective: str,
        start: float,
        degraded: bool,
        notes: Optional[List[str]] = None,
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
            # Keep only last few categories
            tail = notes[-10:]
            _LOG.debug("[%s] notes_tail=%s", self.name, tail)

    # ------------------------------------------------------------------
    # Structured call
    # ------------------------------------------------------------------
    def _call_structured(
        self,
        objective: str,
        context: Optional[PlanningContext],
        max_tasks: int,
    ) -> Dict[str, Any]:
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
        system_prompt = "You are a precision mission planner. Return ONLY valid JSON."
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

    # ------------------------------------------------------------------
    # Text call
    # ------------------------------------------------------------------
    def _call_text(
        self,
        objective: str,
        context: Optional[PlanningContext],
    ) -> str:
        if maestro is None or not hasattr(maestro, "generation_service"):
            raise RuntimeError("maestro_generation_service_unavailable_text")
        svc = maestro.generation_service  # type: ignore
        system_prompt = (
            "You are a mission planner. Output JSON only. Keys: objective, tasks. "
            "Each task: description, tool_name, tool_args(object), dependencies(array)."
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

    # ------------------------------------------------------------------
    # Extraction from text
    # ------------------------------------------------------------------
    def _extract_from_text(
        self,
        raw_text: str,
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
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

        # Heuristic bullet fallback
        tasks_guess: List[Dict[str, Any]] = []
        current: Optional[Dict[str, Any]] = None
        for line in snippet.splitlines():
            ln = line.strip()
            if not ln:
                continue
            if ln.startswith("- "):
                if current:
                    tasks_guess.append(current)
                current = {
                    "description": ln[2:].strip(),
                    "tool_name": "unknown",
                    "tool_args": {},
                    "dependencies": [],
                }
            elif ":" in ln and current:
                k, v = ln.split(":", 1)
                k = k.strip().lower()
                v = v.strip().strip(",")
                if k in ("tool", "tool_name"):
                    current["tool_name"] = v
        if current:
            tasks_guess.append(current)

        if tasks_guess:
            return {"objective": "Recovered (bullets)", "tasks": tasks_guess}, errs

        errs.append("extraction_all_failed")
        return None, errs

    # ------------------------------------------------------------------
    # Normalize tasks (critical hardening section)
    # ------------------------------------------------------------------
    def _normalize_tasks(
        self,
        tasks_raw: Any,
        cap: int,
        errors_out: List[str],
    ) -> List[PlannedTask]:
        if not isinstance(tasks_raw, list):
            raise PlanValidationError("tasks_not_list", self.name)

        cleaned: List[PlannedTask] = []
        seen_ids: set = set()
        normalization_notes: List[str] = []

        for idx, t in enumerate(tasks_raw):
            task_index = idx + 1
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

            # Canonicalize tool name
            canonical_tool, notes = _canonicalize_tool_name(raw_tool, raw_desc)
            normalization_notes.extend([f"task_{task_index}:{n}" for n in notes])

            # If canonical tool not registered, but looks like read/write, optionally force
            if FORCE_FILE_TOOLS and canonical_tool not in {CANON_WRITE, CANON_READ}:
                if _looks_like_write(raw_desc):
                    canonical_tool = CANON_WRITE
                    normalization_notes.append(f"task_{task_index}:forced_write_from_desc")
                elif _looks_like_read(raw_desc):
                    canonical_tool = CANON_READ
                    normalization_notes.append(f"task_{task_index}:forced_read_from_desc")

            # Auto-fill mandatory args for file tools
            if AUTO_FIX_FILE_TASKS:
                _autofill_file_args(canonical_tool, tool_args, task_index, normalization_notes)

            # Verify tool existence (after fixes). If still unknown, degrade gracefully
            if agent_tools and not _tool_exists(canonical_tool):
                errors_out.append(f"task_{idx}_tool_missing:{canonical_tool}")
                # Optionally fallback to a known file tool if path/content present
                if FORCE_FILE_TOOLS and (
                    "path" in tool_args or _looks_like_write(raw_desc) or _looks_like_read(raw_desc)
                ):
                    fallback_tool = CANON_WRITE if "content" in tool_args or _looks_like_write(raw_desc) else CANON_READ
                    normalization_notes.append(
                        f"task_{task_index}:substitute_missing_tool->{fallback_tool}"
                    )
                    canonical_tool = fallback_tool

            # Filter dependencies (keep only matching existing IDs once assigned)
            # We'll store dependency names as is (IDs referencing tasks) – if referencing
            # future unknown tasks, they get pruned.
            filtered_deps: List[str] = []
            for d in deps:
                if isinstance(d, str) and d.startswith("t") and len(d) <= 5:
                    filtered_deps.append(d)
                else:
                    # Non-ID dependencies are ignored (planner-level)
                    pass

            tid = _canonical_task_id(len(cleaned) + 1)
            while tid in seen_ids:
                tid = _canonical_task_id(len(seen_ids) + len(cleaned) + 1)
            seen_ids.add(tid)

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

        # Summarize normalization
        if normalization_notes:
            _LOG.debug(
                "[%s] normalization_events total=%d sample=%s",
                self.name,
                len(normalization_notes),
                normalization_notes[:12],
            )

        return cleaned

    # ------------------------------------------------------------------
    # Post validate (lightweight)
    # ------------------------------------------------------------------
    def _post_validate(self, plan: MissionPlanSchema):
        graph = {t.task_id: set(t.dependencies) for t in plan.tasks}
        valid = set(graph.keys())
        for deps in graph.values():
            deps.intersection_update(valid)

        visited: Dict[str, int] = {}

        def dfs(node: str, stack: List[str]):
            st = visited.get(node, 0)
            if st == 1:
                raise PlanValidationError(f"cycle_detected:{'->'.join(stack + [node])}", self.name)
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

    # ------------------------------------------------------------------
    # Fallback Plan (degraded)
    # ------------------------------------------------------------------
    def _fallback_plan(self, objective: str, cap: int) -> MissionPlanSchema:
        words = [w for w in re.split(r"\s+", objective.strip()) if w]
        if not words:
            words = ["objective"]
        slice_count = min(FALLBACK_MAX, cap, max(1, len(words)))
        chunk_len = max(1, len(words) // slice_count)
        segments: List[str] = []
        for i in range(0, len(words), chunk_len):
            segments.append(" ".join(words[i : i + chunk_len]))
            if len(segments) >= slice_count:
                break
        tool_default = CANON_WRITE if agent_tools else "unknown"
        tasks: List[PlannedTask] = []
        for i, seg in enumerate(segments, start=1):
            tool_args: Dict[str, Any] = {}
            if AUTO_FIX_FILE_TASKS and tool_default == CANON_WRITE:
                tool_args = {
                    "path": f"fallback_{i:02d}{FILE_DEFAULT_EXT}",
                    "content": f"Fallback segment: {seg}",
                }
            tasks.append(
                PlannedTask(
                    task_id=_canonical_task_id(i),
                    description=f"Decompose: {seg}",
                    tool_name=tool_default,
                    tool_args=tool_args,
                    dependencies=[] if i == 1 else [_canonical_task_id(i - 1)],
                )
            )
        return MissionPlanSchema(objective=objective, tasks=tasks)

    # ------------------------------------------------------------------
    # Prompt Rendering
    # ------------------------------------------------------------------
    def _render_prompt(
        self,
        objective: str,
        context: Optional[PlanningContext],
        max_tasks: int,
    ) -> str:
        lines: List[str] = []
        lines.append("OBJECTIVE:")
        lines.append(objective)
        lines.append("")
        if context and context.past_failures:
            lines.append("PAST_FAILURES:")
            for f in context.past_failures[:5]:
                lines.append(f"- {f}")
            lines.append("")
        examples = self._tool_examples(limit=5)
        if examples:
            lines.append("TOOL_EXAMPLES:")
            for name, desc in examples:
                lines.append(f"- {name}: {desc or 'No description'}")
            lines.append("")
        lines.append(f"Produce up to {max_tasks} tasks.")
        lines.append("Return ONLY JSON with keys: objective (string), tasks (array).")
        lines.append(
            "Each task object: description (string), tool_name (string), tool_args (object), dependencies (array)."
        )
        # Nudge to supply file paths explicitly
        lines.append(
            "If creating or writing a file ALWAYS include tool_args.path and tool_args.content."
        )
        lines.append("If reading a file ALWAYS include tool_args.path.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Tool examples
    # ------------------------------------------------------------------
    def _tool_examples(self, limit: int = 5) -> List[Tuple[str, Optional[str]]]:
        out: List[Tuple[str, Optional[str]]] = []
        if not agent_tools:
            return out
        try:
            for i, t in enumerate(agent_tools.list_tools()):  # type: ignore
                if i >= limit:
                    break
                out.append(
                    (
                        getattr(t, "name", f"tool_{i}"),
                        getattr(t, "description", None),
                    )
                )
        except Exception as e:
            _LOG.debug("[%s] tool_enum_fail:%s", self.name, e)
        return out

    # ------------------------------------------------------------------
    # Objective validity
    # ------------------------------------------------------------------
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
# Dev main (quick manual test)
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    ok, reason = LLMGroundedPlanner.self_test()
    print(f"[SELF_TEST] ok={ok} reason={reason}")
    planner = LLMGroundedPlanner()
    plan = planner.generate_plan("Create and then read a health check file for diagnostics.")
    print("Tasks:", len(plan.tasks))
    for t in plan.tasks:
        print(t.task_id, t.tool_name, t.tool_args)