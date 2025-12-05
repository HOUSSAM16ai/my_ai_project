# app/services/task_execution_helpers.py
"""
Helper classes and functions for task execution refactoring.
تقليل التعقيد عبر تقسيم منطق execute_task إلى وحدات منفصلة.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from app.services.fastapi_generation_service import (
    OrchestratorConfig,
    OrchestratorTelemetry,
    StepState,
)


@dataclass
class TaskExecutionContext:
    """Context object to hold task execution state."""

    task: Any
    mission: Any
    cfg: OrchestratorConfig
    telemetry: OrchestratorTelemetry
    steps: list[StepState] = field(default_factory=list)
    cumulative_usage: dict[str, int] = field(default_factory=dict)
    tools_used: list[str] = field(default_factory=list)
    tool_repeat_warnings: list[str] = field(default_factory=list)
    previous_tools: list[str] = field(default_factory=list)
    final_answer: str = "(no answer produced)"
    repeat_counter: dict[str, int] = field(default_factory=dict)
    emit_events: bool = False
    stagnation_fail: bool = False
    hotspot_hint_enabled: bool = True
    repeat_threshold: int = 3
    repeat_abort: bool = False
    tool_call_limit: int | None = None


class TaskInitializer:
    """Handles task initialization and configuration."""

    @staticmethod
    def initialize_context(
        task: Any, model: str | None, config_dict: dict[str, Any]
    ) -> TaskExecutionContext:
        """Initialize task execution context with all required settings."""
        from app.services.fastapi_generation_service import (
            OrchestratorConfig,
            OrchestratorTelemetry,
        )

        cfg = OrchestratorConfig(
            model_name=config_dict.get("model_name", "default"),
            max_steps=config_dict.get("max_steps", 5),
        )

        telemetry = OrchestratorTelemetry()

        ctx = TaskExecutionContext(
            task=task,
            mission=task.mission if hasattr(task, "mission") else None,
            cfg=cfg,
            telemetry=telemetry,
            emit_events=config_dict.get("emit_events", False),
            stagnation_fail=config_dict.get("stagnation_fail", False),
            hotspot_hint_enabled=config_dict.get("hotspot_hint_enabled", True),
            repeat_threshold=config_dict.get("repeat_threshold", 3),
            repeat_abort=config_dict.get("repeat_abort", False),
        )

        # Parse tool_call_limit safely
        try:
            raw_limit = os.getenv("MAESTRO_TOOL_CALL_LIMIT")
            if raw_limit:
                ctx.tool_call_limit = int(raw_limit)
        except Exception:
            ctx.tool_call_limit = None

        return ctx


class ToolCallHandler:
    """Handles tool call execution and validation."""

    def __init__(self, context: TaskExecutionContext):
        self.ctx = context

    def should_abort_on_limit(self) -> bool:
        """Check if tool call limit has been reached."""
        if self.ctx.tool_call_limit is None:
            return False
        return self.ctx.telemetry.tools_invoked > self.ctx.tool_call_limit

    def check_repeat_pattern(self, canonical: str, fn_args: dict[str, Any]) -> bool:
        """
        Check if tool is being repeated excessively.
        Returns True if should abort execution.
        """
        sig = self._tool_signature(canonical, fn_args)
        self.ctx.repeat_counter[sig] = self.ctx.repeat_counter.get(sig, 0) + 1

        if self.ctx.repeat_counter[sig] == self.ctx.repeat_threshold:
            msg = f"repeat_pattern_threshold:{canonical}:{self.ctx.repeat_threshold}"
            self.ctx.tool_repeat_warnings.append(msg)
            self.ctx.telemetry.repeat_pattern_triggered = True
            return self.ctx.repeat_abort

        return False

    @staticmethod
    def _tool_signature(tool_name: str, args: dict[str, Any]) -> str:
        """Generate signature for tool call to detect repeats."""
        try:
            args_json = json.dumps(args, sort_keys=True)
            return f"{tool_name}:{args_json}"
        except Exception:
            return tool_name


class StagnationDetector:
    """Detects stagnation patterns in tool usage."""

    @staticmethod
    def is_stagnation(previous_tools: list[str], current_tools: list[str]) -> bool:
        """
        Detect if agent is stuck in a loop.
        Returns True if same tools are being called repeatedly.
        """
        if not previous_tools or not current_tools:
            return False
        if len(previous_tools) != len(current_tools):
            return False
        return previous_tools == current_tools


class TaskFinalizer:
    """Handles task completion and result formatting."""

    @staticmethod
    def build_result(context: TaskExecutionContext) -> dict[str, Any]:
        """Build final task result dictionary."""
        from dataclasses import asdict

        usage_rate_tokens_per_step = None
        total_tokens = context.cumulative_usage.get("total_tokens")
        if total_tokens and context.telemetry.steps_taken:
            usage_rate_tokens_per_step = round(
                total_tokens / max(1, context.telemetry.steps_taken), 2
            )

        result = {
            "telemetry": context.telemetry.to_dict(),
            "steps": [asdict(s) for s in context.steps],
            "tools_used": context.tools_used,
            "usage": context.cumulative_usage,
            "usage_rate_tokens_per_step": usage_rate_tokens_per_step,
            "final_reason": context.telemetry.finalization_reason,
            "repeat_pattern_triggered": context.telemetry.repeat_pattern_triggered,
            "hotspot_hint_used": context.telemetry.hotspot_hint_used,
            "tool_repeat_warnings": context.tool_repeat_warnings,
        }

        if context.telemetry.error:
            result["error"] = context.telemetry.error

        return result

    @staticmethod
    def determine_final_status(context: TaskExecutionContext) -> str:
        """Determine final task status based on telemetry."""
        from app.models import TaskStatus

        if context.telemetry.stagnation and context.stagnation_fail:
            return TaskStatus.FAILED
        if context.telemetry.tool_call_limit_hit:
            return TaskStatus.FAILED
        if context.telemetry.repeat_pattern_triggered and context.repeat_abort:
            return TaskStatus.FAILED

        return TaskStatus.SUCCESS


class MessageBuilder:
    """Builds messages for LLM conversation."""

    @staticmethod
    def build_initial_messages(task: Any, system_prompt: str) -> list[dict[str, Any]]:
        """Build initial message list for conversation."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": getattr(task, "description", "")},
        ]

    @staticmethod
    def normalize_assistant_message(raw_msg: Any) -> dict[str, Any]:
        """Normalize assistant message from LLM response."""
        msg = {"role": "assistant"}

        if hasattr(raw_msg, "content") and raw_msg.content:
            msg["content"] = raw_msg.content

        if hasattr(raw_msg, "tool_calls") and raw_msg.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": getattr(tc, "id", ""),
                    "type": getattr(tc, "type", "function"),
                    "function": {
                        "name": getattr(tc.function, "name", "") if hasattr(tc, "function") else "",
                        "arguments": getattr(tc.function, "arguments", "")
                        if hasattr(tc, "function")
                        else "",
                    },
                }
                for tc in raw_msg.tool_calls
            ]

        return msg


class UsageTracker:
    """Tracks token usage across steps."""

    @staticmethod
    def extract_usage(llm_response: Any) -> dict[str, int]:
        """Extract usage information from LLM response."""
        usage = {}
        if hasattr(llm_response, "usage"):
            usage_obj = llm_response.usage
            if hasattr(usage_obj, "prompt_tokens"):
                usage["prompt_tokens"] = usage_obj.prompt_tokens
            if hasattr(usage_obj, "completion_tokens"):
                usage["completion_tokens"] = usage_obj.completion_tokens
            if hasattr(usage_obj, "total_tokens"):
                usage["total_tokens"] = usage_obj.total_tokens
        return usage

    @staticmethod
    def accumulate_usage(cumulative: dict[str, int], new_usage: dict[str, int]) -> None:
        """Accumulate usage statistics."""
        for k, v in new_usage.items():
            if isinstance(v, int):
                cumulative[k] = cumulative.get(k, 0) + v
