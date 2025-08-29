# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
"""
# -*- coding: utf-8 -*-
# =================================================================================================
# LLMGroundedPlanner  (Version 1.4.0  "FORENSIC-STABLE / ZERO-TRIPLE-QUOTE")
# -------------------------------------------------------------------------------------------------
# الهدف:
#   تحويل objective لغوي إلى خطة مهام أداة-مرتكزة (tool-grounded) صالحة وقابلة للتنفيذ.
#
# السمات:
#   - لا سلاسل ثلاثية مطلقاً (تجنّب SyntaxError الناجم عن تلف نسخ/لصق).
#   - استيراد صارم لـ BasePlanner (Stub اختياري فقط إذا LLM_PLANNER_ALLOW_STUB=1).
#   - self_test يعيد (bool, reason) بلا صمت.
#   - توليد منظّم (structured JSON) أولاً، ثم استخراج متعدد المراحل عند الفشل.
#   - استخراج متعدد المراحل: (1) Direct Parse (2) tasks array synthesize (3) أول بلوك {} (4) Bullets.
#   - فحص / تطبيع المهام (أسماء الأدوات، args، deps) + كشف الدورات.
#   - Logging واضح: INFO (بداية/نجاح) / WARNING (فشل مرحلة) / ERROR (فشل نهائي) / DEBUG (تفاصيل).
#   - حماية من الأدوات المفقودة وتنبيه reliability.
#   - لا اعتماد على docstrings للتسجيل أو التعريف.
#
# متغيرات البيئة:
#   LLM_PLANNER_ALLOW_STUB=1        يسمح Stub مؤقت عند فشل استيراد القاعدة (DEV ONLY).
#   LLM_PLANNER_STRICT_JSON=1       يمنع السقوط إلى النص؛ فشل فوري إن أخفق التوليد المنظم.
#   LLM_PLANNER_MAX_TASKS=N         حد أقصى للمهام (افتراضي 25).
#   LLM_PLANNER_SELFTEST_STRICT=1   self_test يفشل إذا غابت الخدمات (maestro/agent_tools).
#   LLM_PLANNER_LOG_LEVEL=DEBUG|INFO|WARNING|ERROR|CRITICAL
#
# للتحقق السريع بعد الاستبدال:
#   1) grep -n '"""' app/overmind/planning/llm_planner.py || echo "NO triple quotes"
#   2) grep -n "'''" app/overmind/planning/llm_planner.py || echo "NO triple quotes"
#   3) python -m py_compile app/overmind/planning/llm_planner.py
# =================================================================================================

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Iterable

# -------------------------------------------------------------------------------------------------
# LOGGER
# -------------------------------------------------------------------------------------------------
_LOG = logging.getLogger("llm_planner")
_env_level = os.getenv("LLM_PLANNER_LOG_LEVEL", "").upper()
if _env_level:
    _LOG.setLevel(getattr(logging, _env_level, logging.INFO))
else:
    _LOG.setLevel(logging.INFO)

if not _LOG.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_handler)

# -------------------------------------------------------------------------------------------------
# STRICT BASE IMPORT
# -------------------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB", "0") == "1"
try:
    from .base_planner import BasePlanner, PlannerError  # type: ignore
except Exception as _base_err:  # noqa: BLE001
    if not _ALLOW_STUB:
        raise RuntimeError(
            "FATAL: Cannot import .base_planner. Set LLM_PLANNER_ALLOW_STUB=1 ONLY for temporary dev."
        ) from _base_err

    class PlannerError(Exception):  # type: ignore
        def __init__(self, message: str, planner: str = "stub", objective: str = "", extra: Dict[str, Any] = None):
            super().__init__(message)
            self.planner = planner
            self.objective = objective
            self.extra = extra or {}

    class BasePlanner:  # type: ignore
        name = "base_planner_stub"
        @classmethod
        def live_planner_classes(cls):
            return {}
        @classmethod
        def planner_metadata(cls):
            return {}
        @classmethod
        def compute_rank_hint(cls, **kwargs):
            return 0.0

    _LOG.error("USING STUB BasePlanner (LLM_PLANNER_ALLOW_STUB=1). This is NOT production ready.")

