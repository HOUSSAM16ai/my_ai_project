# app/overmind/planning/llm_planner.py
# """
llm_planner.py  (Version 5.0  "GROUNDED-PURE-THINK / CONTEXT-AWARE / JSON-MODE")

High–fidelity mission planner with:
  - Smart Routing Layer (fast paths for trivial objectives).
  - Strict Tool Grounding (enumerate ONLY actually available tools).
  - JSON Mode / Function Calling attempt (maestro.generate_json).
  - Multi-Strategy Ladder (strict_full → structured_template → minimal_hint).
  - Defensive JSON parsing with minimal graceful fallback.
  - Output bridging placeholders: ${previous_task_id.output} allowed inside tool_args.
  - Bilingual (Arabic / English) objective tolerance.
  - Backoff & adaptive prompt shrinking.
  - Compatibility preserved with MissionPlanSchema (objective, tasks[]).
  - Does NOT invent tools. Forces unknown tool names to generic_think.

Execution layer MUST later replace placeholders ${task_id.output} in tool_args before executing
dependent tasks (fetch previous task textual result and inject).

ENV CONFIG (all optional):
  PLANNER_TIMEOUT_SECONDS          (default: 40.0)
  PLANNER_RETRY_ATTEMPTS           (default: 3)
  PLANNER_MODEL_OVERRIDE           (forces a model name for maestro)
  PLANNER_MAX_TASKS                (default: 120)
  PLANNER_ENABLE_FAST_PATH         ("1" default)
  PLANNER_ENABLE_SMARTFAST         ("1" default)
  PLANNER_JSON_FORCE_SINGLE_TASK   ("0" default)
  PLANNER_LOG_VERBOSE              ("0" default) → set "1" for debug logging
  PLANNER_STRICT_SHORT             ("1" default) if set, do not augment ultra short objectives
  PLANNER_FALLBACK_ON_PARSE        ("1" default) produce fallback plan on parse failure
  PLANNER_SHORT_OBJECTIVE_MIN_LEN  (default: 12) threshold for short objective augmentation
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Callable

# ---------------------------------------------------------------------------
# External Dependencies (soft imports / graceful degradation)
# ---------------------------------------------------------------------------

try:
    from .schemas import MissionPlanSchema, PlannedTask, PlanningContext  # type: ignore
except Exception:  # pragma: no cover
    # Minimal stand‑ins to avoid crashes if real schemas are absent.
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
        tasks: List[PlannedTask]

    @dataclass
    class PlanningContext:  # type: ignore
        past_failures: Optional[List[str]] = None
        user_preferences: Optional[Dict[str, Any]] = None
        tags: Optional[List[str]] = None

try:
    from .base import BasePlanner, PlannerError, PlanValidationError  # type: ignore
except Exception:  # pragma: no cover
    class PlannerError(Exception):
        def __init__(self, message: str, planner_name: str = "llm_planner", objective: str = ""):
            super().__init__(f"[{planner_name}] {message} :: objective='{objective}'")
            self.planner_name = planner_name
            self.objective = objective

    class PlanValidationError(PlannerError):
        pass

    class BasePlanner:  # type: ignore
        def quick_validate_objective(self, objective: str) -> bool:
            return bool(objective and len(objective.strip()) > 0)

# Generation service (LLM orchestration)
try:
    from app.services import generation_service as maestro  # type: ignore
except Exception:  # pragma: no cover
    maestro = None  # type: ignore

# Agent tools registry (for grounding)
try:
    from app.agent import tools as agent_tools  # type: ignore
except Exception:  # pragma: no cover
    agent_tools = None  # type: ignore

# Optional json5 parsing enhancement
try:  # pragma: no cover
    import json5  # type: ignore
except Exception:  # pragma: no cover
    json5 = None  # type: ignore


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log_debug(msg: str):
    if os.getenv("PLANNER_LOG_VERBOSE", "0") == "1":
        print(f"[Planner::DEBUG] {msg}")


# ---------------------------------------------------------------------------
# Planner Implementation
# ---------------------------------------------------------------------------

