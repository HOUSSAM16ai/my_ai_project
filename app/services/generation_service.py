# app/services/generation_service.py
#
# ======================================================================================
# ==                          MAESTRO COGNITIVE ORCHESTRATOR (v13.0.1)               ==
# ==                    Hyper-Iterative Synthetic Reasoning Subsystem                ==
# ======================================================================================
#
# PRIME DIRECTIVE:
#   This module is the strategic executive cortex. It does NOT touch raw filesystem
#   or code directly. It:
#       - Gathers contextual intelligence (delegated to system_service / memory tools)
#       - Builds an adaptive reasoning plan
#       - Invokes LLM with strict tool schema
#       - Executes tool calls deterministically
#       - Reflects, evaluates progress, prevents unproductive loops
#       - Compresses history to conserve token budget
#       - Archives entire cognitive trace (for audit / replay / analytics)
#
# DESIGN PILLARS:
#   1. Deterministic Contracts: All outward observable actions are logged & persisted.
#   2. Structured Cognition: Each step has a StepState (timing, decisions, deltas).
#   3. Tool Governance: Guard against repetitive, low-value tool invocations.
#   4. Adaptive Context: Optional compression once conversational budget inflates.
#   5. Fail-Fast Safety: Detect stagnation / runaway loops & stop gracefully.
#   6. Extensibility: Clear TODO anchors for critic passes, strategy modules, planners.
#
# NOTE:
#   This version fixes a bug where assistant messages with content=None (e.g. tool-only
#   responses) were appended as raw SDK objects causing downstream JSON + front-end errors.
#

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from flask import current_app
from app import db
from app.models import Message

# External cognitive substrates
from .llm_client_service import get_llm_client
from . import agent_tools   # expects v10+ (dynamic schema + ToolResult)
from . import system_service  # optional: for pre-step context heuristics

# --------------------------------------------------------------------------------------
# Version
# --------------------------------------------------------------------------------------
__version__ = "13.0.1"

# --------------------------------------------------------------------------------------
# Data Contracts
# --------------------------------------------------------------------------------------
@dataclass
class StepState:
    step_index: int
    started_ms: float = field(default_factory=lambda: time.perf_counter() * 1000)
    decision: str = ""                 # "tool" | "final"
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None
    stagnation_flag: bool = False
    history_compressed: bool = False

    def finish(self):
        self.duration_ms = round(time.perf_counter() * 1000 - self.started_ms, 2)


@dataclass
class OrchestratorConfig:
    model_name: str
    max_steps: int = 6
    max_repeated_tool: int = 3          # same tool consecutively
    max_consecutive_no_progress: int = 2
    history_compress_threshold_chars: int = 18000
    history_compress_keep_tail: int = 30
    enable_context_bootstrap: bool = True
    allow_history_compression: bool = True


@dataclass
class OrchestratorTelemetry:
    steps_taken: int = 0
    tools_invoked: int = 0
    distinct_tools: int = 0
    repeated_tool_blocks: int = 0
    compression_events: int = 0
    finalization_reason: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# --------------------------------------------------------------------------------------
# Internal Helpers
# --------------------------------------------------------------------------------------
def _serialize_safe(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return repr(obj)


def _save_message(conversation_id: Optional[str], role: str, content: Any,
                  tool_name: Optional[str] = None, tool_ok: Optional[bool] = None):
    """
    Queues a message for persistence. Commit handled outside for batch efficiency.
    """
    if not conversation_id:
        current_app.logger.debug("Skipping DB save (no conversation_id). Role=%s", role)
        return
    text_content = content if isinstance(content, str) else _serialize_safe(content)
    try:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=text_content,
            tool_name=tool_name,
            tool_ok_status=tool_ok
        )
        db.session.add(msg)
    except Exception as e:
        current_app.logger.error("Failed to queue message (role=%s): %s", role, e, exc_info=True)


