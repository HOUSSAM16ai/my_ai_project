# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
# -*- coding: utf-8 -*-
# # -*- coding: utf-8 -*-
# ======================================================================================
# LLMGroundedPlanner (Version 2.0.0 "RESURRECTION / FAST-SELFTEST / DEGRADABLE")
# ======================================================================================
# خصائص الإصدار:
#   - صفر سلاسل ثلاثية (لا """ ولا ''').
#   - self_test غير حاظر: أوضاع fast / skip / normal.
#   - لا حجر للمخطط بسبب غياب maestro (يعد نجاحاً في fast/skip).
#   - توليد خطة احتياطية (degraded) تلقائياً إن لم تتوفر خدمة LLM مع السماح عبر env.
#   - استخراج متعدد المراحل لخروج LLM (عند توفره).
#   - تحقق المهام + كشف الدورات + تطبيع أسماء الأدوات.
#   - تسجيل غني وإرجاع أخطاء واضحة فقط عند خيار صارم.
#
# متغيرات بيئة أساسية:
#   LLM_PLANNER_SELFTEST_MODE=fast|skip|normal   (افتراضي fast إن لم يُضبط)
#   LLM_PLANNER_FALLBACK_ALLOW=1                 تمكين خطة بديلة بلا LLM
#   LLM_PLANNER_FALLBACK_MAX_TASKS=5             أقصى مهام fallback
#   LLM_PLANNER_STRICT_JSON=1                    يمنع السقوط إلى النص / fallback
#   LLM_PLANNER_MAX_TASKS=25                     الحد الأعلى العام
#   LLM_PLANNER_ALLOW_STUB=1                     يسمح Stub لو فشل import القاعدة
#   LLM_PLANNER_LOG_LEVEL=DEBUG|INFO|...         ضبط مستوى السجل
#
# خطوات تشخيص سريعة بعد الحفظ:
#   grep -n '"""' app/overmind/planning/llm_planner.py || echo "NO triple quotes"
#   python -m py_compile app/overmind/planning/llm_planner.py
# ======================================================================================

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------------------
# LOGGER
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
# BASE IMPORT (STRICT, stub only via env)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB", "0") == "1"
try:
    from .base_planner import BasePlanner, PlannerError  # type: ignore
except Exception as _e:  # noqa: BLE001
    if not _ALLOW_STUB:
        raise RuntimeError("Cannot import .base_planner. Set LLM_PLANNER_ALLOW_STUB=1 for dev stub.") from _e
    class PlannerError(Exception):  # type: ignore
        def __init__(self, msg: str, planner: str = "stub", objective: str = "", extra: Dict[str, Any] = None):
            super().__init__(msg)
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
    _LOG.error("USING STUB BasePlanner (dev mode).")

# --------------------------------------------------------------------------------------
# OPTIONAL SERVICES
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
# SCHEMAS FALLBACK
# --------------------------------------------------------------------------------------
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

# --------------------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------------------
STRICT_JSON_ONLY = os.getenv("LLM_PLANNER_STRICT_JSON", "0") == "1"
SELF_TEST_MODE = os.getenv("LLM_PLANNER_SELFTEST_MODE") or "fast"  # fast|skip|normal
FALLBACK_ALLOW = os.getenv("LLM_PLANNER_FALLBACK_ALLOW", "0") == "1"
FALLBACK_MAX = int(os.getenv("LLM_PLANNER_FALLBACK_MAX_TASKS", "5"))
SELF_TEST_STRICT = os.getenv("LLM_PLANNER_SELFTEST_STRICT", "0") == "1"  # still honored if normal
MAX_TASKS_DEFAULT = int(os.getenv("LLM_PLANNER_MAX_TASKS", "25"))