class LLMGroundedPlanner(BasePlanner):
    """
    High-level LLM grounded planner with multi-strategy generation and robust fallback.
    """

    name: str = "llm_grounded_planner"
    version: str = "5.0.0"

    capabilities: Set[str] = {"grounded", "routing", "json-mode"}

    # Configuration / Limits
    MAX_OUTPUT_CHARS: int = 60_000
    MAX_TASKS: int = int(os.getenv("PLANNER_MAX_TASKS", "120"))
    RETRY_ATTEMPTS: int = int(os.getenv("PLANNER_RETRY_ATTEMPTS", "3"))
    INITIAL_BACKOFF: float = 0.9
    BACKOFF_JITTER: float = 0.35
    TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,60}$")

    default_timeout_seconds: float = float(os.getenv("PLANNER_TIMEOUT_SECONDS", "40.0"))
    ENABLE_FAST_PATH: bool = os.getenv("PLANNER_ENABLE_FAST_PATH", "1") == "1"
    ENABLE_SMARTFAST: bool = os.getenv("PLANNER_ENABLE_SMARTFAST", "1") == "1"
    STRICT_SHORT: bool = os.getenv("PLANNER_STRICT_SHORT", "1") == "1"
    MIN_OBJECTIVE_LENGTH: int = int(os.getenv("PLANNER_SHORT_OBJECTIVE_MIN_LEN", "12"))
    LOW_TIME_THRESHOLD: float = 3.5  # seconds remaining instruct early bail

    # -----------------------------------------------------------------------
    # Public Entry
    # -----------------------------------------------------------------------
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None
    ) -> MissionPlanSchema:
        raw_objective = (objective or "").strip()
        if not raw_objective:
            raise PlannerError("Empty objective supplied.", self.name, raw_objective)

        objective = self._normalize_objective(raw_objective)

        # Fast path routing
        routed = self._route_objective(objective)
        if routed:
            _log_debug(f"ROUTED fast_path='{routed['route']}'")
            return self._build_schema(routed["data"], objective)

        if maestro is None:
            raise PlannerError("generation_service (maestro) unavailable.", self.name, objective)

        if not self.quick_validate_objective(objective):
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                return self._build_schema(self._fallback_data(objective), objective)
            raise PlannerError("Objective failed quick validation.", self.name, objective)

        # Tool grounding
        tool_inventory = self._gather_tool_inventory()
        prompt = self._construct_meta_prompt(objective, context, tool_inventory)
        conversation_id = f"plan-{uuid.uuid4()}"

        start_time = time.monotonic()
        plan_dict: Optional[Dict[str, Any]] = None

        # Attempt strict JSON mode if available
        try:
            plan_dict = self._attempt_strict_json_mode(
                objective=objective,
                prompt=prompt,
                tool_inventory=tool_inventory,
                conversation_id=conversation_id,
                start=start_time
            )
        except PlannerError as exc:
            _log_debug(f"Strict JSON mode PlannerError: {exc}")
        except Exception as exc:  # pragma: no cover
            _log_debug(f"Strict JSON unexpected exception: {exc}")

        # If strict JSON failed or unsupported, use multi-strategy textual ladder
        if plan_dict is None:
            try:
                raw_answer = self._call_llm_with_strategies(
                    prompt=prompt,
                    conversation_id=conversation_id,
                    objective=objective,
                    start_time=start_time
                )
                json_text = self._sanitize_and_extract_json(raw_answer, objective)
                plan_dict = self._robust_parse_json(json_text, objective)
            except Exception as exc:
                _log_debug(f"Strategy + parsing pipeline failed: {exc}")
                if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                    plan_dict = self._fallback_data(objective)
                else:
                    raise PlannerError(f"Failed to obtain valid plan: {exc}", self.name, objective) from exc

        # Clean / enforce
        plan_dict = self._postprocess_parsed_plan(plan_dict, objective, tool_inventory)
        schema_obj = self._build_schema(plan_dict, objective)
        self._validate_dag(schema_obj, objective)
        return schema_obj

    # -----------------------------------------------------------------------
    # Routing Layer
    # -----------------------------------------------------------------------
    def _route_objective(self, objective: str) -> Optional[Dict[str, Any]]:
        """
        Returns: dict {route: <name>, data: <plan_dict>} or None to proceed with LLM.
        Fast path categories:
          - File creation
          - Greeting
          - Simple list
          - Micro-answer (short conceptual ask)
        """
        if self.ENABLE_FAST_PATH and self._is_file_creation(objective):
            return {"route": "file_fast", "data": self._plan_file_fast(objective)}

        if self.ENABLE_SMARTFAST:
            g_or_l = self._smart_greeting_or_list(objective)
            if g_or_l:
                return g_or_l

        # Micro generic answer
        if len(objective) < 55 and not re.search(r"\b(file|ملف)\b", objective, re.IGNORECASE):
            return {
                "route": "micro_generic",
                "data": {
                    "objective": objective,
                    "tasks": [
                        {
                            "task_id": "answer",
                            "description": f"Produce a concise answer for: {objective}",
                            "tool_name": "generic_think",
                            "tool_args": {"mode": "answer"},
                            "dependencies": []
                        }
                    ]
                }
            }
        return None

    # -----------------------------------------------------------------------
    # Objective Normalization
    # -----------------------------------------------------------------------
    def _normalize_objective(self, objective: str) -> str:
        if len(objective) >= self.MIN_OBJECTIVE_LENGTH:
            return objective
        if self.STRICT_SHORT:
            return objective
        augmented = f"Short objective: {objective}. Provide a minimal actionable plan."
        _log_debug(f"Augmented short objective '{objective}' → '{augmented}'")
        return augmented

    # -----------------------------------------------------------------------
    # Tool Inventory / Grounding
    # -----------------------------------------------------------------------
    def _gather_tool_inventory(self) -> List[Dict[str, Any]]:
        """
        Build a list of available tools with minimal summaries.
        Ensures 'generic_think' always present.
        """
        tools: List[Dict[str, Any]] = []
        if agent_tools and hasattr(agent_tools, "_TOOL_REGISTRY"):
            registry = getattr(agent_tools, "_TOOL_REGISTRY")
            if isinstance(registry, dict):
                for name, meta in registry.items():
                    summary = ""
                    if isinstance(meta, dict):
                        summary = meta.get("description") or meta.get("summary") or ""
                    tools.append({
                        "name": str(name),
                        "summary": summary[:200] if summary else ""
                    })

        # Guarantee 'generic_think'
        names = {t["name"] for t in tools}
        if "generic_think" not in names:
            tools.append({"name": "generic_think", "summary": "LLM cognitive reasoning / thinking step."})
        return tools

    # -----------------------------------------------------------------------
    # Prompt Construction (Grounded)
    # -----------------------------------------------------------------------
    def _construct_meta_prompt(
        self,
        objective: str,
        context: Optional[PlanningContext],
        tool_inventory: List[Dict[str, Any]]
    ) -> str:
        ctx_block = self._context_block(context) if context else "None."
        max_tasks_dynamic = min(self.MAX_TASKS, 50 if len(objective) > 180 else 25 if len(objective) > 90 else 15)

        tool_lines = []
        for t in tool_inventory:
            tool_lines.append(f"- {t['name']}: {t['summary'] or '[no summary]'}")

        grounded_rules = (
            "YOU MUST ONLY USE THESE TOOLS (no invention, no web_search, no imaginary tools):\n"
            + os.linesep.join(tool_lines)
            + "\nIf a tool you think you need is NOT listed above, RESTRUCTURE using only allowed tools.\n"
        )

        output_binding_rules = """
OUTPUT BINDING / CONTEXT BRIDGING:
- A later task may re-use textual output of a previous task by referencing a placeholder inside tool_args.
- Pattern: "${previous_task_id.output}" inside tool_args for tasks depending on a prior result.
- When referencing previous output, ADD that previous task_id to dependencies.
Example:
  Task A (task_id: analyze) -> tool: generic_think
  Task B (task_id: summarize) depends on analyze and has:
     "tool_args": {"source": "${analyze.output}"}
"""

        short_mode = len(objective) < 70
        if short_mode:
            return (
                "Return ONLY valid JSON (no markdown, no commentary).\n"
                f'Objective: "{objective}"\n'
                "Keys: objective, tasks.\n"
                "Each task: {task_id, description, tool_name, tool_args, dependencies[]}\n"
                f"tasks count <= {10 if max_tasks_dynamic > 10 else max_tasks_dynamic}\n"
                "Use only allowed tools.\n"
                + grounded_rules +
                "JSON only."
            )

        return f"""
SYSTEM ROLE:
You are a grounded decomposition & planning engine. Generate a realistic DAG of tasks
that can be executed by the orchestrator. DO NOT hallucinate tools.

OBJECTIVE:
\"\"\"{objective}\"\"\"

CONTEXT (metadata):
{ctx_block}

{grounded_rules}

{output_binding_rules}

STRICT OUTPUT FORMAT (JSON ONLY):
{{
  "objective": "...",
  "tasks": [
     {{
       "task_id": "short_id",
       "description": "Action",
       "tool_name": "one_of_listed_tools",
       "tool_args": {{}},
       "dependencies": []
     }}
  ]
}}

RULES:
- Return ONLY a single JSON object. No backticks, no prose outside JSON.
- task_id: short, unique, [a-zA-Z0-9_-].
- dependencies: only list previous task_ids (acyclic).
- If reusing previous output, put "${{prev_task_id.output}}" in tool_args and include dependency.
- Keep tasks <= {max_tasks_dynamic}.
- Parallelize where safe; avoid unnecessary deep chains.
- A plan using unlisted tools is invalid; reframe using available tools.
- If uncertain, produce a minimal valid plan.

JSON ONLY. NO MARKDOWN. NO EXTRA TEXT
""".strip()

    def _context_block(self, context: PlanningContext) -> str:
        parts: List[str] = []
        if getattr(context, "past_failures", None):
            parts.append(f"PastFailures({len(context.past_failures)})")
        if getattr(context, "user_preferences", None):
            parts.append(f"UserPrefs({len(context.user_preferences)})")
        if getattr(context, "tags", None):
            parts.append("Tags:" + ",".join(context.tags))
        return " | ".join(parts) if parts else "None."

    # -----------------------------------------------------------------------
    # Fast Paths
    # -----------------------------------------------------------------------
    def _is_file_creation(self, objective: str) -> bool:
        obj = objective.lower().strip()
        verbs = (
            "create", "make", "write", "generate", "build", "produce", "add",
            "اصنع", "انشئ", "أنشئ", "اكتب", "أضف", "اضف"
        )
        if any(obj.startswith(v) for v in verbs):
            if "file" in obj or "ملف" in obj:
                return True
        return bool(re.match(r"^(create|write|make|generate)\s+.*file", obj))

    def _infer_filename(self, objective: str) -> str:
        m = re.search(r"(?:named|call(?:ed)?|اسم(?:ه)?)\s+([A-Za-z0-9_\-\.]+)", objective, re.IGNORECASE)
        if m:
            name = m.group(1)
            if not name.lower().endswith((".md", ".txt", ".log", ".py", ".json")):
                return f"{name}.md"
            return name
        base = re.sub(r"[^a-zA-Z0-9_\-]+", "_", objective.lower()).strip("_") or "auto_file"
        if not base.endswith(".md"):
            base += ".md"
        return base[:80]

    def _plan_file_fast(self, objective: str) -> Dict[str, Any]:
        return {
            "objective": objective,
            "tasks": [
                {
                    "task_id": "create_file",
                    "description": f"Create a file addressing: {objective}",
                    "tool_name": "write_file",
                    "tool_args": {
                        "path": self._infer_filename(objective),
                        "content": f"# Auto Generated File\n\nObjective: {objective}\n\n(Initial draft.)\n"
                    },
                    "dependencies": []
                }
            ]
        }

    def _smart_greeting_or_list(self, objective: str) -> Optional[Dict[str, Any]]:
        o = objective.lower().strip()
        greet_patterns = [
            r"^hi$", r"^hello$", r"^hey$", r"^مرحبا$", r"^اهلا$", r"^تحية$", r"^say hi$"
        ]
        list_hints = [
            "list ", "enumerate ", "advantages", "benefits", "improvements",
            "خطوات", "مزايا", "فوائد", "points", "reasons"
        ]
        if any(re.match(p, o) for p in greet_patterns):
            return {
                "route": "greeting",
                "data": {
                    "objective": objective,
                    "tasks": [
                        {
                            "task_id": "greet",
                            "description": "Produce a warm concise greeting",
                            "tool_name": "generic_think",
                            "tool_args": {"style": "greeting"},
                            "dependencies": []
                        }
                    ]
                }
            }
        if len(o) < 160 and any(h in o for h in list_hints):
            return {
                "route": "list_simple",
                "data": {
                    "objective": objective,
                    "tasks": [
                        {
                            "task_id": "list",
                            "description": f"Generate enumerated list for: {objective}",
                            "tool_name": "generic_think",
                            "tool_args": {"mode": "list"},
                            "dependencies": []
                        }
                    ]
                }
            }
        return None

    # -----------------------------------------------------------------------
    # Strict JSON Mode Attempt
    # -----------------------------------------------------------------------
    def _attempt_strict_json_mode(
        self,
        objective: str,
        prompt: str,
        tool_inventory: List[Dict[str, Any]],
        conversation_id: str,
        start: float
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to use maestro.generate_json(schema=...) if available.
        Returns dict or None if unsupported / time insufficient.
        """
        if not hasattr(maestro, "generate_json"):
            return None

        elapsed = time.monotonic() - start
        if self.default_timeout_seconds - elapsed < self.LOW_TIME_THRESHOLD:
            _log_debug("Skipping strict JSON mode (low time).")
            return None

        schema = {
            "type": "object",
            "properties": {
                "objective": {"type": "string"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "description": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "tool_args": {"type": "object"},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["task_id", "description", "tool_name", "tool_args", "dependencies"]
                    }
                }
            },
            "required": ["objective", "tasks"]
        }

        _log_debug("Attempting strict JSON mode (generate_json)...")
        try:
            response = maestro.generate_json(  # type: ignore
                prompt=prompt,
                schema=schema,
                conversation_id=conversation_id,
                model=os.getenv("PLANNER_MODEL_OVERRIDE") or None
            )
        except Exception as exc:
            raise PlannerError(f"Strict JSON generation failed: {exc}", self.name, objective) from exc

        if not isinstance(response, dict):
            raise PlannerError("Strict JSON mode returned non-dict.", self.name, objective)

        if "tasks" not in response or not isinstance(response["tasks"], list):
            raise PlannerError("Strict JSON mode missing tasks array.", self.name, objective)

        return response

    # -----------------------------------------------------------------------
    # Multi-Strategy textual attempts
    # -----------------------------------------------------------------------
    def _call_llm_with_strategies(
        self,
        prompt: str,
        conversation_id: str,
        objective: str,
        start_time: float
    ) -> str:
        strategies: List[Tuple[str, str]] = [
            ("strict_full", prompt),
            ("structured_template", self._inject_structural_template(prompt)),
            ("minimal_hint", self._minimal_hint_prompt(objective)),
        ]
        last_error = None

        for strategy_index, (label, sprompt) in enumerate(strategies, start=1):
            attempts = self.RETRY_ATTEMPTS
            _log_debug(f"Strategy {strategy_index}/{len(strategies)} '{label}' start")
            adaptive_prompt = sprompt
            for attempt in range(1, attempts + 1):
                elapsed = time.monotonic() - start_time
                remaining = self.default_timeout_seconds - elapsed
                if remaining <= self.LOW_TIME_THRESHOLD:
                    _log_debug("Remaining time low → abort strategies early.")
                    raise PlannerError("Low time budget", self.name, objective)

                # Choose generation function
                gen_fn: Optional[Callable[..., Any]] = None
                if hasattr(maestro, "generate_text"):
                    gen_fn = getattr(maestro, "generate_text")
                elif hasattr(maestro, "forge_new_code"):
                    gen_fn = getattr(maestro, "forge_new_code")

                if gen_fn is None:
                    raise PlannerError("No usable LLM generation function.", self.name, objective)

                t0 = time.monotonic()
                try:
                    _log_debug(f"Strategy '{label}' attempt {attempt}/{attempts}")
                    kwargs = dict(prompt=adaptive_prompt, conversation_id=conversation_id)
                    model_override = os.getenv("PLANNER_MODEL_OVERRIDE")
                    if model_override:
                        kwargs["model"] = model_override
                    response = gen_fn(**kwargs)  # type: ignore
                    latency = time.monotonic() - t0
                    # Expect response could be dict or simple text
                    answer, status = self._extract_answer_and_status(response)
                    _log_debug(f"LLM latency: {latency:.2f}s status={status}")
                    if status not in ("success", "ok") or not answer:
                        raise RuntimeError(f"Bad status/empty answer (status={status})")
                    return answer[: self.MAX_OUTPUT_CHARS]
                except Exception as exc:
                    last_error = str(exc)
                    _log_debug(f"Strategy '{label}' attempt {attempt} failed: {last_error}")
                    if attempt < attempts:
                        adaptive_prompt = self._shrink_prompt(adaptive_prompt)
                        backoff = self._compute_backoff(attempt)
                        _log_debug(f"Backoff {backoff:.2f}s then retry with shrunk prompt size={len(adaptive_prompt)}")
                        time.sleep(backoff)
                    else:
                        _log_debug(f"Strategy '{label}' exhausted attempts.")
                        # Continue to next strategy
                        continue
        raise PlannerError(f"All strategies failed. Last error: {last_error}", self.name, objective)

    def _inject_structural_template(self, base_prompt: str) -> str:
        template = """
FOLLOW THIS EXACT JSON SHAPE (NO EXTRA TEXT):
{
 "objective": "...",
 "tasks": [
    {
      "task_id": "task_one",
      "description": "Brief action",
      "tool_name": "generic_think",
      "tool_args": {},
      "dependencies": []
    }
 ]
}
Return only filled JSON.
"""
        return base_prompt + "\n\n" + template

    def _minimal_hint_prompt(self, objective: str) -> str:
        return (
            "Return ONLY JSON with keys: objective, tasks.\n"
            f'Objective: "{objective}"\n'
            'If unsure, produce a single task using "generic_think".\n'
            'Each task fields: task_id, description, tool_name, tool_args, dependencies.\n'
            "JSON only."
        )

    # -----------------------------------------------------------------------
    # LLM response extraction + JSON sanitization
    # -----------------------------------------------------------------------
    def _extract_answer_and_status(self, response: Any) -> Tuple[str, str]:
        """
        Normalize differing response shapes from generation service.
        Expected possibilities:
          - dict with keys: {"answer": str, "status": "success"}
          - dict with "text"
          - plain string
        """
        if isinstance(response, str):
            return response, "success"
        if isinstance(response, dict):
            if "answer" in response and isinstance(response["answer"], str):
                return response["answer"], str(response.get("status", "success"))
            if "text" in response and isinstance(response["text"], str):
                return response["text"], str(response.get("status", "success"))
            # Fallback: first str value
            for v in response.values():
                if isinstance(v, str):
                    return v, str(response.get("status", "success"))
        return "", "error"

    def _sanitize_and_extract_json(self, raw: str, objective: str) -> str:
        """
        Attempts to isolate largest JSON object substring.
        Removes backticks/fences, trims extraneous text.
        """
        text = raw.strip()
        # Remove code fences
        text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).replace("```", "")
        # Direct object?
        if text.startswith("{") and text.endswith("}"):
            return text
        # Find widest braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
            _log_debug("Could not isolate JSON object; using fallback plan.")
            return json.dumps(self._fallback_data(objective), ensure_ascii=False)
        raise PlanValidationError("Failed to isolate JSON object.", self.name, objective)

    # -----------------------------------------------------------------------
    # JSON Parsing & Validation
    # -----------------------------------------------------------------------
    def _robust_parse_json(self, text: str, objective: str) -> Dict[str, Any]:
        try:
            return self._validate_parsed_object(json.loads(text), objective)
        except Exception as e1:
            _log_debug(f"json.loads failed: {e1}")
            if json5:
                try:
                    return self._validate_parsed_object(json5.loads(text), objective)
                except Exception as e2:
                    _log_debug(f"json5 parse failed: {e2}")
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                return self._fallback_data(objective)
            raise PlanValidationError("JSON parse failed with no fallback permitted.", self.name, objective)

    def _validate_parsed_object(self, data: Any, objective: str) -> Dict[str, Any]:
        if not isinstance(data, dict):
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                return self._fallback_data(objective)
            raise PlanValidationError("Top-level JSON must be an object.", self.name, objective)
        tasks = data.get("tasks")
        if tasks is None:
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                data["tasks"] = self._fallback_data(objective)["tasks"]
            else:
                raise PlanValidationError("Missing 'tasks' key.", self.name, objective)
        if not isinstance(data["tasks"], list):
            raise PlanValidationError("'tasks' must be a list.", self.name, objective)
        data.setdefault("objective", objective)
        return data

    def _postprocess_parsed_plan(
        self,
        plan_dict: Dict[str, Any],
        objective: str,
        tool_inventory: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        self._enforce_limits(plan_dict, objective)
        allowed_tool_names = {t["name"] for t in tool_inventory}
        cleaned_tasks: List[Dict[str, Any]] = []
        for raw_task in plan_dict.get("tasks", []):
            try:
                cleaned = self._transform_raw_task(raw_task, objective, allowed_tool_names)
                cleaned_tasks.append(cleaned)
            except Exception as exc:
                _log_debug(f"Skipping invalid task entry: {exc}")
        if not cleaned_tasks:
            cleaned_tasks = self._fallback_data(objective)["tasks"]
        plan_dict["tasks"] = cleaned_tasks
        return plan_dict

    # -----------------------------------------------------------------------
    # Limits & Task Transformation
    # -----------------------------------------------------------------------
    def _enforce_limits(self, data: Dict[str, Any], objective: str):
        tasks = data.get("tasks") or []
        if not isinstance(tasks, list):
            raise PlanValidationError("'tasks' must be list during limit enforcement.", self.name, objective)
        if len(tasks) > self.MAX_TASKS:
            _log_debug(f"Truncating tasks from {len(tasks)} → {self.MAX_TASKS}")
            data["tasks"] = tasks[: self.MAX_TASKS]
        if os.getenv("PLANNER_JSON_FORCE_SINGLE_TASK", "0") == "1":
            data["tasks"] = tasks[:1]

    def _transform_raw_task(
        self,
        task: Any,
        objective: str,
        allowed_tool_names: Set[str]
    ) -> Dict[str, Any]:
        if not isinstance(task, dict):
            raise PlanValidationError("Task entry not an object.", self.name, objective)

        tid = (task.get("task_id") or task.get("id") or "").strip()
        if not tid:
            tid = f"task_{uuid.uuid4().hex[:6]}"
        if not self.TASK_ID_PATTERN.match(tid):
            tid = re.sub(r"[^a-zA-Z0-9_\-]", "_", tid)[:60] or f"task_{uuid.uuid4().hex[:4]}"

        desc = (task.get("description") or task.get("desc") or "").strip()
        if not desc:
            desc = f"Execute {tid} to advance objective."

        tool_name = (task.get("tool_name") or task.get("tool") or "generic_think").strip() or "generic_think"
        if tool_name not in allowed_tool_names:
            _log_debug(f"Unknown tool '{tool_name}' → forcing 'generic_think'.")
            tool_name = "generic_think"

        tool_args = task.get("tool_args") or task.get("args") or {}
        if not isinstance(tool_args, dict):
            tool_args = {}

        deps_raw = task.get("dependencies") or task.get("depends_on") or []
        if not isinstance(deps_raw, list):
            deps_raw = []
        cleaned_deps: List[str] = []
        seen = set()
        for d in deps_raw:
            if isinstance(d, str):
                d2 = d.strip()
                if d2 and d2 != tid and d2 not in seen:
                    seen.add(d2)
                    cleaned_deps.append(d2)

        return {
            "task_id": tid,
            "description": desc,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "dependencies": cleaned_deps
        }

    def _build_schema(self, data: Dict[str, Any], objective: str) -> MissionPlanSchema:
        # Convert list of dict tasks to schema objects if underlying schema requires
        tasks_out: List[Any] = []
        for t in data.get("tasks", []):
            if isinstance(t, PlannedTask):
                tasks_out.append(t)
            else:
                try:
                    tasks_out.append(PlannedTask(**t))
                except Exception:
                    # Fallback simple dict if schema dataclass fails (to preserve minimal shape)
                    tasks_out.append(t)
        try:
            return MissionPlanSchema(objective=data.get("objective", objective), tasks=tasks_out)
        except Exception as exc:
            _log_debug(f"MissionPlanSchema validation failed: {exc}")
            if os.getenv("PLANNER_FALLBACK_ON_PARSE", "1") == "1":
                fb = self._fallback_data(objective)
                fb_tasks = [PlannedTask(**x) for x in fb["tasks"]]
                return MissionPlanSchema(objective=objective, tasks=fb_tasks)
            raise PlanValidationError(f"Schema validation failed: {exc}", self.name, objective) from exc

    # -----------------------------------------------------------------------
    # DAG Validation
    # -----------------------------------------------------------------------
    def _validate_dag(self, plan: MissionPlanSchema, objective: str):
        tasks = getattr(plan, "tasks", [])
        ids: Set[str] = set()
        adjacency: Dict[str, List[str]] = {}
        indeg: Dict[str, int] = {}

        # Collect node ids
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
            deps = getattr(t, "dependencies", []) if hasattr(t, "dependencies") else t.get("dependencies", [])
            if not isinstance(deps, list):
                raise PlanValidationError(f"Dependencies not list in '{tid}'", self.name, objective)
            for d in deps:
                if d == tid:
                    raise PlanValidationError(f"Self-dependency in '{tid}'", self.name, objective)
                if d not in ids:
                    raise PlanValidationError(f"Unknown dependency '{d}' for '{tid}'", self.name, objective)
                adjacency[d].append(tid)
                indeg[tid] += 1

        # Kahn's topological check
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

    # -----------------------------------------------------------------------
    # Fallback Data (contextual minimal plan)
    # -----------------------------------------------------------------------
    def _fallback_data(self, objective: str) -> Dict[str, Any]:
        return {
            "objective": objective,
            "tasks": [
                {
                    "task_id": "analyze",
                    "description": f"Analyze objective: {objective}",
                    "tool_name": "generic_think",
                    "tool_args": {},
                    "dependencies": []
                },
                {
                    "task_id": "produce",
                    "description": "Produce final answer using previous analysis",
                    "tool_name": "generic_think",
                    "tool_args": {"source": "${analyze.output}"},
                    "dependencies": ["analyze"]
                }
            ]
        }

    # -----------------------------------------------------------------------
    # Backoff & Helpers
    # -----------------------------------------------------------------------
    def _compute_backoff(self, attempt: int) -> float:
        base = self.INITIAL_BACKOFF * (2 ** (attempt - 1))
        jitter = random.uniform(0, self.BACKOFF_JITTER)
        return base + jitter

    def _shrink_prompt(self, prompt: str) -> str:
        if len(prompt) <= 1800:
            return prompt
        # Keep head (system instructions) + tail (format section)
        head = prompt[:900]
        tail = prompt[-500:]
        shrunk = head + "\n...SNIP...\n" + tail
        _log_debug(f"Prompt shrunk from {len(prompt)} to {len(shrunk)}")
        return shrunk


# ---------------------------------------------------------------------------
# Notes / Integration Hints
# ---------------------------------------------------------------------------
"""
Integration / Execution Layer Notes:

1) Do NOT change MissionPlanSchema now; tasks still:
     task_id, description, tool_name, tool_args, dependencies
2) Execution layer should substitute ${task_id.output} placeholders:
     - Before invoking tool for a task, scan tool_args values (recursively if needed),
       replace occurrences with the actual prior task output (e.g., result_text / final answer).
3) If maestro.generate_json is absent, multi-strategy textual fallback ensures resilience.
4) Enable verbose logs via PLANNER_LOG_VERBOSE=1
5) Unknown or hallucinated tools are replaced with 'generic_think' early to avoid runtime tool errors.
6) For extremely short objectives, if STRICT_SHORT=0 planner auto-augments them; if =1 it leaves them as-is.
"""