def _maybe_compress_history(messages: List[Dict[str, Any]], cfg: OrchestratorConfig, client, model_name: str) -> bool:
    """
    Heuristic compression: If total textual content exceeds threshold, compress user/assistant/tool
    content (excluding system identity prompt).
    Returns True if compression performed.
    """
    if not cfg.allow_history_compression:
        return False

    total_chars = 0
    for m in messages:
        total_chars += len(m.get("content", "") or "")

    if total_chars < cfg.history_compress_threshold_chars:
        return False

    # Gather tail for stronger recency retention
    tail = messages[-cfg.history_compress_keep_tail:] if len(messages) > cfg.history_compress_keep_tail else messages[:]
    to_compress = messages[1: -len(tail)] if len(messages) > (1 + cfg.history_compress_keep_tail) else []

    compress_payload = {
        "summary_scope": "conversation_history_compression",
        "discarded_message_count": len(to_compress),
        "fragments": [
            {
                "role": m.get("role"),
                "excerpt": (m.get("content") or "")[:600]
            }
            for m in to_compress
        ]
    }

    compression_prompt = [
        {
            "role": "system",
            "content": (
                "You are a compression engine. Summarize prior conversation fragments into a concise, "
                "loss-minimized technical digest that preserves: goals, constraints, decisions, tool results. "
                "Respond ONLY with the compressed text."
            )
        },
        {"role": "user", "content": _serialize_safe(compress_payload)}
    ]
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=compression_prompt
        )
        compressed = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        current_app.logger.warning("History compression failed: %s", e)
        return False

    # Rebuild messages: keep first system message as identity, inject compressed summary, add tail
    identity = messages[0]
    new_msgs = [identity,
                {"role": "system", "content": "[COMPRESSED HISTORY DIGEST]\n" + compressed}] + tail
    messages.clear()
    messages.extend(new_msgs)
    return True


def _invoke_tool(tool_name: str, tool_args: Dict[str, Any]) -> agent_tools.ToolResult:
    """
    Secure invocation wrapper. Supports both dynamic handler registry (v10+) and legacy available_tools.
    """
    # Try canonical dynamic registry
    meta = getattr(agent_tools, "_TOOL_REGISTRY", {}).get(tool_name)
    if meta and "handler" in meta:
        handler = meta["handler"]
        return handler(**tool_args)

    # Fallback: legacy dictionary returns text
    if hasattr(agent_tools, "available_tools") and tool_name in agent_tools.available_tools:
        res_text = agent_tools.available_tools[tool_name](**tool_args)
        return agent_tools.ToolResult(ok=True, data={"text": res_text})

    return agent_tools.ToolResult(ok=False, error=f"UNKNOWN_TOOL:{tool_name}")


def _detect_no_progress(prev_tools_snapshot: List[str], current_tools_snapshot: List[str]) -> bool:
    """
    Simple heuristic: if both snapshots identical (order + names), we assume no tool-progress.
    """
    if not prev_tools_snapshot:
        return False
    return prev_tools_snapshot == current_tools_snapshot


def _format_identity_block(code_context: Any, wisdom_context: Any) -> str:
    return f"""
You are the MAESTRO (v{__version__}) — an autonomous, precision orchestration intelligence.
ALLOWED ACTIONS: (1) pure reasoning (2) tool invocation(s).
MANDATORY BEHAVIOR:
 - Inspect before modifying: never propose refactors without first reading target file(s).
 - Provide structured, concise final answers unless user explicitly wants raw content.
 - Avoid redundant tool calls—if you already fetched a file, don't re-fetch unless needed.
 - Plan briefly before acting: you can write a quick bullet plan in your assistant response before calling tools.

Contextual Architectural Memory (vector recall):
---
{_serialize_safe(code_context)}
---

Relevant Historical Dialogue Fragments:
---
{_serialize_safe(wisdom_context)}
---
""".strip()


def _normalize_assistant_message(raw_msg) -> Dict[str, Any]:
    """
    Converts the SDK assistant message object to a plain dict safe for:
      - Reuse in the next API call
      - Front-end rendering
      - Persistence
    Guarantees 'content' is a string ("" if None).
    Preserves tool_calls in expected schema for Azure/OpenAI.
    """
    # raw_msg could be an SDK object with attributes:
    #   role, content, tool_calls
    content = raw_msg.content if getattr(raw_msg, "content", None) is not None else ""
    base = {
        "role": getattr(raw_msg, "role", "assistant"),
        "content": content
    }
    tool_calls_out = []
    raw_tool_calls = getattr(raw_msg, "tool_calls", None) or []
    for tc in raw_tool_calls:
        # tc.function.arguments is expected to be a JSON string (per OpenAI spec)
        function_name = getattr(getattr(tc, "function", None), "name", None)
        function_args = getattr(getattr(tc, "function", None), "arguments", None)
        tool_calls_out.append({
            "id": getattr(tc, "id", ""),
            "type": "function",
            "function": {
                "name": function_name or "unknown_function",
                "arguments": function_args or "{}"
            }
        })
    if tool_calls_out:
        base["tool_calls"] = tool_calls_out
    return base