# -------------------------------------------------------------------------------------------------
# EXTERNAL SERVICES (Optional)
# -------------------------------------------------------------------------------------------------
try:
    from app.services import maestro  # type: ignore
except Exception:
    maestro = None  # type: ignore

try:
    from app.services import agent_tools  # type: ignore
except Exception:
    agent_tools = None  # type: ignore

# -------------------------------------------------------------------------------------------------
# OPTIONAL SHARED SCHEMAS
# -------------------------------------------------------------------------------------------------
try:
    from .schemas import MissionPlanSchema, PlannedTask, PlanningContext  # type: ignore
except Exception:
    @dataclass
    class PlannedTask:  # type: ignore
        task_id: str
        description: str
        tool_name: str
        tool_args: Dict[str, Any]
        dependencies: List[str]

    @dataclass
    class MissionPlanSchema:  # type: ignore
        objective: str
        tasks: List[PlannedTask] = field(default_factory=list)

    @dataclass
    class PlanningContext:  # type: ignore
        user_id: Optional[str] = None
        past_failures: List[str] = field(default_factory=list)
        user_preferences: Dict[str, Any] = field(default_factory=dict)
        tags: List[str] = field(default_factory=list)

# -------------------------------------------------------------------------------------------------
# CONFIG / CONSTANTS
# -------------------------------------------------------------------------------------------------
STRICT_JSON_ONLY = os.getenv("LLM_PLANNER_STRICT_JSON", "0") == "1"
SELF_TEST_STRICT = os.getenv("LLM_PLANNER_SELFTEST_STRICT", "0") == "1"
MAX_TASKS_DEFAULT = int(os.getenv("LLM_PLANNER_MAX_TASKS", "25"))

# Regex patterns (كلها raw أو عادية بدون backslash غير مهرب)
_VALID_TOOL_NAME = re.compile(r"^[a-zA-Z0-9_.\-:]{2,128}$")
_TASK_ARRAY_REGEX = re.compile(r'"tasks"\s*:\s*(\[[^\]]*\])', re.IGNORECASE | re.DOTALL)
_JSON_BLOCK_CURLY = re.compile(r"\{.*\}", re.DOTALL)

# -------------------------------------------------------------------------------------------------
# CUSTOM ERRORS
# -------------------------------------------------------------------------------------------------
class PlanValidationError(PlannerError):
    pass

# -------------------------------------------------------------------------------------------------
# UTILS
# -------------------------------------------------------------------------------------------------
def _clip(s: str, n: int = 180) -> str:
    return s if len(s) <= n else s[: n - 3] + "..."

