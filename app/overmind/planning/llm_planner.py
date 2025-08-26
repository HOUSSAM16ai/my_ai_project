# app/overmind/planning/llm_planner.py
# ======================================================================================
#  MAESTRO GRAPH PLANNER (v4.1 • "ZERO‑STALL / MULTI‑FALLBACK / SMARTFAST / RESILIENT") #
# ======================================================================================
# PURPOSE:
#   تحويل هدف لغوي (Objective) إلى خطة مهام (DAG) صالحة (MissionPlanSchema) بسرعة واعتمادية
#   مع الحد الأقصى من إزالة جذور مهلة التخطيط (PlannerTimeoutError) للأهداف
#   البسيطة والمتوسطة والتحليلية القصيرة، مع تحسينات قوية في تنظيف / استرجاع JSON.
#
# MAIN ENHANCEMENTS vs 3.0.0:
#   1) SMART FAST PATHS:
#        - File objectives (موجود سابقاً)
#        - Greeting / simple output ("hi", "say hi", "hello", تحيات عربية) حتى لو قصيرة جداً
#        - Simple enumerate / list (e.g. "list three benefits of ...")
#   2) SHORT OBJECTIVE AUTO-AUGMENT:
#        - الأهداف القصيرة جداً (< 3 أو < 4) تُوسّع تلقائياً لتصبح وصفاً قابلاً للمعالجة
#          بدلاً من الفشل المباشر (يمكن تعطيلها ببيئة PLANNER_STRICT_SHORT=1).
#   3) MULTI-STAGE JSON RECOVERY:
#        - استخراج أول/أوسع كتلة أقواس {}
#        - المحاولة بنمط regex متعدد
#        - تنقية code fences + Markdown + تعليقات
#        - إصلاح الفواصل الزائدة
#        - إصلاح استبدال علامات اقتباس أحادية إلى مزدوجة إذا لم ينجح التحليل
#        - محاولة json5 (اختياري) إذا متاح (بدون فشل لو غير متوفر)
#        - محاولة تفكيك المصفوفة "tasks" يدوياً عند فشل شامل
#   4) EARLY EXIT & ADAPTIVE DEGRADATION:
#        - مراقبة ميزانية الوقت الداخلية: إذا بقي < (LOW_TIME_THRESHOLD) يتجه فوراً
#          لخطة fallback بدون إعادة محاولات عديمة الجدوى.
#   5) IMPROVED FALLBACK STRATEGY:
#        - مستويات: minimal → generic_think multi-steps (تحليل → تنفيذ) حسب طول الهدف
#        - تحكم عبر PLANNER_FALLBACK_MODE (minimal | dual | analytic)
#   6) PROMPT ADAPTATION:
#        - تقليص أقسام السياق مع كل محاولة فاشلة
#        - تقليص max_tasks ديناميكياً عند المحاولة التالية
#   7) LOGGING TRACE (عند PLANNER_LOG_VERBOSE=1):
#        - مراحل sanitization
#        - مدة كل محاولة LLM
#        - أداة fallback المستخدمة
#   8) CONFIGURABLE GREETING / LIST FAST PATH عبر PLANNER_ENABLE_SMARTFAST
#
# CONFIG (ENV):
#   PLANNER_TIMEOUT_SECONDS          (float)  المهلة الكلية (افتراضي 50.0)
#   PLANNER_RETRY_ATTEMPTS           (int)    محاولات إعادة النداء (افتراضي 3)
#   PLANNER_FAST_PATH=0/1            تمكين fast file path (افتراضي 1)
#   PLANNER_ENABLE_SMARTFAST=0/1     تمكين fast path للأهداف التحيات/التعداد (افتراضي 1)
#   PLANNER_MODEL_OVERRIDE           اسم نموذج مخصص
#   PLANNER_MAX_TASKS                الحد الأقصى للمهام (افتراضي 180)
#   PLANNER_JSON_LEN_LIMIT           حد أقصى لنص JSON (افتراضي 60000)
#   PLANNER_FALLBACK_ON_PARSE=0/1    تفعيل fallback عند فشل parsing (افتراضي 1)
#   PLANNER_FALLBACK_MODE            minimal | dual | analytic (افتراضي dual)
#   PLANNER_LOG_VERBOSE=1            تفعيل detailed debug
#   PLANNER_STRICT_SHORT=1           يمنع توسيع الأهداف القصيرة (افتراضي 0 = يسمح بالتوسيع)
#   PLANNER_MIN_OBJECTIVE_LENGTH     الحد الأدنى (افتراضي 3)
#   PLANNER_JSON_FORCE_SINGLE_TASK   إذا 1 يجبر إنتاج مهمة واحدة عند فشل (افتراضي 0)
#
# ======================================================================================
from __future__ import annotations

