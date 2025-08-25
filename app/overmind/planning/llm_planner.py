# app/overmind/planning/llm_planner.py
# ======================================================================================
# ==                         MAESTRO GRAPH PLANNER (v2.2 • LLM)                       ==
# ==                     LLM–POWERED STRATEGIC DAG (MISSION PLAN)                      ==
# ======================================================================================
#
# PURPOSE (القصد):
#   تحويل هدف (Objective) لغوي عالي المستوى إلى خطة مهام (Directed Acyclic Graph)
#   متماسكة وفق مخطط MissionPlanSchema: كل مهمة لها معرف، وصف، أداة، معاملات، واعتماديات.
#
# ROOT CAUSE (سبب الخلل السابق):
#   - كان الـ Planner يعرّف name كـ @property → BasePlanner v2.1+ يتطلب name كـ
#     "CLASS ATTRIBUTE" لتسجيله في السجل (_registry) أثناء تعريف الصنف.
#   - النتيجة: planner لم يُسجَّل → discover() يعرض planners=0 → CLI يفشل:
#       Planner 'maestro_graph_planner_v2' not found / No planners available.
#
# FIX (الإصلاح):
#   - تعريف: name = "maestro_graph_planner_v2" كحقل صنفي.
#   - الصنف: MaestroGraphPlannerV2 (يمكن تغيير الاسم، ولكن الاسم registry يعتمد على name).
#   - التزمنا بعقد BasePlanner.generate_plan() وأعدنا MissionPlanSchema.
#
# SAFETY & DESIGN:
#   - استدعاء خدمة LLM (generation_service) مع استرجاع graceful في حال عدم توفر الدالة.
#   - إعادة محاولة (Retry) مع Backoff أسي + Jitter.
#   - استخراج JSON صارم + trimming.
#   - فحص DAG: معرفات فريدة، عدم وجود اعتماد ذاتي، لا دورات (Cycles).
#   - حدود موارد: حجم النص، عدد المهام.
#   - تحويل / تكييف مخرجات LLM إلى الشكل المطلوب قبل إدخالها في MissionPlanSchema.
#
# ADAPTATION HOOKS (نقاط تكيّف سريعة):
#   - _construct_meta_prompt: عدّل التعليمات.
#   - _transform_raw_task: عدّل إعادة التسمية / الحقول لتطابق مخططك الفعلي.
#   - _BUILD_SCHEMA: راجع إذا كانت MissionPlanSchema تختلف في التواقيع.
#
# ======================================================================================

from __future__ import annotations

import json
import re
import time
import uuid
import random
from typing import Any, Dict, List, Optional, Set

from .base_planner import (
    BasePlanner,
    PlanningContext,
    PlannerError,
    PlanValidationError,
)

# Schema imports (عدِّل إذا المسار مختلف)
from .schemas import MissionPlanSchema
try:
    # إذا لديك نموذج مهام منفصل (Pydantic) استخدمه، وإلا سيتعامل القاموس مباشرة
    from .schemas import PlannedTask  # type: ignore
except Exception:  # noqa: F401
    PlannedTask = Dict[str, Any]  # type: ignore

# محاولة استيراد خدمة التوليد (LLM)
try:
    from app.services import generation_service as maestro
except Exception:  # pragma: no cover
    maestro = None