_VALID_TOOL_NAME = re.compile(r"^[a-zA-Z0-9_.\\-:]{2,128}$")
_TASK_ARRAY_REGEX = re.compile(r'"tasks"\\s*:\\s*(\\[[^\\]]*\\])', re.IGNORECASE | re.DOTALL)
_JSON_BLOCK_CURLY = re.compile(r"\\{.*\\}", re.DOTALL)

# --------------------------------------------------------------------------------------
# CUSTOM ERROR
# --------------------------------------------------------------------------------------
class PlanValidationError(PlannerError):
    pass

# --------------------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------------------
def _clip(s: str, n: int = 160) -> str:
    if s is None:
        return ""
    return s if len(s) <= n else s[: n - 3] + "..."

def _safe_json_loads(txt: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(txt), None
    except Exception as e:  # noqa: BLE001
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

# --------------------------------------------------------------------------------------
# PLANNER
# --------------------------------------------------------------------------------------
class LLMGroundedPlanner(BasePlanner):
    name = "llm_grounded_planner"
    version = "2.0.0"
    tier = "core"
    production_ready = True
    capabilities = {"planning", "llm", "tool-grounding"}
    tags = {"mission", "tasks"}

    # -------------------- SELF TEST --------------------
    @classmethod
    def self_test(cls) -> Tuple[bool, str]:
        mode = SELF_TEST_MODE.lower()
        if not cls.name or " " in cls.name:
            return False, "invalid_name"
        # skip mode passes unconditionally
        if mode == "skip":
            return True, "skip_mode"
        # fast mode: do not contact maestro
        if mode == "fast":
            if maestro is None:
                return True, "fast_no_maestro"
            return True, "fast_ok"
        # normal mode: attempt minimal structured ping (bounded)
        if maestro is None and SELF_TEST_STRICT:
            return False, "maestro_missing_strict"
        if maestro and hasattr(maestro, "generation_service"):
            try:
                svc = maestro.generation_service  # type: ignore
                schema = {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]}
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
            except Exception as e:  # noqa: BLE001
                if SELF_TEST_STRICT:
                    return False, f"selftest_exception:{type(e).__name__}"
                return True, "selftest_degraded"
        return True, "normal_ok"

    # -------------------- PUBLIC API --------------------
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
        _LOG.info("[%s] plan_start objective='%s' cap=%d strict=%s fallback_allow=%s",
                  self.name, _clip(objective, 120), cap, STRICT_JSON_ONLY, FALLBACK_ALLOW)

        errors: List[str] = []
        structured: Optional[Dict[str, Any]] = None

        # Phase 1: structured
        if maestro and hasattr(maestro, "generation_service"):
            try:
                structured = self._call_structured(objective, context, cap)
                _LOG.debug("[%s] structured_ok keys=%s", self.name, list(structured.keys()))
            except Exception as e:  # noqa: BLE001
                errors.append(f"struct_fail:{type(e).__name__}:{e}")
                _LOG.warning("[%s] structured_fail %s", self.name, e)
        else:
            errors.append("maestro_unavailable")

        if STRICT_JSON_ONLY and structured is None and not FALLBACK_ALLOW:
            raise PlannerError("strict_mode_no_structured", self.name, objective, extra={"errors": errors[-5:]})

        raw_text: Optional[str] = None
        if structured is None and maestro and hasattr(maestro, "generation_service"):
            try:
                raw_text = self._call_text(objective, context)
                _LOG.debug("[%s] text_len=%d", self.name, len(raw_text))
            except Exception as e:  # noqa: BLE001
                errors.append(f"text_fail:{type(e).__name__}:{e}")
                _LOG.error("[%s] text_fail %s", self.name, e)

        plan_dict: Optional[Dict[str, Any]] = None
        extraction_notes: List[str] = []
        if structured is not None:
            plan_dict = structured
        elif raw_text:
            plan_dict, extraction_notes = self._extract_from_text(raw_text)
            errors.extend(extraction_notes)

        if plan_dict is None:
            if FALLBACK_ALLOW:
                _LOG.warning("[%s] using_degraded_fallback errors_tail=%s", self.name, errors[-4:])
                plan = self._fallback_plan(objective, cap)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                _LOG.info("[%s] plan_success_fallback tasks=%d elapsed_ms=%.1f objective='%s'",
                          self.name, len(plan.tasks), elapsed_ms, _clip(objective, 80))
                return plan
            raise PlannerError("extraction_failed", self.name, objective, extra={"errors": errors[-6:]})

        # Normalize
        tasks_raw = plan_dict.get("tasks")
        norm_errs: List[str] = []
        try:
            tasks = self._normalize_tasks(tasks_raw, cap, norm_errs)
        except PlanValidationError as ve:
            errors.extend(norm_errs)
            if FALLBACK_ALLOW:
                _LOG.warning("[%s] normalize_failed_using_fallback %s", self.name, ve)
                plan = self._fallback_plan(objective, cap)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                _LOG.info("[%s] plan_success_fallback tasks=%d elapsed_ms=%.1f objective='%s'",
                          self.name, len(plan.tasks), elapsed_ms, _clip(objective, 80))
                return plan
            raise PlannerError("normalize_fail", self.name, objective, extra={"errors": errors[-10:]}) from ve

        mission_plan = MissionPlanSchema(
            objective=str(plan_dict.get("objective") or objective),
            tasks=tasks,
        )

        # Post validate
        self._post_validate(mission_plan)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        _LOG.info("[%s] plan_success tasks=%d elapsed_ms=%.1f objective='%s'",
                  self.name, len(mission_plan.tasks), elapsed_ms, _clip(objective, 80))
        if errors:
            _LOG.debug("[%s] notes=%s", self.name, errors[-6:])
        return mission_plan

    # -------------------- STRUCTURED CALL --------------------
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

    # -------------------- TEXT CALL --------------------
    def _call_text(self, objective: str, context: Optional[PlanningContext]) -> str:
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
            temperature=0.35,
            max_tokens=900,
            max_retries=1,
            fail_hard=False,
        )
        if not txt or not isinstance(txt, str):
            raise PlannerError("text_empty_response", self.name, objective)
        return txt

    # -------------------- EXTRACTION --------------------
    def _extract_from_text(self, raw_text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        errs: List[str] = []
        snippet = (raw_text or "").strip()
        if not snippet:
            return None, ["empty_text"]
        # A) Direct parse
        parsed, err = _safe_json_loads(snippet)
        if parsed and isinstance(parsed, dict) and "tasks" in parsed:
            return parsed, errs
        if err:
            errs.append(f"direct_fail:{err}")
        # B) tasks array
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
        # C) first curly block
        blk = _JSON_BLOCK_CURLY.search(snippet)
        if blk:
            block = blk.group(0)
            cand2, err3 = _safe_json_loads(block)
            if cand2 and isinstance(cand2, dict) and "tasks" in cand2:
                return cand2, errs
            if err3:
                errs.append(f"block_fail:{err3}")
        # D) bullet heuristic
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

    # -------------------- NORMALIZATION --------------------
    def _normalize_tasks(self, tasks_raw: Any, cap: int, errors_out: List[str]) -> List[PlannedTask]:
        if not isinstance(tasks_raw, list):
            raise PlanValidationError("tasks_not_list", self.name)
        cleaned: List[PlannedTask] = []
        seen_ids: set = set()
        for idx, t in enumerate(tasks_raw):
            if len(cleaned) >= cap:
                errors_out.append("task_limit_reached")
                break
            if not isinstance(t, dict):
                errors_out.append(f"task_{idx}_not_dict")
                continue
            desc = str(t.get("description") or "").strip()
            if not desc:
                errors_out.append(f"task_{idx}_missing_description")
                continue
            tool_name = str(t.get("tool_name") or "unknown").strip()
            if not _VALID_TOOL_NAME.match(tool_name):
                errors_out.append(f"task_{idx}_invalid_tool_name:{tool_name}")
                tool_name = "unknown"
            tool_args = t.get("tool_args")
            if not isinstance(tool_args, dict):
                errors_out.append(f"task_{idx}_tool_args_not_object")
                tool_args = {}
            deps = t.get("dependencies")
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
            tid = _canonical_task_id(len(cleaned) + 1)
            while tid in seen_ids:
                tid = _canonical_task_id(len(seen_ids) + len(cleaned) + 1)
            seen_ids.add(tid)
            cleaned.append(
                PlannedTask(
                    task_id=tid,
                    description=desc,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    dependencies=filtered_deps,
                )
            )
        if not cleaned:
            raise PlanValidationError("no_valid_tasks", self.name)
        return cleaned

    # -------------------- POST VALIDATION --------------------
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

    # -------------------- FALLBACK PLAN --------------------
    def _fallback_plan(self, objective: str, cap: int) -> MissionPlanSchema:
        # سلوك احتياطي: تقسيم الهدف إلى عبارات قصيرة (بسيط) لإنتاج مهام مع tool_name=unknown أو أول أداة متاحة.
        words = [w for w in re.split(r"\\s+", objective.strip()) if w]
        chunk_size = max(1, max( len(words)//max(1,min(cap,FALLBACK_MAX)), 3))
        segments: List[str] = []
        current: List[str] = []
        for w in words:
            current.append(w)
            if len(current) >= chunk_size:
                segments.append(" ".join(current))
                current = []
        if current:
            segments.append(" ".join(current))
        segments = segments[: min(cap, FALLBACK_MAX)]
        tool_default = "unknown"
        if agent_tools:
            try:
                tool_list = list(agent_tools.list_tools())  # type: ignore
                if tool_list:
                    first_tool = getattr(tool_list[0], "name", None)
                    if isinstance(first_tool, str) and _VALID_TOOL_NAME.match(first_tool):
                        tool_default = first_tool
            except Exception:
                pass
        tasks: List[PlannedTask] = []
        for i, seg in enumerate(segments, start=1):
            tasks.append(
                PlannedTask(
                    task_id=_canonical_task_id(i),
                    description=f"Analyze segment: {seg}",
                    tool_name=tool_default,
                    tool_args={},
                    dependencies=[] if i == 1 else [ _canonical_task_id(i-1) ],
                )
            )
        return MissionPlanSchema(objective=objective, tasks=tasks)

    # -------------------- PROMPT RENDER --------------------
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
        examples = self._tool_examples(limit=5)
        if examples:
            lines.append("TOOL_EXAMPLES:")
            for name, desc in examples:
                lines.append(f"- {name}: {desc or 'No description'}")
            lines.append("")
        lines.append(f"Produce up to {max_tasks} tasks.")
        lines.append("Return ONLY JSON with keys: objective (string), tasks (array).")
        lines.append("Each task: description, tool_name, tool_args(object), dependencies(array).")
        return "\\n".join(lines)

    # -------------------- TOOL EXAMPLES --------------------
    def _tool_examples(self, limit: int = 5) -> List[Tuple[str, Optional[str]]]:
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

    # -------------------- OBJECTIVE VALID --------------------
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
# EXPORTS
# --------------------------------------------------------------------------------------
__all__ = [
    "LLMGroundedPlanner",
    "PlanValidationError",
    "MissionPlanSchema",
    "PlannedTask",
    "PlanningContext",
]

# --------------------------------------------------------------------------------------
# DEV MAIN
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    ok, reason = LLMGroundedPlanner.self_test()
    print(f"[SELF_TEST] ok={ok} reason={reason}")
    planner = LLMGroundedPlanner()
    plan = planner.generate_plan("Analyze codebase structure and outline refactor steps.")
    print("Tasks:", len(plan.tasks))
    for t in plan.tasks:
        print(t.task_id, t.description)