import json
import os
import re
import time
import uuid
import random
from typing import Any, Dict, List, Optional, Set, Tuple

from .base_planner import (
    BasePlanner,
    PlanningContext,
    PlannerError,
    PlanValidationError,
)
from .schemas import MissionPlanSchema
try:
    from .schemas import PlannedTask  # type: ignore
except Exception:  # pragma: no cover
    PlannedTask = Dict[str, Any]  # type: ignore

# Optional json5 usage (won't fail if absent)
try:  # pragma: no cover
    import json5  # type: ignore
except Exception:  # pragma: no cover
    json5 = None

# Attempt to import generation service
try:
    from app.services import generation_service as maestro
except Exception:  # pragma: no cover
    maestro = None


# -------------------------------- Logging Helper -------------------------------- #
def _log_debug(msg: str):
    if os.getenv("PLANNER_LOG_VERBOSE", "0") == "1":
        print(f"[Planner::DEBUG] {msg}")


class MaestroGraphPlannerV2(BasePlanner):
    name: str = "maestro_graph_planner_v2"
    version: str = "4.1.0"

    capabilities: Set[str] = {
        "llm",
        "dag-planning",
        "decomposition",
        "json-output",
    }
    tags: Set[str] = {"core", "stable", "graph", "resilient"}

    # Limits & Config
    MAX_OUTPUT_CHARS: int = int(os.getenv("PLANNER_JSON_LEN_LIMIT", "60000"))
    MAX_TASKS: int = int(os.getenv("PLANNER_MAX_TASKS", "180"))
    RETRY_ATTEMPTS: int = int(os.getenv("PLANNER_RETRY_ATTEMPTS", "3"))
    INITIAL_BACKOFF: float = 1.0
    BACKOFF_JITTER: float = 0.25
    TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,50}$")
    default_timeout_seconds = float(os.getenv("PLANNER_TIMEOUT_SECONDS", "50.0"))
    MIN_OBJECTIVE_LENGTH = int(os.getenv("PLANNER_MIN_OBJECTIVE_LENGTH", "3"))
    STRICT_SHORT = os.getenv("PLANNER_STRICT_SHORT", "0") == "1"
    ENABLE_SMARTFAST = os.getenv("PLANNER_ENABLE_SMARTFAST", "1") == "1"

    LOW_TIME_THRESHOLD = 4.5  # seconds left → bail to fallback

    # --------------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------------- #
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> MissionPlanSchema:
        raw_objective = (objective or "").strip()

        if not raw_objective:
            raise PlannerError("Objective is empty.", self.name, raw_objective)

        objective = self._normalize_objective(raw_objective)

        # FAST PATH (files)
        if self._fast_path_enabled() and self._is_trivial_file_objective(objective):
            _log_debug("FAST_PATH (file) activated.")
            return self._build_schema(self._fast_path_file_plan(objective), objective)

        # SMART FAST PATH (greetings / list) if enabled
        if self.ENABLE_SMARTFAST:
            smart_plan = self._smartfast_plan_if_applicable(objective)
            if smart_plan:
                _log_debug("SMART_FAST_PATH activated.")
                return self._build_schema(smart_plan, objective)

        if maestro is None:
            raise PlannerError("generation_service unavailable (maestro is None).", self.name, objective)

        if not self.quick_validate_objective(objective):
            _log_debug("quick_validate_objective returned False.")
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                return self._build_schema(self._fallback_data(objective), objective)
            raise PlannerError("Objective failed preliminary validation.", self.name, objective)

        prompt = self._construct_meta_prompt(objective, context)
        conversation_id = f"plan-{uuid.uuid4()}"
        start = time.monotonic()

        try:
            raw_answer = self._call_llm_with_retries(prompt, conversation_id, objective, start_time=start)
        except PlannerError as exc:
            _log_debug(f"LLM call final failure: {exc}")
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                return self._build_schema(self._fallback_data(objective), objective)
            raise

        try:
            json_text = self._multi_stage_extract_and_sanitize_json(raw_answer, objective)
            data = self._robust_parse_json(json_text, objective)
        except Exception as exc:
            _log_debug(f"Parsing pipeline failed: {exc}")
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                data = self._fallback_data(objective)
            else:
                raise

        data["objective"] = objective
        self._enforce_limits(data, objective)
        data["tasks"] = [self._transform_raw_task(t, objective) for t in data.get("tasks", [])]

        plan_schema = self._build_schema(data, objective)
        self._validate_dag(plan_schema, objective)

        return plan_schema

    # --------------------------------------------------------------------------- #
    # Objective Normalization
    # --------------------------------------------------------------------------- #
    def _normalize_objective(self, objective: str) -> str:
        """Ensure objective length & clarity. Expand very short objectives if allowed."""
        if len(objective) >= self.MIN_OBJECTIVE_LENGTH:
            return objective
        if self.STRICT_SHORT:
            return objective  # let schema or validator fail
        # Auto-augment
        augmented = f"Simple objective: {objective}. Provide a minimal actionable plan."
        _log_debug(f"Augmented short objective '{objective}' → '{augmented}'")
        return augmented

    # --------------------------------------------------------------------------- #
    # Prompt Construction
    # --------------------------------------------------------------------------- #
    def _construct_meta_prompt(self, objective: str, context: Optional[PlanningContext]) -> str:
        o_len = len(objective)
        ctx_block = self._context_block(context) if context else "None."
        max_tasks = min(self.MAX_TASKS, 60 if o_len < 280 else self.MAX_TASKS)
        if o_len < 55:
            # Micro/short mode
            return (
                "Return ONLY valid JSON.\n"
                f'Objective: "{objective}"\n'
                f"Keys: objective, tasks\n"
                f"tasks[]= {{task_id, description, tool_name, tool_args, dependencies[]}}\n"
                f"Limit tasks <= {max_tasks if max_tasks < 10 else 10}.\n"
                "JSON only. No commentary, no markdown."
            )
        return f"""
SYSTEM ROLE:
You are an advanced decomposition engine. Return ONLY JSON (no markdown / no prose).

OBJECTIVE:
\"\"\"{objective}\"\"\"

CONTEXT:
{ctx_block}

OUTPUT RULES:
- Single JSON object with: objective, tasks
- tasks: array of objects {{"task_id","description","tool_name","tool_args","dependencies"}}
- task_id: short (snake_or_hyphen)
- dependencies: only previous task_ids (no cycles)
- Use actionable concise descriptions.
- tasks <= {max_tasks}
- Parallelize where logical (minimize chains).
- No commentary, no code fences, no surrounding text.
""".strip()

    def _context_block(self, context: PlanningContext) -> str:
        parts: List[str] = []
        if context.past_failures:
            parts.append(f"PastFailures({len(context.past_failures)})")
        if context.user_preferences:
            parts.append(f"UserPrefs({len(context.user_preferences)})")
        if context.tags:
            parts.append("Tags:" + ",".join(context.tags))
        return " | ".join(parts) if parts else "None."

    # --------------------------------------------------------------------------- #
    # Fast Path (files)
    # --------------------------------------------------------------------------- #
    def _fast_path_enabled(self) -> bool:
        return os.getenv("PLANNER_FAST_PATH", "1") == "1"

    def _is_trivial_file_objective(self, objective: str) -> bool:
        o = objective.lower()
        if len(o) > 140:
            return False
        verbs_en = ("create", "make", "write", "build", "generate", "produce", "add")
        verbs_ar = ("اصنع", "انشئ", "أنشئ", "اكتب", "أضف", "اضف")
        if ("file" in o or "ملف" in o) and (
            any(o.startswith(v) for v in verbs_en) or any(o.startswith(v) for v in verbs_ar)
        ):
            return True
        return bool(re.match(r"^(create|write|make|generate)\s+.*file", o))

    def _infer_filename(self, objective: str) -> str:
        m = re.search(r"(?:named|call(?:ed)?|اسم(?:ه)?)\s+([A-Za-z0-9_\-\.]+)", objective, re.IGNORECASE)
        if m:
            name = m.group(1)
            if not name.lower().endswith((".md", ".txt", ".log")):
                return f"{name}.md"
            return name
        base = re.sub(r"[^a-zA-Z0-9_\-]+", "_", objective.lower()).strip("_") or "auto_file"
        if not base.endswith(".md"):
            base += ".md"
        return base[:48]

    def _fast_path_file_plan(self, objective: str) -> Dict[str, Any]:
        return {
            "objective": objective,
            "tasks": [
                {
                    "task_id": "create_file",
                    "description": f"Create file for: {objective}",
                    "tool_name": "write_file",
                    "tool_args": {
                        "path": self._infer_filename(objective),
                        "content": f"Auto-generated file\nObjective: {objective}\n(FAST_PATH v{self.version})"
                    },
                    "dependencies": []
                }
            ]
        }

    # --------------------------------------------------------------------------- #
    # SMART FAST PATH (greeting / list / simple summarization)
    # --------------------------------------------------------------------------- #
    GREET_PATTERNS = [
        r"^hi$", r"^hello$", r"^hey$", r"^مرحبا$", r"^اهلا$", r"^say hi", r"^تحية",
    ]
    LIST_HINTS = [
        "list ", "enumerate ", "three ", "5 ", "five ", "advantages", "benefits",
        "improvements", "خطوات", "مزايا", "فوائد"
    ]

    def _smartfast_plan_if_applicable(self, objective: str) -> Optional[Dict[str, Any]]:
        o = objective.lower().strip()
        # Greetings
        if any(re.match(p, o) for p in self.GREET_PATTERNS):
            return {
                "objective": objective,
                "tasks": [
                    {
                        "task_id": "greet",
                        "description": "Produce a short greeting",
                        "tool_name": "generic_think",
                        "tool_args": {"style": "greeting"},
                        "dependencies": []
                    }
                ]
            }
        # Simple list or enumerate (short)
        if len(o) < 160 and any(h in o for h in self.LIST_HINTS):
            return {
                "objective": objective,
                "tasks": [
                    {
                        "task_id": "analyze_prompt",
                        "description": "Analyze objective and extract requested list items",
                        "tool_name": "generic_think",
                        "tool_args": {"mode": "list"},
                        "dependencies": []
                    }
                ]
            }
        return None

    # --------------------------------------------------------------------------- #
    # LLM Call with adaptive retries
    # --------------------------------------------------------------------------- #
    def _call_llm_with_retries(
        self,
        prompt: str,
        conversation_id: str,
        objective: str,
        start_time: float
    ) -> str:
        chain: List[Tuple[str, Any]] = []
        if hasattr(maestro, "generate_json"):
            chain.append(("generate_json", maestro.generate_json))
        if hasattr(maestro, "forge_new_code"):
            chain.append(("forge_new_code", maestro.forge_new_code))
        if hasattr(maestro, "execute_task_legacy_wrapper"):
            chain.append(("execute_task_legacy_wrapper", maestro.execute_task_legacy_wrapper))
        if not chain:
            raise PlannerError("No valid LLM generation functions available.", self.name, objective)

        attempts = self.RETRY_ATTEMPTS
        budget = self.default_timeout_seconds * 0.97
        last_error: Optional[str] = None
        adaptive_prompt = prompt
        model_override = os.getenv("PLANNER_MODEL_OVERRIDE")
        max_tasks_hint = self.MAX_TASKS

        for attempt in range(1, attempts + 1):
            elapsed = time.monotonic() - start_time
            remaining = budget - elapsed
            if remaining <= self.LOW_TIME_THRESHOLD:
                _log_debug(f"Remaining time {remaining:.2f}s < LOW_TIME_THRESHOLD → early fallback.")
                raise PlannerError("Early fallback trigger (low time).", self.name, objective)

            fn_name, fn = chain[0]
            t0 = time.monotonic()
            try:
                _log_debug(f"LLM attempt {attempt}/{attempts} using {fn_name} (remaining ~{remaining:.2f}s)")
                if fn_name == "execute_task_legacy_wrapper":
                    resp = fn({"description": adaptive_prompt})  # type: ignore
                    status = resp.get("status", "")
                    answer = (resp.get("answer") or resp.get("echo") or "").strip()
                else:
                    kwargs = dict(prompt=adaptive_prompt, conversation_id=conversation_id)
                    if model_override:
                        kwargs["model"] = model_override
                    resp = fn(**kwargs)  # type: ignore
                    status = resp.get("status", "")
                    answer = (resp.get("answer") or "").strip()

                dur = time.monotonic() - t0
                _log_debug(f"LLM latency: {dur:.2f}s status={status}")
                if status not in ("success", "ok"):
                    raise RuntimeError(f"Bad status '{status}' from LLM.")
                if not answer:
                    raise RuntimeError("Empty answer from LLM.")
                return answer[: self.MAX_OUTPUT_CHARS]

            except Exception as exc:
                last_error = str(exc)
                _log_debug(f"Attempt {attempt} failed: {last_error}")
                if attempt < attempts:
                    # Adaptive degrade
                    if len(adaptive_prompt) > 2000:
                        adaptive_prompt = self._shrink_prompt(adaptive_prompt)
                    # Reduce max tasks hint inside prompt (if present)
                    max_tasks_hint = max(5, max_tasks_hint // 2)
                    adaptive_prompt = re.sub(r"tasks <= \d+", f"tasks <= {max_tasks_hint}", adaptive_prompt)
                    backoff = self._compute_backoff(attempt)
                    if (time.monotonic() - start_time + backoff) > budget:
                        backoff = max(0.05, budget - (time.monotonic() - start_time))
                    time.sleep(max(0.05, backoff))
                else:
                    if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                        _log_debug("All LLM attempts failed; using fallback raw answer.")
                        return self._fallback_raw_answer(objective)
                    raise PlannerError(
                        f"LLM failed after {attempts} attempts. Last error: {last_error}",
                        self.name,
                        objective
                    ) from exc
        return ""

    def _shrink_prompt(self, prompt: str) -> str:
        if len(prompt) <= 1400:
            return prompt
        return "OBJECTIVE_SNIPPET:\n" + prompt[-1100:]

    def _compute_backoff(self, attempt: int) -> float:
        base = self.INITIAL_BACKOFF * (2 ** (attempt - 1))
        jitter = random.uniform(0, self.BACKOFF_JITTER)
        return base + jitter

    # --------------------------------------------------------------------------- #
    # Fallback Logic
    # --------------------------------------------------------------------------- #
    def _fallback_raw_answer(self, objective: str) -> str:
        return json.dumps(self._fallback_data(objective), ensure_ascii=False)

    def _fallback_data(self, objective: str) -> Dict[str, Any]:
        mode = os.getenv("PLANNER_FALLBACK_MODE", "dual").lower()
        if mode not in ("minimal", "dual", "analytic"):
            mode = "dual"
        if mode == "minimal":
            tasks = [
                {
                    "task_id": "single_step",
                    "description": f"Process objective: {objective}",
                    "tool_name": "generic_think",
                    "tool_args": {},
                    "dependencies": []
                }
            ]
        elif mode == "analytic":
            tasks = [
                {
                    "task_id": "analyze",
                    "description": f"Analyze objective: {objective}",
                    "tool_name": "generic_think",
                    "tool_args": {"phase": "analysis"},
                    "dependencies": []
                },
                {
                    "task_id": "synthesize",
                    "description": "Synthesize actionable plan",
                    "tool_name": "generic_think",
                    "tool_args": {"phase": "synthesis"},
                    "dependencies": ["analyze"]
                }
            ]
        else:  # dual (default)
            tasks = [
                {
                    "task_id": "analyze",
                    "description": f"Initial analysis for objective: {objective}",
                    "tool_name": "generic_think",
                    "tool_args": {},
                    "dependencies": []
                },
                {
                    "task_id": "execute",
                    "description": "Produce final structured result",
                    "tool_name": "generic_think",
                    "tool_args": {},
                    "dependencies": ["analyze"]
                }
            ]
        if os.getenv("PLANNER_JSON_FORCE_SINGLE_TASK", "0") == "1":
            tasks = tasks[:1]
        return {
            "objective": objective,
            "tasks": tasks
        }

    # --------------------------------------------------------------------------- #
    # Multi-Stage JSON Extraction & Parsing
    # --------------------------------------------------------------------------- #
    def _multi_stage_extract_and_sanitize_json(self, raw: str, objective: str) -> str:
        """
        Attempts several extraction strategies to salvage a JSON object.
        Raises PlanValidationError only if all fail and fallback not allowed.
        """
        _log_debug("Begin JSON extraction pipeline.")
        original = raw

        # Stage 1: strip leading/trailing whitespace
        raw = raw.strip()

        # Stage 2: remove code fences (```, ```json)
        raw = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE)

        # Stage 3: remove obvious commentary lines
        raw = re.sub(r"^\s*//.*?$", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"^\s*#.*?$", "", raw, flags=re.MULTILINE)

        # If raw itself looks like pure object
        if raw.startswith("{") and raw.endswith("}"):
            candidate = self._strip_trailing_commas(raw)
            if self._looks_like_json(candidate):
                _log_debug("Stage direct object success.")
                return candidate

        # Stage 4: locate widest braces
        wide_start = raw.find("{")
        wide_end = raw.rfind("}")
        if wide_start != -1 and wide_end != -1 and wide_end > wide_start:
            candidate = raw[wide_start: wide_end + 1]
            candidate = self._strip_trailing_commas(candidate)
            if self._looks_like_json(candidate):
                _log_debug("Stage wide braces success.")
                return candidate

        # Stage 5: regex all potential JSON root objects (shallow heuristic)
        object_matches = re.findall(r"\{.*?\}", raw, flags=re.DOTALL)
        object_matches = sorted(object_matches, key=len, reverse=True)
        for om in object_matches:
            cm = om.strip()
            if cm.count("{") == cm.count("}"):  # naive balance
                cm2 = self._strip_trailing_commas(cm)
                if self._looks_like_json(cm2):
                    _log_debug("Stage regex object match success.")
                    return cm2

        # Stage 6: attempt partial salvage if tasks array present separately
        tasks_array = self._extract_tasks_array(raw)
        if tasks_array:
            salvage = {
                "objective": objective,
                "tasks": tasks_array
            }
            _log_debug("Stage tasks-array salvage success.")
            return json.dumps(salvage, ensure_ascii=False)

        # Stage 7: attempt fix single quotes → double quotes if that produces parseable JSON
        fixed_single = self._force_double_quotes(original)
        if fixed_single and self._looks_like_json(fixed_single):
            _log_debug("Stage single-quote fix success.")
            return fixed_single

        # Stage 8: last attempt with json5 (optional)
        if json5:
            try:
                data = json5.loads(original)
                if isinstance(data, dict):
                    _log_debug("Stage json5 success.")
                    return json.dumps(data, ensure_ascii=False)
            except Exception:
                pass

        # Failure
        if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
            _log_debug("All extraction stages failed – using fallback JSON.")
            return json.dumps(self._fallback_data(objective), ensure_ascii=False)
        raise PlanValidationError("Unable to extract JSON from LLM output.", self.name, objective)

    def _looks_like_json(self, text: str) -> bool:
        # quick heuristic
        return '"tasks"' in text or '"objective"' in text

    def _extract_tasks_array(self, raw: str) -> Optional[List[Any]]:
        # Attempt to isolate tasks array: "tasks": [ ... ]
        m = re.search(r'"tasks"\s*:\s*\[(.*?)\]', raw, flags=re.DOTALL)
        if not m:
            return None
        inside = m.group(1)
        # crude split by "}," boundaries (imperfect but salvage)
        parts = re.split(r"}\s*,\s*\{", inside)
        tasks: List[Dict[str, Any]] = []
        for i, p in enumerate(parts):
            chunk = p
            if not chunk.strip():
                continue
            if not chunk.strip().startswith("{"):
                chunk = "{" + chunk
            if not chunk.strip().endswith("}"):
                chunk = chunk + "}"
            try:
                t = json.loads(self._strip_trailing_commas(chunk))
                if isinstance(t, dict):
                    tasks.append(t)
            except Exception:
                # ignore malformed piece
                continue
        return tasks if tasks else None

    def _force_double_quotes(self, raw: str) -> Optional[str]:
        # naive attempt: replace single quotes around keys with double quotes
        # (risk: inside text) – only apply if very little double quotes exist
        if raw.count('"') > 4:
            return None
        candidate = re.sub(r"'", '"', raw)
        return candidate

    def _strip_trailing_commas(self, text: str) -> str:
        return re.sub(r",(\s*[}\]])", r"\1", text)

    def _robust_parse_json(self, text: str, objective: str) -> Dict[str, Any]:
        # Attempt normal json
        try:
            return self._validate_parsed_object(json.loads(text), objective)
        except Exception as e1:
            _log_debug(f"json.loads failed: {e1}")
            # Try json5
            if json5:
                try:
                    return self._validate_parsed_object(json5.loads(text), objective)
                except Exception as e2:
                    _log_debug(f"json5 parse failed: {e2}")
            # Attempt final salvage: fallback
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                return self._fallback_data(objective)
            raise PlanValidationError(f"JSON parsing error: {e1}", self.name, objective) from e1

    def _validate_parsed_object(self, data: Any, objective: str) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise PlanValidationError("Top-level JSON must be an object.", self.name, objective)
        tasks = data.get("tasks")
        if tasks is None:
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                data["tasks"] = self._fallback_data(objective)["tasks"]
            else:
                raise PlanValidationError("Missing 'tasks' key.", self.name, objective)
        if not isinstance(data["tasks"], list):
            raise PlanValidationError("'tasks' must be a list.", self.name, objective)
        return data

    # --------------------------------------------------------------------------- #
    # Limits & Transformation
    # --------------------------------------------------------------------------- #
    def _enforce_limits(self, data: Dict[str, Any], objective: str):
        tasks = data.get("tasks", [])
        if len(tasks) > self.MAX_TASKS:
            raise PlanValidationError(f"Too many tasks ({len(tasks)} > {self.MAX_TASKS}).", self.name, objective)

    def _transform_raw_task(self, task: Any, objective: str) -> Dict[str, Any]:
        if not isinstance(task, dict):
            raise PlanValidationError("Task entry not an object.", self.name, objective)
        tid = (task.get("task_id") or task.get("id") or "").strip()
        if not tid:
            tid = f"task_{uuid.uuid4().hex[:6]}"
        if not self.TASK_ID_PATTERN.match(tid):
            tid = re.sub(r"[^a-zA-Z0-9_\-]", "_", tid)[:30] or f"task_{uuid.uuid4().hex[:4]}"

        desc = (task.get("description") or task.get("desc") or "").strip()
        if not desc:
            desc = f"Execute {tid} for objective."

        tool_name = (task.get("tool_name") or task.get("tool") or "generic_think").strip() or "generic_think"
        tool_args = task.get("tool_args") or task.get("args") or {}
        if not isinstance(tool_args, dict):
            tool_args = {}

        deps = task.get("dependencies") or task.get("depends_on") or []
        if not isinstance(deps, list):
            deps = []
        cleaned: List[str] = []
        seen = set()
        for d in deps:
            if isinstance(d, str):
                d = d.strip()
                if d and d != tid and d not in seen:
                    seen.add(d)
                    cleaned.append(d)

        return {
            "task_id": tid,
            "description": desc,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "dependencies": cleaned,
        }

    def _build_schema(self, data: Dict[str, Any], objective: str) -> MissionPlanSchema:
        try:
            return MissionPlanSchema(**data)
        except Exception as exc:
            _log_debug(f"MissionPlanSchema validation failed: {exc}")
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                return MissionPlanSchema(**self._fallback_data(objective))
            raise PlanValidationError(f"Schema validation failed: {exc}", self.name, objective) from exc

    # --------------------------------------------------------------------------- #
    # DAG Validation
    # --------------------------------------------------------------------------- #
    def _validate_dag(self, plan: MissionPlanSchema, objective: str):
        tasks = getattr(plan, "tasks", None)
        if not tasks:
            raise PlanValidationError("No tasks to validate.", self.name, objective)

        ids: Set[str] = set()
        adjacency: Dict[str, List[str]] = {}
        indeg: Dict[str, int] = {}

        # Collect
        for t in tasks:
            tid = getattr(t, "task_id", None) if hasattr(t, "task_id") else t.get("task_id")
            if not tid or not isinstance(tid, str):
                raise PlanValidationError("Invalid task_id (None).", self.name, objective)
            if tid in ids:
                raise PlanValidationError(f"Duplicate task_id '{tid}'", self.name, objective)
            ids.add(tid)
            adjacency[tid] = []
            indeg[tid] = 0

        # Edges
        for t in tasks:
            tid = getattr(t, "task_id", None) if hasattr(t, "task_id") else t.get("task_id")
            deps = getattr(t, "dependencies", None) if hasattr(t, "dependencies") else t.get("dependencies")
            deps = deps or []
            if not isinstance(deps, list):
                raise PlanValidationError(f"Task '{tid}' dependencies not list.", self.name, objective)
            for d in deps:
                if d == tid:
                    raise PlanValidationError(f"Self-dependency in '{tid}'", self.name, objective)
                if d not in ids:
                    raise PlanValidationError(f"Unknown dependency '{d}' for '{tid}'", self.name, objective)
                adjacency[d].append(tid)
                indeg[tid] += 1

        # Topological check
        queue = [n for n, deg in indeg.items() if deg == 0]
        visited = 0
        while queue:
            cur = queue.pop()
            visited += 1
            for nxt in adjacency[cur]:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)

        if visited != len(ids):
            raise PlanValidationError("Cycle detected in task graph.", self.name, objective)

    # --------------------------------------------------------------------------- #
    # Quick Objective Validation
    # --------------------------------------------------------------------------- #
    def quick_validate_objective(self, objective: str) -> bool:
        obj = (objective or "").strip()
        if len(obj) < self.MIN_OBJECTIVE_LENGTH:
            return False
        return True


# ======================================================================================
# END OF FILE
# ======================================================================================