# app/services/generation_service.py
#
# ======================================================================================
# ==                          MAESTRO COGNITIVE ORCHESTRATOR (v14.1.0)               ==
# ==                       Context-Aware & Resilient Tactical Subsystem               ==
# ======================================================================================
#
# PRIME DIRECTIVE:
#   This service is the TACTICAL execution engine. It operates within the scope of a
#   single, well-defined TASK provided by the Overmind.
#
# NOTE:
#   This version (v14.1.0) introduces a critical architectural fix. All logic
#   dependent on the Flask application context (like configuration and logging) is
#   now correctly encapsulated within the main execution function. This resolves
#   the `NameError: name 'current_app' is not defined` that occurred during
#   application startup and testing.

from __future__ import annotations

import json
import time
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# --- [CRITICAL FIX] We only import `current_app` here. We DO NOT use it at the top level.
from flask import current_app
from app import db

# Import the new models and helper functions from the Grand Blueprint.
from app.models import (
    Mission, Task,
    log_mission_event, finalize_task, MissionEventType, TaskStatus
)

# External cognitive substrates
from .llm_client_service import get_llm_client
from . import agent_tools
from . import system_service

__version__ = "14.1.0"

# --------------------------------------------------------------------------------------
# Data Contracts (Defined at the top level, as they are context-independent)
# --------------------------------------------------------------------------------------
@dataclass
class StepState:
    step_index: int
    started_ms: float = field(default_factory=lambda: time.perf_counter() * 1000)
    decision: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None

    def finish(self):
        self.duration_ms = round(time.perf_counter() * 1000 - self.started_ms, 2)

@dataclass
class OrchestratorConfig:
    model_name: str
    max_steps: int

@dataclass
class OrchestratorTelemetry:
    steps_taken: int = 0
    tools_invoked: int = 0
    distinct_tools: int = 0
    repeated_tool_blocks: int = 0
    finalization_reason: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)

# --------------------------------------------------------------------------------------
# Internal Helpers (Context-independent helpers)
# --------------------------------------------------------------------------------------
def _serialize_safe(obj: Any) -> str:
    if isinstance(obj, str): return obj
    try: return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception: return repr(obj)

def _invoke_tool(tool_name: str, tool_args: Dict[str, Any]) -> agent_tools.ToolResult:
    meta = getattr(agent_tools, "_TOOL_REGISTRY", {}).get(tool_name)
    if meta and "handler" in meta: return meta["handler"](**tool_args)
    return agent_tools.ToolResult(ok=False, error=f"UNKNOWN_TOOL:{tool_name}")

def _detect_no_progress(prev_tools: List[str], current_tools: List[str]) -> bool:
    return prev_tools and prev_tools == current_tools

def _format_identity_block(task: Task, code_context: Any) -> str:
    return f"""
You are the MAESTRO (v{__version__}), a tactical AI subsystem. Your current directive is to execute a single task within a larger mission.
MISSION OBJECTIVE: {task.mission.objective}
CURRENT TASK: "{task.description}"

Focus exclusively on this task. Use your tools to gather information and formulate a final response or action.
Contextual Architectural Memory relevant to your task:
---
{_serialize_safe(code_context)}
---
""".strip()

def _normalize_assistant_message(raw_msg) -> Dict[str, Any]:
    content = raw_msg.content if getattr(raw_msg, "content", None) is not None else ""
    base = {"role": getattr(raw_msg, "role", "assistant"), "content": content}
    raw_tool_calls = getattr(raw_msg, "tool_calls", None) or []
    if raw_tool_calls:
        base["tool_calls"] = [tc.model_dump() for tc in raw_tool_calls]
    return base

