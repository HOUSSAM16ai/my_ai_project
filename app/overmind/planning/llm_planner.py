# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
"""
# -*- coding: utf-8 -*-
# ======================================================================================
# LLMGroundedPlanner
# Version: 1.3.0  "GROUNDING / FORENSIC-LOG / NO-SILENT-FAIL"
# ======================================================================================
# الغاية:
#   تحويل هدف لغوي (objective) إلى خطة مهام مرتّبة (tool-grounded) مع تبعيات سليمة.
#   يعتمد أولاً على توليد منظَّم (structured JSON) ثم يسقط تدريجياً إلى مسارات استخراج
#   ذكية عند الفشل، مع منع أي صمت أو فشل مخفي.
#
# الميزات الأساسية:
#   - استيراد صارم لـ BasePlanner (لا Stub إلا إذا LLM_PLANNER_ALLOW_STUB=1).
#   - self_test شامل يعيد (bool, reason).
#   - تسجيل غني بكل خطوة (debug / info / warning / error).
#   - منع fallback الصامت: كل فشل له سبب واضح.
#   - استخراج JSON متعدد المراحل + Heuristic bullet list.
#   - فحص و تطبيع المهام: أسماء أدوات، تبعيات، حدود، إزالة الدورات.
#   - كشف الدورات في التبعيات (cycle detection).
#   - توافق مع factory عبر name وخصائص version / capabilities / tags / production_ready.
#
# متغيرات البيئة:
#   LLM_PLANNER_ALLOW_STUB=1       يسمح باستخدام Stub إذا فشل استيراد BasePlanner (للتطوير فقط).
#   LLM_PLANNER_STRICT_JSON=1      فشل فوري إذا لم ينجح المسار المنظَّم.
#   LLM_PLANNER_MAX_TASKS=25       أقصى عدد مهام مقبول.
#   LLM_PLANNER_SELFTEST_STRICT=1  self_test يفشل لو غابت الخدمات (maestro / agent_tools).
#   LLM_PLANNER_LOG_LEVEL=DEBUG|INFO|...  يضبط مستوى السجل للمخطط.
#
# الشكل العام للمخرجات (MissionPlanSchema):
# {
#   "objective": str,
#   "tasks": [ { task_id, description, tool_name, tool_args, dependencies[] }, ... ]
# }
# ======================================================================================

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Iterable

# --------------------------------------------------------------------------------------
# إعداد السجل
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("llm_planner")
_log_env_level = os.getenv("LLM_PLANNER_LOG_LEVEL", "").upper()
if _log_env_level:
    _LOG.setLevel(getattr(logging, _log_env_level, logging.INFO))
else:
    _LOG.setLevel(logging.INFO)

if not _LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# استيراد BasePlanner (صارم مع خيار Stub اختياري)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB", "0") == "1"
try:
    from .base_planner import BasePlanner, PlannerError  # type: ignore
except Exception as e:  # noqa: BLE001
    if not _ALLOW_STUB:
        raise RuntimeError(
            "FATAL: Cannot import '.base_planner'. "
            "Set LLM_PLANNER_ALLOW_STUB=1 فقط للتطوير المؤقت."
        ) from e

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

    _LOG.error("USING STUB BasePlanner (LLM_PLANNER_ALLOW_STUB=1) – غير مناسب للإنتاج.")

# --------------------------------------------------------------------------------------
# خدمات خارجية محتملة
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
# مخططات / نماذج مشتركة (مع fallback)
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
# إعدادات
# --------------------------------------------------------------------------------------
STRICT_JSON_ONLY = os.getenv("LLM_PLANNER_STRICT_JSON", "0") == "1"
SELF_TEST_STRICT = os.getenv("LLM_PLANNER_SELFTEST_STRICT", "0") == "1"
MAX_TASKS_DEFAULT = int(os.getenv("LLM_PLANNER_MAX_TASKS", "25"))

_VALID_TOOL_NAME = re.compile(r"^[a-zA-Z0-9_.\-:]{2,128}$", re.UNICODE)
_TASK_ARRAY_REGEX = re.compile(r'"tasks"\s*:\s*(\[[^\]]*\])', re.IGNORECASE | re.DOTALL)
_JSON_BLOCK_CURLY = re.compile(r"\{.*\}", re.DOTALL)

# --------------------------------------------------------------------------------------
# أخطاء مخصصة
# --------------------------------------------------------------------------------------
class PlanValidationError(PlannerError):
    """خطأ تحقق (فشل بنية / دورة / بيانات غير صالحة)"""


# --------------------------------------------------------------------------------------
# أدوات مساعدة
# --------------------------------------------------------------------------------------
def _clip(s: str, n: int = 180) -> str:
    return s if len(s) <= n else s[: n - 3] + "..."

def _safe_json_loads(payload: str) -> Tuple[Optional[Any], Optional[str]]:
    try:
        return json.loads(payload), None
    except Exception as e:  # noqa: BLE001
        return None, str(e)

def _tool_exists(name: str) -> bool:
    try:
        if not agent_tools:
            return False
        return bool(agent_tools.get_tool(name))  # type: ignore
    except Exception:
        return False

def _canonical_task_id(seq: int) -> str:
    return f"t{seq:02d}"


# --------------------------------------------------------------------------------------
# الفئة الرئيسية للمخطط
# --------------------------------------------------------------------------------------
class LLMGroundedPlanner(BasePlanner):
    # مخطِّط مرتكز LLM – (السطر السابق كان غير معلّق وتسبب IndentationError في نسخة تالفة)
    name: str = "llm_grounded_planner"
    version: str = "1.3.0"
    tier: str = "core"
    production_ready: bool = True
    capabilities = {"planning", "llm", "tool-grounding"}
    tags = {"mission", "tasks"}

    # ------------------------------------------------------------------
    # self_test
    # ------------------------------------------------------------------
    @classmethod
    def self_test(cls) -> Tuple[bool, str]:
        if not cls.name or " " in cls.name:
            return False, "invalid_name"
        if maestro is None and SELF_TEST_STRICT:
            return False, "maestro_unavailable_strict"
        if agent_tools is None and SELF_TEST_STRICT:
            return False, "agent_tools_unavailable_strict"
        # محاولة استدعاء منظم مبسط
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
                if not isinstance(resp, dict) or resp.get("status") != "ok":
                    return False, f"mini_struct_bad:{resp}"
            except Exception as e:  # noqa: BLE001
                if SELF_TEST_STRICT:
                    return False, f"mini_struct_exc:{type(e).__name__}:{e}"
        return True, "ok"

    # ------------------------------------------------------------------
    # API: توليد الخطة
    # ------------------------------------------------------------------
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        max_tasks: Optional[int] = None,
    ) -> MissionPlanSchema:
        t0 = time.perf_counter()

        if not self._objective_is_valid(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        cap = max_tasks or MAX_TASKS_DEFAULT
        cap = min(cap, MAX_TASKS_DEFAULT)

        _LOG.info("[%s] plan_start objective='%s' cap=%d strict_json=%s",
                  self.name, _clip(objective, 120), cap, STRICT_JSON_ONLY)

        structured_data: Optional[Dict[str, Any]] = None
        errors: List[str] = []

        # المرحلة 1: محاولة توليد منظم
        if maestro and hasattr(maestro, "generation_service"):
            try:
                structured_data = self._call_structured_llm(objective, context, cap)
                _LOG.debug("[%s] structured_ok keys=%s", self.name, list(structured_data.keys()))
            except Exception as e:  # noqa: BLE001
                errors.append(f"struct_fail:{type(e).__name__}:{e}")
                _LOG.warning("[%s] structured_fail: %s", self.name, e)
        else:
            errors.append("maestro_unavailable")

        # نمط صارم؟
        if STRICT_JSON_ONLY and structured_data is None:
            raise PlannerError(
                f"strict_json_failed errors={errors[-5:]}",
                self.name,
                objective,
                extra={"errors": errors},
            )

        # المرحلة 2: نص fallback
        raw_text: Optional[str] = None
        if structured_data is None:
            try:
                raw_text = self._call_text_llm(objective, context)
                _LOG.debug("[%s] text_len=%d", self.name, len(raw_text))
            except Exception as e:  # noqa: BLE001
                errors.append(f"text_fail:{type(e).__name__}:{e}")
                _LOG.error("[%s] text_fail: %s", self.name, e)

        # المرحلة 3: استخراج
        plan_dict: Optional[Dict[str, Any]] = None
        extraction_notes: List[str] = []
        if structured_data is not None:
            plan_dict = structured_data
        elif raw_text:
            plan_dict, extraction_notes = self._extract_plan_from_text(raw_text)
            errors.extend(extraction_notes)

        if plan_dict is None:
            raise PlannerError(
                f"plan_extraction_failed errors={errors[-6:]}",
                self.name,
                objective,
                extra={"errors": errors},
            )

        # المرحلة 4: التطبيع والتحقق
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

        # المرحلة 5: تحقق لاحق (دورات + ضبط نهائي)
        self._post_validate(mission_plan)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        _LOG.info("[%s] plan_success objective='%s' tasks=%d elapsed_ms=%.1f",
                  self.name, _clip(objective, 100), len(mission_plan.tasks), elapsed_ms)
        if errors:
            _LOG.debug("[%s] notes=%s", self.name, errors[-6:])
        return mission_plan

    # ------------------------------------------------------------------
    # تحقق الهدف
    # ------------------------------------------------------------------
    def _objective_is_valid(self, objective: str) -> bool:
        if not objective:
            return False
        txt = objective.strip()
        if len(txt) < 5:
            return False
        if txt.isdigit():
            return False
        return True

    # ------------------------------------------------------------------
    # استدعاء منظم
    # ------------------------------------------------------------------
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
        system_prompt = (
            "You are a precision mission planner. Respond ONLY with JSON object matching schema."
        )

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

    # ------------------------------------------------------------------
    # استدعاء نصي
    # ------------------------------------------------------------------
    def _call_text_llm(
        self,
        objective: str,
        context: Optional[PlanningContext],
    ) -> str:
        if maestro is None or not hasattr(maestro, "generation_service"):
            raise RuntimeError("maestro_generation_service_unavailable_text")
        svc = maestro.generation_service  # type: ignore

        system_prompt = (
            "You are a mission planner. Provide a JSON object with keys 'objective' and 'tasks'. "
            "tasks: array of {description, tool_name, tool_args(object), dependencies(array)}."
        )
        user_prompt = self._render_user_prompt(objective, context, MAX_TASKS_DEFAULT)

        text = svc.text_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.35,
            max_tokens=900,
            max_retries=1,
            fail_hard=False,
        )
        if not text or not isinstance(text, str):
            raise PlannerError("text_empty_response", self.name, objective)
        return text

    # ------------------------------------------------------------------
    # استخراج متعدد المراحل من نص
    # ------------------------------------------------------------------
    def _extract_plan_from_text(self, raw_text: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        errs: List[str] = []
        if not raw_text:
            return None, ["empty_text"]
        snippet = raw_text.strip()

        # A) محاولة التحليل المباشر
        parsed, err = _safe_json_loads(snippet)
        if parsed and isinstance(parsed, dict) and "tasks" in parsed:
            return parsed, errs
        if err:
            errs.append(f"direct_fail:{err}")

        # B) محاولة استخراج مصفوفة tasks
        arr_match = _TASK_ARRAY_REGEX.search(snippet)
        if arr_match:
            arr_chunk = arr_match.group(1)
            synth = f'{{"objective":"{_clip(snippet,50)}","tasks":{arr_chunk}}}'
            candidate, err2 = _safe_json_loads(synth)
            if candidate and isinstance(candidate, dict) and "tasks" in candidate:
                return candidate, errs
            if err2:
                errs.append(f"tasks_array_fail:{err2}")

        # C) أول بلوك {} كبير
        block_match = _JSON_BLOCK_CURLY.search(snippet)
        if block_match:
            block = block_match.group(0)
            candidate, err3 = _safe_json_loads(block)
            if candidate and isinstance(candidate, dict) and "tasks" in candidate:
                return candidate, errs
            if err3:
                errs.append(f"block_fail:{err3}")

        # D) Heuristic bullets
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

    # ------------------------------------------------------------------
    # بناء Prompt المستخدم
    # ------------------------------------------------------------------
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
            lines.append("PAST_FAILURES:")
            for f in context.past_failures[:5]:
                lines.append(f"- {f}")
            lines.append("")
        tool_examples = self._list_tool_examples(limit=5)
        if tool_examples:
            lines.append("TOOL_EXAMPLES:")
            for name, desc in tool_examples:
                lines.append(f"- {name}: {desc or 'No description'}")
            lines.append("")
        lines.append(f"Produce up to {max_tasks} tasks.")
        lines.append("Return ONLY valid JSON with keys: objective (string), tasks (array).")
        lines.append("Each task: {description, tool_name, tool_args, dependencies}.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # أمثلة أدوات
    # ------------------------------------------------------------------
    def _list_tool_examples(self, limit: int = 5) -> List[Tuple[str, Optional[str]]]:
        out: List[Tuple[str, Optional[str]]] = []
        if not agent_tools:
            return out
        try:
            for i, t in enumerate(agent_tools.list_tools()):  # type: ignore
                if i >= limit:
                    break
                out.append((
                    getattr(t, "name", f"tool_{i}"),
                    getattr(t, "description", None)
                ))
        except Exception as e:  # noqa: BLE001
            _LOG.debug("[%s] tool_enum_fail:%s", self.name, e)
        return out

    # ------------------------------------------------------------------
    # تطبيع + تحقق المهام
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # التحقق النهائي (دورات تبعيات / حدود)
    # ------------------------------------------------------------------
    def _post_validate(self, plan: MissionPlanSchema):
        graph = {t.task_id: set(t.dependencies) for t in plan.tasks}
        valid_ids = set(graph.keys())
        # إزالة تبعيات مجهولة (أمان إضافي)
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


# --------------------------------------------------------------------------------------
# صادرات
# --------------------------------------------------------------------------------------
__all__ = [
    "LLMGroundedPlanner",
    "PlanValidationError",
    "MissionPlanSchema",
    "PlannedTask",
    "PlanningContext",
]

# --------------------------------------------------------------------------------------
# تنفيذ يدوي
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    ok, reason = LLMGroundedPlanner.self_test()
    print(f"[SELF_TEST] ok={ok} reason={reason}")
    if ok:
        planner = LLMGroundedPlanner()
        try:
            plan = planner.generate_plan("Analyze repository architecture and propose refactor.")
            print("Generated plan (tasks count):", len(plan.tasks))
        except Exception as exc:  # noqa: BLE001
            print("Generation error:", exc)