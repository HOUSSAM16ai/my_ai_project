# app/services/generation_service.py
#
# ======================================================================================
# ==                          MAESTRO COGNITIVE ORCHESTRATOR (v14.0.0)               ==
# ==                       Overmind-Compatible Tactical Subsystem                     ==
# ======================================================================================
#
# PRIME DIRECTIVE:
#   This service is the TACTICAL execution engine. It operates within the scope of a
#   single, well-defined TASK provided by the Overmind. It is responsible for the
#   short-term, iterative reasoning loop required to complete that task.
#
#   It no longer manages its own long-term memory; it logs its actions as EVENTS
#   against the parent MISSION, contributing to the eternal Akashic Record.
#
# NOTE:
#   This version is a MAJOR refactor. It REMOVES the concept of a "conversation"
#   and now requires a `mission_id` and `task` context to operate. The public
#   entry point `forge_new_code` is now `execute_task`.

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from flask import current_app
from app import db

# --- [THE NEW REALITY] ---
# Import the new models and helper functions from the Grand Blueprint.
from app.models import (
    Mission, Task, MissionEvent,
    log_mission_event, finalize_task, MissionEventType, TaskStatus
)

# --- External cognitive substrates ---
from .llm_client_service import get_llm_client
from . import agent_tools
from . import system_service

__version__ = "14.0.0"

# --------------------------------------------------------------------------------------
# Data Contracts (Remain the same, as they describe the internal loop)
# --------------------------------------------------------------------------------------
@dataclass
class StepState: # ... (as before)
@dataclass
class OrchestratorConfig: # ... (as before)
@dataclass
class OrchestratorTelemetry: # ... (as before)

# --------------------------------------------------------------------------------------
# Internal Helpers (Adapted for the new reality)
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

def _format_identity_block(task: Task, code_context: Any, wisdom_context: Any) -> str:
    # The identity is now task-focused
    return f"""
You are the MAESTRO (v{__version__}), a tactical AI subsystem. Your current directive is to execute a single task within a larger mission.
MISSION OBJECTIVE: {task.mission.objective}
CURRENT TASK: "{task.description}"

You must focus exclusively on completing this task. Use your tools to gather information and formulate a response or action.
Contextual Architectural Memory:
---
{_serialize_safe(code_context)}
---
Relevant Historical Experiences:
---
{_serialize_safe(wisdom_context)}
---
""".strip()

# --------------------------------------------------------------------------------------
# PUBLIC ORCHESTRATION ENTRY (THE NEW INTERFACE)
# --------------------------------------------------------------------------------------
def execute_task(
    task: Task,
    mission: Mission,
    task_history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    The new primary entry point. Orchestrates the completion of a single Task.
    It is STATEFUL within the task, but STATELESS across tasks.
    """
    cfg = OrchestratorConfig(...) # Load config as before
    telemetry = OrchestratorTelemetry()
    step_states: List[StepState] = []
    tool_usage_sequence: List[str] = []
    previous_tool_names_snapshot: List[str] = []
    consecutive_no_progress = 0
    final_answer = "(Task did not produce a final answer)"

    current_app.logger.info(f"[Maestro] Executing Task #{task.id} for Mission #{mission.id}")
    task.status = TaskStatus.RUNNING
    db.session.commit()

    try:
        client = get_llm_client()
        
        # --- Bootstrap context (as before) ---
        code_ctx_res = system_service.find_related_context(task.description)
        # wisdom_ctx_res = ... (wisdom can be adapted later)
        
        identity_prompt = {"role": "system", "content": _format_identity_block(task, code_ctx_res.data, {})}
        
        messages: List[Dict[str, Any]] = [identity_prompt]
        if task_history:
            messages.extend(task_history)
        else:
            # The "prompt" for the task is its description
            messages.append({"role": "user", "content": task.description})

        tools_schema = agent_tools.get_tools_schema()
        
        # --- Main Cognitive Loop ---
        for step_idx in range(cfg.max_steps):
            state = StepState(step_index=step_idx)
            step_states.append(state)
            telemetry.steps_taken = step_idx + 1

            # ... (History compression logic can be adapted here if needed) ...

            # Sanitize messages before API call
            for m in messages:
                if m.get("content") is None: m["content"] = ""
            
            # LLM Decision
            llm_response = client.chat.completions.create(
                model=cfg.model_name,
                messages=messages,
                tools=tools_schema,
                tool_choice="auto"
            )
            raw_response_message = llm_response.choices[0].message
            tool_calls = getattr(raw_response_message, "tool_calls", None) or []
            
            # --- The new logging mechanism: Log events, not messages ---
            assistant_dict = _normalize_assistant_message(raw_response_message)
            messages.append(assistant_dict)
            log_mission_event(
                mission,
                MissionEventType.TASK_UPDATED,
                payload={"task_id": task.id, "step": step_idx, "decision": assistant_dict},
                note="Maestro reasoning step."
            )

            if tool_calls:
                state.decision = "tool"
                # ... (Logic for tool calls, repetition guards, etc. remains largely the same)
                # ... but instead of _save_message, we use log_mission_event

                for call in tool_calls:
                    # ... (extract t_name, args)
                    tool_result = _invoke_tool(t_name, args)
                    # ... (update telemetry)
                    tool_payload = tool_result.to_dict()
                    
                    messages.append({
                        "role": "tool",
                        "name": t_name,
                        "tool_call_id": call.id,
                        "content": _serialize_safe(tool_payload)
                    })
                    log_mission_event(
                        mission,
                        MissionEventType.TASK_UPDATED,
                        payload={"task_id": task.id, "tool_result": tool_payload},
                        note=f"Tool '{t_name}' executed."
                    )
                # ... (Stagnation detection logic as before) ...
                continue

            # NO TOOL BRANCH -> Final answer for the TASK
            else:
                state.decision = "final"
                final_answer = assistant_dict.get("content") or "(no textual content)"
                telemetry.finalization_reason = "model_concluded"
                state.finish()
                break
        
        # ... (Handle loop exhaustion as before) ...

        # Finalize the task in the database
        finalize_task(
            task,
            status=TaskStatus.SUCCESS,
            result_text=final_answer,
            result_meta={"telemetry": telemetry.to_dict(), "steps": [asdict(s) for s in step_states]}
        )
        db.session.commit()
        
        return {"status": "success", "answer": final_answer}

    except Exception as e:
        telemetry.error = f"{type(e).__name__}: {e}"
        current_app.logger.error(f"[Maestro] Catastrophic failure on Task #{task.id}: {e}", exc_info=True)
        
        # Ensure the task is marked as FAILED in the database
        finalize_task(
            task,
            status=TaskStatus.FAILED,
            result_text=f"Catastrophic failure: {e}",
            result_meta={"trace": traceback.format_exc(), "telemetry": telemetry.to_dict()}
        )
        db.session.commit()
        
        return {"status": "error", "message": str(e)}

# --------------------------------------------------------------------------------------
# Helper: _normalize_assistant_message (as before, crucial for stability)
# --------------------------------------------------------------------------------------
def _normalize_assistant_message(raw_msg) -> Dict[str, Any]:
    # ... (Implementation from v13.0.1 is perfect and should be kept here)