# --------------------------------------------------------------------------------------
# PUBLIC ORCHESTRATION ENTRY (The single, context-aware entry point)
# --------------------------------------------------------------------------------------
def execute_task(task: Task) -> None:
    """
    Orchestrates the completion of a single Task. All context-dependent operations
    (logging, config) are safely performed within this function's scope.
    """
    # --- [CRITICAL FIX] Configuration is now loaded INSIDE the function ---
    # This ensures `current_app` exists and is available when we need it.
    cfg = OrchestratorConfig(
        model_name=current_app.config.get("DEFAULT_AI_MODEL", "openai/gpt-4o"),
        max_steps=current_app.config.get("AGENT_MAX_STEPS", 5)
    )

    mission = task.mission
    telemetry = OrchestratorTelemetry()
    step_states: List[StepState] = []
    tool_usage_sequence: List[str] = []
    previous_tool_names_snapshot: List[str] = []
    final_answer = "(Task did not produce a final textual answer)"

    # --- Start of context-safe operations ---
    current_app.logger.info(f"[Maestro] Executing Task #{task.id} for Mission #{mission.id}")
    task.status = TaskStatus.RUNNING
    log_mission_event(mission, MissionEventType.TASK_STATUS_CHANGE, payload={"task_id": task.id, "status": "RUNNING"})
    db.session.commit()

    try:
        client = get_llm_client()
        code_ctx_res = system_service.find_related_context(task.description)
        
        identity_prompt = {"role": "system", "content": _format_identity_block(task, code_ctx_res.data)}
        messages: List[Dict[str, Any]] = [identity_prompt, {"role": "user", "content": task.description}]
        tools_schema = agent_tools.get_tools_schema()

        # --- Main Cognitive Loop ---
        for step_idx in range(cfg.max_steps):
            state = StepState(step_index=step_idx)
            step_states.append(state)
            telemetry.steps_taken = step_idx + 1
            
            for m in messages:
                if m.get("content") is None: m["content"] = ""
            
            llm_response = client.chat.completions.create(model=cfg.model_name, messages=messages, tools=tools_schema, tool_choice="auto")
            raw_response_message = llm_response.choices[0].message
            tool_calls = getattr(raw_response_message, "tool_calls", None) or []
            
            assistant_dict = _normalize_assistant_message(raw_response_message)
            messages.append(assistant_dict)
            log_mission_event(mission, MissionEventType.TASK_UPDATED, payload={"task_id": task.id, "step": step_idx, "decision": assistant_dict}, note="Maestro reasoning step.")

            if tool_calls:
                state.decision = "tool"
                new_tool_names = [call.function.name for call in tool_calls]

                if _detect_no_progress(previous_tool_names_snapshot, new_tool_names):
                    telemetry.finalization_reason = "stagnation_detected"
                    break

                previous_tool_names_snapshot = new_tool_names
                tool_usage_sequence.extend(new_tool_names)
                
                for call in tool_calls:
                    tool_result = _invoke_tool(call.function.name, json.loads(call.function.arguments))
                    messages.append({"role": "tool", "tool_call_id": call.id, "name": call.function.name, "content": _serialize_safe(tool_result.to_dict())})
                    log_mission_event(mission, MissionEventType.TASK_UPDATED, payload={"task_id": task.id, "tool_result": tool_result.to_dict()}, note=f"Tool '{call.function.name}' executed.")
                continue
            else:
                state.decision = "final"
                final_answer = assistant_dict.get("content") or "(no textual content)"
                telemetry.finalization_reason = "model_concluded"
                state.finish()
                break
        else:
            telemetry.finalization_reason = "max_steps_exhausted"
        
        finalize_task(
            task, status=TaskStatus.SUCCESS, result_text=final_answer,
            result_meta={"telemetry": telemetry.to_dict(), "steps": [asdict(s) for s in step_states]}
        )
        db.session.commit()

    except Exception as e:
        # This is also a context-safe operation
        current_app.logger.error(f"[Maestro] Catastrophic failure on Task #{task.id}: {e}", exc_info=True)
        finalize_task(
            task, status=TaskStatus.FAILED, result_text=f"Catastrophic failure: {e}",
            result_meta={"trace": traceback.format_exc()}
        )
        db.session.commit()