class MaestroGraphPlannerV2(BasePlanner):
    """
    LLM Graph Planner:
      1. يُنشئ meta-prompt غني بالتعليمات.
      2. يستدعي خدمة التوليد (maestro) للحصول على JSON.
      3. يطبّق Sanitization + Parsing + Validation.
      4. يتحقق من سلامة DAG (لا دورات / لا مراجع مفقودة).
      5. يُرجع MissionPlanSchema.

    مخرجات LLM المتوقعة (مبسّطة):
    {
      "objective": "...",
      "tasks": [
        {
          "task_id": "analyze",
          "description": "Analyze objective",
          "tool_name": "generic_think",
          "tool_args": {},
          "dependencies": []
        }
      ]
    }
    """

    # ---------- REQUIRED IDENTITY (FIXED FOR REGISTRY) ----------
    name: str = "maestro_graph_planner_v2"
    version: str = "2.2.0"

    # ---------- DISCOVERY METADATA ----------
    capabilities: Set[str] = {
        "llm",
        "dag-planning",
        "decomposition",
        "json-output",
    }
    tags: Set[str] = {"core", "stable", "graph"}

    # ---------- LIMITS & RETRY CONFIG ----------
    MAX_OUTPUT_CHARS: int = 60_000
    MAX_TASKS: int = 180
    RETRY_ATTEMPTS: int = 3
    INITIAL_BACKOFF: float = 1.2
    BACKOFF_JITTER: float = 0.35
    TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,50}$")

    # Optional timeout (leveraged by BasePlanner.instrumented_generate)
    default_timeout_seconds = 50.0

    # ==================================================================================
    # PUBLIC CORE (BasePlanner requirement)
    # ==================================================================================
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> MissionPlanSchema:
        objective = (objective or "").strip()
        if not objective:
            raise PlannerError("Objective is empty.", self.name, objective)

        if maestro is None:
            raise PlannerError(
                "generation_service (maestro) unavailable. Cannot invoke LLM.",
                self.name,
                objective
            )

        prompt = self._construct_meta_prompt(objective, context)
        convo_id = f"plan-{uuid.uuid4()}"

        raw = self._call_llm_with_retries(prompt, convo_id, objective)
        json_block = self._extract_json(raw, objective)
        data = self._parse_json(json_block, objective)

        # Normalize & enforce objective match
        data["objective"] = objective

        # Clamp / limit
        self._enforce_limits(data, objective)

        # Adapt each raw task (rename / ensure keys)
        data["tasks"] = [self._transform_raw_task(t, objective) for t in data.get("tasks", [])]

        # Build schema (Pydantic or custom)
        plan_schema = self._build_schema(data, objective)

        # Graph structural validation (DAG)
        self._validate_dag(plan_schema, objective)

        return plan_schema

    # ==================================================================================
    # VALIDATION HOOK (extra semantics) – auto-called by instrumented_generate()
    # ==================================================================================
    def validate_plan(
        self,
        plan: MissionPlanSchema,
        objective: str,
        context: Optional[PlanningContext]
    ) -> None:  # noqa: D401
        # Must contain tasks
        tasks = getattr(plan, "tasks", None)
        if not tasks:
            raise PlanValidationError("No tasks generated.", self.name, objective)
        # Example: ensure objective appears in at least one description (soft heuristic)
        sig = objective.split()
        if sig:
            first_kw = sig[0].lower()
            found = any(first_kw in (getattr(t, "description", "") or "").lower()
                        for t in tasks)
            if not found:  # not fatal, but illustrate semantic hook
                # لا نرفع استثناء هنا لتجنب الإفراط، يمكن تفعيل هذا كتحذير
                pass

    # ==================================================================================
    # INTERNAL: PROMPT CONSTRUCTION
    # ==================================================================================
    def _construct_meta_prompt(self, objective: str, context: Optional[PlanningContext]) -> str:
        ctx_parts: List[str] = []
        if context:
            if context.past_failures:
                ctx_parts.append(
                    f"- Past Failures Keys: {', '.join(list(context.past_failures.keys())[:6])}"
                )
            if context.user_preferences:
                ctx_parts.append(
                    f"- User Prefs Keys: {', '.join(list(context.user_preferences.keys())[:6])}"
                )
            if context.tags:
                ctx_parts.append(f"- Context Tags: {', '.join(context.tags)}")
        ctx_block = "\n".join(ctx_parts) or "None."

        return f"""
SYSTEM MODE:
You are an expert strategic planner that produces ONLY JSON (no prose, no markdown code fences).

OBJECTIVE:
\"\"\"{objective}\"\"\"

CONTEXT:
{ctx_block}

OUTPUT REQUIREMENTS:
- Top-level object with keys: objective, tasks.
- tasks: array of objects. Each task object MUST contain:
    task_id (unique, short snake_case/hyphen id),
    description (concise actionable),
    tool_name (string),
    tool_args (object),
    dependencies (array of task_id).
- DAG must be acyclic. A task may depend on zero or more earlier tasks.
- Encourage parallelism where possible while preserving logical order.
- Keep tasks <= {self.MAX_TASKS}.

STRICTLY RETURN JSON ONLY. DO NOT wrap in ``` or provide commentary.

EXAMPLE (illustrative only):
{{
  "objective": "{objective}",
  "tasks": [
    {{
      "task_id": "analyze_objective",
      "description": "Analyze and clarify the objective.",
      "tool_name": "generic_think",
      "tool_args": {{}},
      "dependencies": []
    }},
    {{
      "task_id": "research_prerequisites",
      "description": "Collect required knowledge or references.",
      "tool_name": "knowledge_search",
      "tool_args": {{"query": "key concepts"}},
      "dependencies": ["analyze_objective"]
    }},
    {{
      "task_id": "synthesize_solution",
      "description": "Integrate findings into solution draft.",
      "tool_name": "generic_think",
      "tool_args": {{}},
      "dependencies": ["research_prerequisites"]
    }}
  ]
}}

NOW RETURN THE JSON PLAN:
""".strip()

    # ==================================================================================
    # INTERNAL: LLM CALL + RETRY
    # ==================================================================================
    def _call_llm_with_retries(self, prompt: str, conversation_id: str, objective: str) -> str:
        """
        Expects generation_service to expose one of:
          - forge_new_code(prompt=..., conversation_id=...)
          - generate_json(prompt=..., conversation_id=...)
          - execute_task_legacy_wrapper({...})   (Worst-case fallback)
        """
        # Determine best callable
        call_chain = []
        if hasattr(maestro, "forge_new_code"):
            call_chain.append(("forge_new_code", maestro.forge_new_code))
        if hasattr(maestro, "generate_json"):
            call_chain.append(("generate_json", maestro.generate_json))
        if hasattr(maestro, "execute_task_legacy_wrapper"):
            # Legacy signature may differ; adapt below if needed
            call_chain.append(("execute_task_legacy_wrapper", maestro.execute_task_legacy_wrapper))

        if not call_chain:
            raise PlannerError(
                "No suitable generation function found in generation_service.",
                self.name,
                objective
            )

        last_error: Optional[str] = None
        for attempt in range(1, self.RETRY_ATTEMPTS + 1):
            fn_name, fn = call_chain[0]  # choose highest priority
            try:
                if fn_name == "execute_task_legacy_wrapper":
                    response = fn({"description": prompt})  # type: ignore
                    # Expecting something like {"status":"ok","echo": "..."} fallback
                    answer = response.get("answer") or response.get("echo") or ""
                    status = response.get("status", "unknown")
                    if status != "ok" and not answer:
                        raise RuntimeError(f"Legacy wrapper failure: {response}")
                else:
                    response = fn(prompt=prompt, conversation_id=conversation_id)  # type: ignore
                    answer = response.get("answer", "")
                    status = response.get("status", "unknown")

                if status not in ("success", "ok"):
                    raise RuntimeError(f"LLM service responded with status '{status}'")

                if not answer.strip():
                    raise RuntimeError("Empty answer string from LLM service.")
                return answer[: self.MAX_OUTPUT_CHARS]

            except Exception as exc:
                last_error = str(exc)
                if attempt < self.RETRY_ATTEMPTS:
                    backoff = self._compute_backoff(attempt)
                    time.sleep(backoff)
                else:
                    raise PlannerError(
                        f"LLM failed after {self.RETRY_ATTEMPTS} attempts. Last error: {last_error}",
                        self.name,
                        objective
                    ) from exc
        return ""  # pragma: no cover

    def _compute_backoff(self, attempt: int) -> float:
        base = self.INITIAL_BACKOFF * (2 ** (attempt - 1))
        jitter = random.uniform(0, self.BACKOFF_JITTER)
        return base + jitter

    # ==================================================================================
    # INTERNAL: JSON EXTRACTION & PARSING
    # ==================================================================================
    def _extract_json(self, raw: str, objective: str) -> str:
        raw = raw.strip()
        if len(raw) > self.MAX_OUTPUT_CHARS:
            raw = raw[: self.MAX_OUTPUT_CHARS]

        # محاولة إزالة أي أسوار Markdown
        raw = raw.replace("```json", "").replace("```", "").strip()

        # إذا كان النص الكامل JSON صالح (يبدأ '{' وينتهي '}') نستخدمه مباشرة
        if raw.startswith("{") and raw.endswith("}"):
            return raw

        # وإلا نحاول التعرف على أول { و آخر } (نطاق)
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise PlanValidationError(
                "Cannot locate JSON object braces in LLM output.",
                self.name,
                objective
            )
        candidate = raw[start:end + 1].strip()
        if not (candidate.startswith("{") and candidate.endswith("}")):
            raise PlanValidationError(
                "Extracted segment not valid JSON object boundaries.",
                self.name,
                objective
            )
        return candidate

    def _parse_json(self, text: str, objective: str) -> Dict[str, Any]:
        try:
            data = json.loads(text)
            if not isinstance(data, dict):
                raise TypeError("Top-level JSON must be an object.")
            if "tasks" not in data:
                raise ValueError("Missing 'tasks' key.")
            if not isinstance(data["tasks"], list):
                raise TypeError("'tasks' must be a list.")
            return data
        except Exception as exc:
            raise PlanValidationError(
                f"JSON parsing error: {exc}",
                self.name,
                objective
            ) from exc

    # ==================================================================================
    # INTERNAL: NORMALIZATION / LIMITS
    # ==================================================================================
    def _enforce_limits(self, data: Dict[str, Any], objective: str) -> None:
        tasks = data.get("tasks", [])
        if len(tasks) > self.MAX_TASKS:
            raise PlanValidationError(
                f"Too many tasks ({len(tasks)} > {self.MAX_TASKS}).",
                self.name,
                objective
            )

    def _transform_raw_task(self, task: Any, objective: str) -> Dict[str, Any]:
        """
        تطبيع (Normalize) مهمة خام من الـ LLM لضمان الحقول:
          task_id, description, tool_name, tool_args, dependencies
        عدّل هنا لو مخططك الفعلي يستخدم أسماء مختلفة.
        """
        if not isinstance(task, dict):
            raise PlanValidationError("Task entry is not an object.", self.name, objective)

        task_id = (task.get("task_id") or task.get("id") or "").strip()
        if not task_id:
            raise PlanValidationError("Task missing task_id.", self.name, objective)
        if not self.TASK_ID_PATTERN.match(task_id):
            raise PlanValidationError(f"Invalid task_id format: {task_id}", self.name, objective)

        description = (task.get("description") or task.get("desc") or "").strip()
        if not description:
            description = f"Execute step '{task_id}' related to objective."

        tool_name = (task.get("tool_name") or task.get("tool") or "generic_think").strip()
        if not tool_name:
            tool_name = "generic_think"

        tool_args = task.get("tool_args") or task.get("args") or {}
        if not isinstance(tool_args, dict):
            tool_args = {}

        deps = task.get("dependencies") or task.get("depends_on") or []
        if not isinstance(deps, list):
            deps = []

        # إزالة التكرار في الاعتماديات والحفاظ على الترتيب
        seen = set()
        clean_deps: List[str] = []
        for d in deps:
            if isinstance(d, str):
                d = d.strip()
                if d and d not in seen and d != task_id:
                    seen.add(d)
                    clean_deps.append(d)

        return {
            "task_id": task_id,
            "description": description,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "dependencies": clean_deps,
        }

    # ==================================================================================
    # INTERNAL: BUILD SCHEMA
    # ==================================================================================
    def _build_schema(self, data: Dict[str, Any], objective: str) -> MissionPlanSchema:
        """
        يبني MissionPlanSchema (اعتمد على مخططك الفعلي). إذا كان مخططك يطلب
        حقولاً إضافية (مثل rationale / stats / score), أضفها هنا.
        """
        try:
            plan = MissionPlanSchema(**data)
            return plan
        except Exception as exc:
            raise PlanValidationError(
                f"Schema validation failed: {exc}",
                self.name,
                objective
            ) from exc

    # ==================================================================================
    # INTERNAL: DAG VALIDATION
    # ==================================================================================
    def _validate_dag(self, plan: MissionPlanSchema, objective: str) -> None:
        tasks = getattr(plan, "tasks", None)
        if not tasks:
            raise PlanValidationError("No tasks present for validation.", self.name, objective)

        ids: Set[str] = set()
        adjacency: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {}

        # Pass 1: gather ids
        for t in tasks:
            # دعم كلٍ من الكائن Pydantic أو dict
            tid = getattr(t, "task_id", None) if hasattr(t, "task_id") else t.get("task_id")
            if not isinstance(tid, str) or not tid:
                raise PlanValidationError("Task missing task_id (validation).", self.name, objective)
            if tid in ids:
                raise PlanValidationError(f"Duplicate task_id '{tid}'", self.name, objective)
            ids.add(tid)
            adjacency[tid] = []
            in_degree[tid] = 0

        # Pass 2: dependencies
        for t in tasks:
            tid = getattr(t, "task_id", None) if hasattr(t, "task_id") else t.get("task_id")
            deps = getattr(t, "dependencies", None) if hasattr(t, "dependencies") else t.get("dependencies")
            deps = deps or []
            if not isinstance(deps, list):
                raise PlanValidationError(f"Task '{tid}' dependencies not a list.", self.name, objective)
            for d in deps:
                if d == tid:
                    raise PlanValidationError(f"Task '{tid}' self-dependency.", self.name, objective)
                if d not in ids:
                    raise PlanValidationError(
                        f"Task '{tid}' depends on unknown task '{d}'.",
                        self.name,
                        objective
                    )
                adjacency[d].append(tid)
                in_degree[tid] += 1

        # Kahn's algorithm for cycle detection
        queue = [n for n, deg in in_degree.items() if deg == 0]
        visited = 0
        while queue:
            current = queue.pop()
            visited += 1
            for nxt in adjacency[current]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        if visited != len(ids):
            raise PlanValidationError("Cycle detected in task graph.", self.name, objective)

    # ==================================================================================
    # OPTIONAL QUICK HEURISTIC
    # ==================================================================================
    def quick_validate_objective(self, objective: str) -> bool:
        """
        Heuristic filter before planning. يمكن استخدامه في orchestrator
        لتجنب طلب LLM لأهداف قصيرة / عديمة المعنى.
        """
        obj = (objective or "").strip()
        if len(obj) < 12:
            return False
        verbs = {"build", "create", "design", "analyze", "generate", "plan", "refactor", "write"}
        tokens = set(re.findall(r"[a-z]{4,}", obj.lower()))
        return bool(verbs & tokens)


# ======================================================================================
# END OF FILE
# ======================================================================================