def _sanitize_messages_for_api(messages: List[Dict[str, Any]]):
    """
    Ensures every message has a string content (never None) before sending to the API.
    """
    for m in messages:
        if "content" not in m or m["content"] is None:
            m["content"] = ""


# --------------------------------------------------------------------------------------
# PUBLIC ORCHESTRATION ENTRY
# --------------------------------------------------------------------------------------
def forge_new_code(
    prompt: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    High-level orchestration entrypoint.
    Returns a dict with status / final synthesized answer or error.
    """
    cfg = OrchestratorConfig(
        model_name=current_app.config.get("DEFAULT_AI_MODEL", "openai/gpt-4o"),
        max_steps=current_app.config.get("AGENT_MAX_STEPS", 6),
        max_repeated_tool=3,
        max_consecutive_no_progress=2,
        history_compress_threshold_chars=current_app.config.get("AGENT_HISTORY_COMPRESS_THRESHOLD", 18000),
        history_compress_keep_tail=current_app.config.get("AGENT_HISTORY_COMPRESS_KEEP_TAIL", 30),
        enable_context_bootstrap=True,
        allow_history_compression=True
    )
    telemetry = OrchestratorTelemetry()
    step_states: List[StepState] = []
    pending_db_commit = True  # we will commit at end unless catastrophic failure
    tool_usage_sequence: List[str] = []
    previous_tool_names_snapshot: List[str] = []
    consecutive_no_progress = 0
    final_answer = "(no answer produced)"

    current_app.logger.info("[Maestro] Begin orchestration (ConvID=%s)", conversation_id)

    try:
        client = get_llm_client()

        # --- Bootstrap external contextual intelligence (optional) ---
        code_ctx = {}
        wisdom_ctx = {}
        if cfg.enable_context_bootstrap:
            try:
                code_res = system_service.find_related_context(prompt)
                if code_res.ok:
                    code_ctx = code_res.data
                else:
                    code_ctx = {"warning": code_res.error}
            except Exception as e:
                code_ctx = {"bootstrap_error": f"code_context_failed: {e}"}

            try:
                wisdom_res = system_service.find_similar_conversations()
                if wisdom_res.ok:
                    wisdom_ctx = wisdom_res.data
                else:
                    wisdom_ctx = {"warning": wisdom_res.error}
            except Exception as e:
                wisdom_ctx = {"bootstrap_error": f"wisdom_context_failed: {e}"}

        identity_system_prompt = {
            "role": "system",
            "content": _format_identity_block(code_ctx, wisdom_ctx)
        }

        messages: List[Dict[str, Any]] = []
        if conversation_history:
            if not conversation_history or conversation_history[0].get("role") != "system":
                messages.append(identity_system_prompt)
            messages.extend(conversation_history)
        else:
            messages.append(identity_system_prompt)

        # Record user message
        user_msg = {"role": "user", "content": prompt}
        messages.append(user_msg)
        _save_message(conversation_id, "user", prompt)

        tools_schema = agent_tools.get_tools_schema()

        # --- Main Cognitive Loop ---
        for step_idx in range(cfg.max_steps):
            state = StepState(step_index=step_idx)
            step_states.append(state)
            telemetry.steps_taken = step_idx + 1

            # Check history inflation
            compressed = _maybe_compress_history(messages, cfg, client, cfg.model_name)
            if compressed:
                telemetry.compression_events += 1
                state.history_compressed = True
                _save_message(conversation_id, "system", "[HISTORY COMPRESSED EVENT]")

            current_app.logger.info("[Maestro] Step %d/%d", step_idx + 1, cfg.max_steps)

            # Sanitize before API call
            _sanitize_messages_for_api(messages)
            api_messages = messages

            # LLM Decision
            llm_response = client.chat.completions.create(
                model=cfg.model_name,
                messages=api_messages,
                tools=tools_schema,
                tool_choice="auto"
            )

            raw_response_message = llm_response.choices[0].message
            tool_calls = getattr(raw_response_message, "tool_calls", None) or []

            # Normalize assistant message FIRST (even when tool calls present)
            assistant_dict = _normalize_assistant_message(raw_response_message)
            messages.append(assistant_dict)
            _save_message(conversation_id, "assistant", assistant_dict)

            # TOOL PHASE
            if tool_calls:
                state.decision = "tool"
                new_tool_names = []
                for call in tool_calls:
                    t_name = call.function.name
                    try:
                        args = json.loads(call.function.arguments) if call.function.arguments else {}
                    except Exception:
                        args = {}
                    new_tool_names.append(t_name)

                    # Repetition guard
                    tool_usage_sequence.append(t_name)
                    recent_slice = tool_usage_sequence[-cfg.max_repeated_tool:]
                    if len(recent_slice) == cfg.max_repeated_tool and all(n == t_name for n in recent_slice):
                        telemetry.repeated_tool_blocks += 1
                        warning_content = {
                            "warning": f"Tool '{t_name}' blocked due to excessive repetition.",
                            "policy": "max_repeated_tool"
                        }
                        messages.append({
                            "role": "tool",
                            "name": t_name,
                            "tool_call_id": call.id,
                            "content": _serialize_safe(warning_content)
                        })
                        _save_message(conversation_id, "tool", warning_content, tool_name=t_name, tool_ok=False)
                        continue

                    tool_result = _invoke_tool(t_name, args)
                    telemetry.tools_invoked += 1
                    telemetry.distinct_tools = len(set(tool_usage_sequence))
                    state.tool_calls.append({
                        "name": t_name,
                        "ok": tool_result.ok,
                        "args": args,
                        "meta": tool_result.meta
                    })

                    tool_payload = tool_result.to_dict() if hasattr(tool_result, "to_dict") else {
                        "raw": _serialize_safe(tool_result)
                    }
                    messages.append({
                        "role": "tool",
                        "name": t_name,
                        "tool_call_id": call.id,
                        "content": _serialize_safe(tool_payload)
                    })
                    _save_message(conversation_id, "tool", tool_payload, tool_name=t_name, tool_ok=tool_result.ok)

                # Progress detection
                if _detect_no_progress(previous_tool_names_snapshot, new_tool_names):
                    consecutive_no_progress += 1
                    state.stagnation_flag = True
                else:
                    consecutive_no_progress = 0
                previous_tool_names_snapshot = new_tool_names

                if consecutive_no_progress >= cfg.max_consecutive_no_progress:
                    telemetry.finalization_reason = "stagnation_detected"
                    state.notes.append("Terminated due to stagnation (no tool progress).")
                    state.finish()
                    break

                state.finish()
                continue  # next reasoning step

            # NO TOOL BRANCH → Final answer
            state.decision = "final"
            final_answer = assistant_dict.get("content") or "(no content)"
            telemetry.finalization_reason = "model_concluded"
            _save_message(conversation_id, "assistant", final_answer)
            state.finish()
            break

        else:
            # Loop exhausted without conclusion
            telemetry.finalization_reason = "max_steps_exhausted"

        # Commit all persisted messages
        if conversation_id and pending_db_commit:
            db.session.commit()

        # Compose final response object
        if telemetry.finalization_reason == "model_concluded":
            sources = ["reasoning"]
            if telemetry.tools_invoked > 0:
                sources.append("tooling")
            result = {
                "status": "success",
                "type": "synthesized_response",
                "answer": final_answer,
                "telemetry": telemetry.to_dict(),
                "steps": [asdict(s) for s in step_states],
                "version": __version__,
                "sources": sources
            }
        elif telemetry.finalization_reason == "stagnation_detected":
            result = {
                "status": "partial",
                "message": "Stopped due to stagnation (repetitive tool usage without progress).",
                "telemetry": telemetry.to_dict(),
                "steps": [asdict(s) for s in step_states],
                "version": __version__
            }
        elif telemetry.finalization_reason == "max_steps_exhausted":
            result = {
                "status": "error",
                "message": f"Agent exceeded maximum thinking steps ({cfg.max_steps}).",
                "telemetry": telemetry.to_dict(),
                "steps": [asdict(s) for s in step_states],
                "version": __version__
            }
        else:
            # Unexpected path but no exception
            result = {
                "status": "error",
                "message": "Unknown termination condition.",
                "telemetry": telemetry.to_dict(),
                "steps": [asdict(s) for s in step_states],
                "version": __version__
            }

        return result

    except Exception as e:
        telemetry.error = f"{type(e).__name__}: {e}"
        current_app.logger.error("[Maestro] Catastrophic failure: %s", e, exc_info=True)
        if conversation_id:
            db.session.rollback()
        return {
            "status": "error",
            "message": f"Catastrophic orchestration failure: {e}",
            "trace": traceback.format_exc(),
            "telemetry": telemetry.to_dict(),
            "version": __version__
        }