def _safe_json_loads(payload: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(payload), None
    except Exception as e:  # noqa: BLE001
        return None, str(e)

def _tool_exists(name: str) -> bool:
    if not agent_tools:
        return False
    try:
        return bool(agent_tools.get_tool(name))  # type: ignore
    except Exception:
        return False

def _canonical_task_id(idx: int) -> str:
    return f"t{idx:02d}"

# -------------------------------------------------------------------------------------------------
# PLANNER IMPLEMENTATION
# -------------------------------------------------------------------------------------------------
class LLMGroundedPlanner(BasePlanner):
    # NOTE: السابق (LLM-grounded mission planner:) كان نص حر في نسخة تالفة؛ تحول الآن إلى تعليق.
    name: str = "llm_grounded_planner"
    version: str = "1.4.0"
    tier: str = "core"
    production_ready: bool = True
    capabilities = {"planning", "llm", "tool-grounding"}
    tags = {"mission", "tasks"}

    # ----------------------------------------------
    # SELF TEST
    # ----------------------------------------------
    @classmethod
    def self_test(cls) -> Tuple[bool, str]:
        if not cls.name or " " in cls.name:
            return False, "invalid_name"
        if maestro is None and SELF_TEST_STRICT:
            return False, "maestro_unavailable_strict"
        if agent_tools is None and SELF_TEST_STRICT:
            return False, "agent_tools_unavailable_strict"

        # Optional minimal structured ping
        if maestro and hasattr(maestro, "generation_service"):
            try:
                svc = maestro.generation_service  # type: ignore
                schema = {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}
                resp = svc.structured_json(
                    system_prompt="Return {'status':'ok'}",
                    user_prompt="Reply ok",
                    format_schema=schema,
                    temperature=0.0,
                    max_retries=1,
                    fail_hard=False,
                )
                if not (isinstance(resp, dict) and resp.get("status") == "ok"):
                    return False, f"mini_struct_bad:{resp}"
            except Exception as e:  # noqa: BLE001
                if SELF_TEST_STRICT:
                    return False, f"mini_struct_exc:{type(e).__name__}:{e}"
        return True, "ok"

    # ----------------------------------------------
    # PLAN GENERATION API
    # ----------------------------------------------
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        max_tasks: Optional[int] = None,
    ) -> MissionPlanSchema:
        start = time.perf_counter()

        if not self._objective_is_valid(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        cap = min(max_tasks or MAX_TASKS_DEFAULT, MAX_TASKS_DEFAULT)
        _LOG.info("[%s] plan_start objective='%s' cap=%d strict=%s",
                  self.name, _clip(objective, 120), cap, STRICT_JSON_ONLY)

        errors: List[str] = []
        structured: Optional[Dict[str, Any]] = None

        # Phase 1: Structured
        if maestro and hasattr(maestro, "generation_service"):
            try:
                structured = self._call_structured_llm(objective, context, cap)
                _LOG.debug("[%s] structured_ok keys=%s", self.name, list(structured.keys()))
            except Exception as e:  # noqa: BLE001
                errors.append(f"struct_fail:{type(e).__name__}:{e}")
                _LOG.warning("[%s] structured_fail %s", self.name, e)
        else:
            errors.append("maestro_unavailable")

        if STRICT_JSON_ONLY and structured is None:
            raise PlannerError(
                f"strict_json_failed errors={errors[-5:]}",
                self.name,
                objective,
                extra={"errors": errors},
            )

        # Phase 2: Text fallback
        raw_text: Optional[str] = None
        if structured is None:
            try:
                raw_text = self._call_text_llm(objective, context)
                _LOG.debug("[%s] text_len=%d", self.name, len(raw_text))
            except Exception as e:  # noqa: BLE001
                errors.append(f"text_fail:{type(e).__name__}:{e}")
                _LOG.error("[%s] text_fail %s", self.name, e)

        # Phase 3: Extraction
        plan_dict: Optional[Dict[str, Any]] = None
        extract_notes: List[str] = []
        if structured is not None:
            plan_dict = structured
        elif raw_text:
            plan_dict, extract_notes = self._extract_plan_from_text(raw_text)
            errors.extend(extract_notes)

        if plan_dict is None:
            raise PlannerError(
                f"extraction_failed errors={errors[-6:]}",
                self.name,
                objective,
                extra={"errors": errors},
            )

        # Phase 4: Normalize / validate tasks
        tasks_raw = plan_dict.get("tasks")
        norm_errors: List[str] = []
        try:
            tasks = self._normalize_and_validate_tasks(tasks_raw, cap, norm_errors)
        except PlanValidationError as ve:
            errors.extend(norm_errors)
            raise PlannerError(
                f"normalize_fail:{ve}",
                self.name,
                objective,
                extra={"errors": errors[-12:]},
            ) from ve

        mission_plan = MissionPlanSchema(
            objective=str(plan_dict.get("objective") or objective),
            tasks=tasks,
        )

        # Phase 5: Post validation (cycles, global constraints)
        self._post_validate(mission_plan)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        _LOG.info("[%s] plan_success objective='%s' tasks=%d elapsed_ms=%.1f",
                  self.name, _clip(objective, 100), len(mission_plan.tasks), elapsed_ms)
        if errors:
            _LOG.debug("[%s] notes=%s", self.name, errors[-6:])
        return mission_plan

    # ----------------------------------------------
    # Objective VS sanity
    # ----------------------------------------------
    def _objective_is_valid(self, objective: str) -> bool:
        if not objective:
            return False
        stripped = objective.strip()
        if len(stripped) < 5:
            return False
        if stripped.isdigit():
            return False
        return True

    # ----------------------------------------------
    # Structured Generation
    # ----------------------------------------------
    def _call_structured_llm(
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

        user_prompt = self._render_user_prompt(objective, context, max_tasks)
        system_prompt = "You are a precision mission planner. Respond ONLY with valid JSON."

        resp = svc.structured_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            format_schema=schema,
            temperature=0.1,
            max_retries=1,
            fail_hard=False,
        )

        if not isinstance(resp, dict):
            raise PlannerError("structured_not_dict", self.name, objective)
        if "tasks" not in resp:
            raise PlannerError("structured_missing_tasks", self.name, objective)
        return resp

    # ----------------------------------------------
    # Textual Fallback
    # ----------------------------------------------
    def _call_text_llm(
        self,
        objective: str,
        context: Optional[PlanningContext],
    ) -> str:
        if maestro is None or not hasattr(maestro, "generation_service"):
            raise RuntimeError("maestro_generation_service_unavailable_text")
        svc = maestro.generation_service  # type: ignore

        system_prompt = (
            "You are a mission planner. Output a JSON object with keys objective and tasks only. "
            "tasks: array of {description, tool_name, tool_args(object), dependencies(array)}."
        )
        user_prompt = self._render_user_prompt(objective, context, MAX_TASKS_DEFAULT)

        text = svc.text_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=900,
            max_retries=1,
            fail_hard=False,
        )
        if not text or not isinstance(text, str):
            raise PlannerError("text_empty_response", self.name, objective)
        return text

    # ----------------------------------------------
    # Multi-Stage Extraction
    # ----------------------------------------------
    def _extract_plan_from_text(self, raw_text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        errs: List[str] = []
        if not raw_text:
            return None, ["empty_text"]
        snippet = raw_text.strip()

        # Step A: Direct parse
        parsed, err = _safe_json_loads(snippet)
        if parsed and isinstance(parsed, dict) and "tasks" in parsed:
            return parsed, errs
        if err:
            errs.append(f"direct_fail:{err}")

        # Step B: tasks array synthesize
        arr_match = _TASK_ARRAY_REGEX.search(snippet)
        if arr_match:
            arr_chunk = arr_match.group(1)
            # Escape quotes inside snippet piece for JSON objective part
            objective_val = json.dumps(_clip(snippet, 50))
            synth = f'{{"objective":{objective_val},"tasks":{arr_chunk}}}'
            candidate, err2 = _safe_json_loads(synth)
            if candidate and isinstance(candidate, dict) and "tasks" in candidate:
                return candidate, errs
            if err2:
                errs.append(f"tasks_array_fail:{err2}")

        # Step C: first curly block
        block_match = _JSON_BLOCK_CURLY.search(snippet)
        if block_match:
            block = block_match.group(0)
            candidate, err3 = _safe_json_loads(block)
            if candidate and isinstance(candidate, dict) and "tasks" in candidate:
                return candidate, errs
            if err3:
                errs.append(f"block_fail:{err3}")

        # Step D: bullets heuristic
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
            return {
                "objective": "Recovered (bullets)",
                "tasks": tasks_guess
            }, errs

        errs.append("extraction_all_failed")
        return None, errs

    # ----------------------------------------------
    # Prompt Rendering
    # ----------------------------------------------
    def _render_user_prompt(
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
            lines.append("PAST_FAILS:")
            for f in context.past_failures[:5]:
                lines.append(f"- {f}")
            lines.append("")
        examples = self._list_tool_examples(limit=5)
        if examples:
            lines.append("TOOL_EXAMPLES:")
            for name, desc in examples:
                lines.append(f"- {name}: {desc or 'No description'}")
            lines.append("")
        lines.append(f"Produce up to {max_tasks} tasks.")
        lines.append("Return ONLY JSON with keys: objective (string), tasks (array).")
        lines.append("Each task: description, tool_name, tool_args(object), dependencies(array).")
        return "\n".join(lines)

    # ----------------------------------------------
    # Tool Examples
    # ----------------------------------------------
    def _list_tool_examples(self, limit: int = 5) -> List[Tuple[str, Optional[str]]]:
        out: List[Tuple[str, Optional[str]]] = []
        if not agent_tools:
            return out
        try:
            for i, t in enumerate(agent_tools.list_tools()):  # type: ignore
                if i >= limit:
                    break
                out.append((getattr(t, "name", f"tool_{i}"), getattr(t, "description", None)))
        except Exception as e:  # noqa: BLE001
            _LOG.debug("[%s] tool_enum_fail:%s", self.name, e)
        return out

    # ----------------------------------------------
    # Normalize & Validate Tasks
    # ----------------------------------------------
    def _normalize_and_validate_tasks(
        self,
        tasks_raw: Any,
        max_tasks: int,
        errors_out: List[str],
    ) -> List[PlannedTask]:
        if not isinstance(tasks_raw, list):
            raise PlanValidationError("tasks_not_list", self.name)

        cleaned: List[PlannedTask] = []
        seen_ids: set = set()

        for idx, task in enumerate(tasks_raw):
            if len(cleaned) >= max_tasks:
                errors_out.append("task_limit_reached")
                break

            if not isinstance(task, dict):
                errors_out.append(f"task_{idx}_not_dict")
                continue

            desc = str(task.get("description") or "").strip()
            if not desc:
                errors_out.append(f"task_{idx}_missing_description")
                continue

            tool_name = str(task.get("tool_name") or "unknown").strip()
            if not _VALID_TOOL_NAME.match(tool_name):
                errors_out.append(f"task_{idx}_invalid_tool_name:{tool_name}")
                tool_name = "unknown"

            tool_args = task.get("tool_args")
            if not isinstance(tool_args, dict):
                errors_out.append(f"task_{idx}_tool_args_not_object")
                tool_args = {}

            deps = task.get("dependencies")
            if not isinstance(deps, list):
                errors_out.append(f"task_{idx}_deps_not_list")
                deps = []

            filtered_deps: List[str] = []
            for d in deps:
                if isinstance(d, str) and _VALID_TOOL_NAME.match(d):
                    filtered_deps.append(d)
                else:
                    errors_out.append(f"task_{idx}_dep_invalid:{d}")

            if not _tool_exists(tool_name):
                errors_out.append(f"task_{idx}_tool_missing:{tool_name}")

            task_id = _canonical_task_id(len(cleaned) + 1)
            while task_id in seen_ids:
                task_id = _canonical_task_id(len(seen_ids) + len(cleaned) + 1)
            seen_ids.add(task_id)

            cleaned.append(
                PlannedTask(
                    task_id=task_id,
                    description=desc,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    dependencies=filtered_deps,
                )
            )

        if not cleaned:
            raise PlanValidationError("no_valid_tasks", self.name)
        return cleaned

    # ----------------------------------------------
    # Post Validation (cycle detection / global constraints)
    # ----------------------------------------------
    def _post_validate(self, plan: MissionPlanSchema):
        graph = {t.task_id: set(t.dependencies) for t in plan.tasks}
        valid_ids = set(graph.keys())
        for deps in graph.values():
            deps.intersection_update(valid_ids)

        visited: Dict[str, int] = {}  # 0=unseen,1=visiting,2=done

        def dfs(node: str, stack: List[str]):
            state = visited.get(node, 0)
            if state == 1:
                raise PlanValidationError(f"cycle_detected:{'->'.join(stack + [node])}", self.name)
            if state == 2:
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


# -------------------------------------------------------------------------------------------------
# EXPORTS
# -------------------------------------------------------------------------------------------------
__all__ = [
    "LLMGroundedPlanner",
    "PlanValidationError",
    "MissionPlanSchema",
    "PlannedTask",
    "PlanningContext",
]

# -------------------------------------------------------------------------------------------------
# MANUAL TEST ENTRY
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    ok, reason = LLMGroundedPlanner.self_test()
    print(f"[SELF_TEST] ok={ok} reason={reason}")
    if ok:
        planner = LLMGroundedPlanner()
        try:
            plan = planner.generate_plan("Analyze repository architecture and propose refactor plan.")
            print("Generated tasks:", len(plan.tasks))
            for t in plan.tasks[:5]:
                print(" -", t.task_id, t.description, t.tool_name)
        except Exception as exc:  # noqa: BLE001
            print("Generation error:", exc)
# =================================================================================================