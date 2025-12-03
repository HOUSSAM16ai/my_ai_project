"""
SUPERHUMAN TESTS FOR TASK EXECUTION HELPERS
============================================
اختبارات خارقة فائقة الدقة لضمان الجودة الخيالية

These tests ensure every component works with MYTHICAL precision.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.task_execution_helpers import (
    MessageBuilder,
    StagnationDetector,
    TaskExecutionContext,
    TaskFinalizer,
    TaskInitializer,
    ToolCallHandler,
    UsageTracker,
)
from app.services.fastapi_generation_service import (
    OrchestratorConfig,
    OrchestratorTelemetry,
    StepState,
)


class TestTaskInitializer:
    """Test TaskInitializer with EXTREME precision."""

    def test_initialize_context_basic(self, monkeypatch):
        """✅ Test basic context initialization."""
        monkeypatch.delenv("MAESTRO_TOOL_CALL_LIMIT", raising=False)
        
        task = SimpleNamespace(mission=SimpleNamespace(id=1))
        config_dict = {
            "model_name": "gpt-4",
            "max_steps": 10,
            "emit_events": True,
            "stagnation_fail": False,
            "hotspot_hint_enabled": True,
            "repeat_threshold": 5,
            "repeat_abort": True,
        }

        ctx = TaskInitializer.initialize_context(task, "gpt-4", config_dict)

        assert ctx.task is task
        assert ctx.mission is task.mission
        assert ctx.cfg.model_name == "gpt-4"
        assert ctx.cfg.max_steps == 10
        assert ctx.emit_events is True
        assert ctx.stagnation_fail is False
        assert ctx.hotspot_hint_enabled is True
        assert ctx.repeat_threshold == 5
        assert ctx.repeat_abort is True
        assert ctx.tool_call_limit is None
        assert isinstance(ctx.steps, list)
        assert len(ctx.steps) == 0
        assert isinstance(ctx.cumulative_usage, dict)
        assert len(ctx.cumulative_usage) == 0

    def test_initialize_context_with_tool_limit(self, monkeypatch):
        """✅ Test context initialization with tool call limit."""
        monkeypatch.setenv("MAESTRO_TOOL_CALL_LIMIT", "50")
        
        task = SimpleNamespace(mission=SimpleNamespace(id=1))
        config_dict = {"model_name": "gpt-4", "max_steps": 5}

        ctx = TaskInitializer.initialize_context(task, None, config_dict)

        assert ctx.tool_call_limit == 50

    def test_initialize_context_invalid_tool_limit(self, monkeypatch):
        """✅ Test context initialization with invalid tool limit."""
        monkeypatch.setenv("MAESTRO_TOOL_CALL_LIMIT", "invalid")
        
        task = SimpleNamespace(mission=SimpleNamespace(id=1))
        config_dict = {"model_name": "gpt-4", "max_steps": 5}

        ctx = TaskInitializer.initialize_context(task, None, config_dict)

        # Should gracefully handle invalid value
        assert ctx.tool_call_limit is None

    def test_initialize_context_no_mission(self):
        """✅ Test context initialization when task has no mission."""
        task = SimpleNamespace()  # No mission attribute
        config_dict = {"model_name": "gpt-4", "max_steps": 5}

        ctx = TaskInitializer.initialize_context(task, None, config_dict)

        assert ctx.task is task
        assert ctx.mission is None


class TestToolCallHandler:
    """Test ToolCallHandler with SURGICAL precision."""

    def test_should_abort_on_limit_no_limit_set(self):
        """✅ Test abort check when no limit is set."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(),
            tool_call_limit=None,
        )
        handler = ToolCallHandler(ctx)

        assert handler.should_abort_on_limit() is False

    def test_should_abort_on_limit_not_reached(self):
        """✅ Test abort check when limit not reached."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(tools_invoked=5),
            tool_call_limit=10,
        )
        handler = ToolCallHandler(ctx)

        assert handler.should_abort_on_limit() is False

    def test_should_abort_on_limit_reached(self):
        """✅ Test abort check when limit is exceeded."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(tools_invoked=15),
            tool_call_limit=10,
        )
        handler = ToolCallHandler(ctx)

        assert handler.should_abort_on_limit() is True

    def test_check_repeat_pattern_first_call(self):
        """✅ Test repeat pattern check on first call."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(),
            repeat_threshold=3,
            repeat_abort=True,
        )
        handler = ToolCallHandler(ctx)

        should_abort = handler.check_repeat_pattern("read_file", {"path": "/test.txt"})

        assert should_abort is False
        assert ctx.repeat_counter["read_file:{\"path\": \"/test.txt\"}"] == 1
        assert len(ctx.tool_repeat_warnings) == 0

    def test_check_repeat_pattern_threshold_reached(self):
        """✅ Test repeat pattern when threshold is reached."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(),
            repeat_threshold=3,
            repeat_abort=True,
        )
        handler = ToolCallHandler(ctx)

        # Call same tool 3 times
        handler.check_repeat_pattern("read_file", {"path": "/test.txt"})
        handler.check_repeat_pattern("read_file", {"path": "/test.txt"})
        should_abort = handler.check_repeat_pattern("read_file", {"path": "/test.txt"})

        assert should_abort is True
        assert ctx.telemetry.repeat_pattern_triggered is True
        assert len(ctx.tool_repeat_warnings) == 1
        assert "repeat_pattern_threshold:read_file:3" in ctx.tool_repeat_warnings[0]

    def test_check_repeat_pattern_threshold_no_abort(self):
        """✅ Test repeat pattern when abort is disabled."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(),
            repeat_threshold=2,
            repeat_abort=False,  # Abort disabled
        )
        handler = ToolCallHandler(ctx)

        handler.check_repeat_pattern("write_file", {"path": "/test.txt", "content": "data"})
        should_abort = handler.check_repeat_pattern("write_file", {"path": "/test.txt", "content": "data"})

        assert should_abort is False
        assert ctx.telemetry.repeat_pattern_triggered is True

    def test_tool_signature_generation(self):
        """✅ Test tool signature generation for repeat detection."""
        sig = ToolCallHandler._tool_signature("read_file", {"path": "/test.txt", "lines": [1, 10]})
        
        # Should create consistent signature
        assert "read_file" in sig
        # Order should be consistent due to sort_keys=True
        sig2 = ToolCallHandler._tool_signature("read_file", {"lines": [1, 10], "path": "/test.txt"})
        assert sig == sig2


class TestStagnationDetector:
    """Test StagnationDetector with LEGENDARY accuracy."""

    def test_no_stagnation_empty_lists(self):
        """✅ Test no stagnation with empty tool lists."""
        assert StagnationDetector.is_stagnation([], []) is False

    def test_no_stagnation_first_call(self):
        """✅ Test no stagnation on first tool call."""
        assert StagnationDetector.is_stagnation([], ["read_file"]) is False

    def test_no_stagnation_different_tools(self):
        """✅ Test no stagnation with different tools."""
        previous = ["read_file", "write_file"]
        current = ["list_directory", "search_code"]
        
        assert StagnationDetector.is_stagnation(previous, current) is False

    def test_no_stagnation_different_length(self):
        """✅ Test no stagnation with different list lengths."""
        previous = ["read_file"]
        current = ["read_file", "write_file"]
        
        assert StagnationDetector.is_stagnation(previous, current) is False

    def test_stagnation_detected(self):
        """✅ Test stagnation detection with identical tool lists."""
        previous = ["read_file", "write_file", "read_file"]
        current = ["read_file", "write_file", "read_file"]
        
        assert StagnationDetector.is_stagnation(previous, current) is True

    def test_stagnation_single_tool(self):
        """✅ Test stagnation with single repeated tool."""
        previous = ["read_file"]
        current = ["read_file"]
        
        assert StagnationDetector.is_stagnation(previous, current) is True


class TestTaskFinalizer:
    """Test TaskFinalizer with DIVINE precision."""

    def test_build_result_basic(self):
        """✅ Test basic result building."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(steps_taken=3, tools_invoked=5),
            final_answer="Task completed successfully",
        )
        ctx.cumulative_usage = {"total_tokens": 300, "prompt_tokens": 100, "completion_tokens": 200}
        ctx.tools_used = ["read_file", "write_file", "read_file"]

        result = TaskFinalizer.build_result(ctx)

        assert "telemetry" in result
        assert result["telemetry"]["steps_taken"] == 3
        assert result["telemetry"]["tools_invoked"] == 5
        assert "steps" in result
        assert result["tools_used"] == ["read_file", "write_file", "read_file"]
        assert result["usage"] == ctx.cumulative_usage
        assert result["usage_rate_tokens_per_step"] == 100.0  # 300 / 3

    def test_build_result_with_error(self):
        """✅ Test result building with error."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(
                steps_taken=2,
                error="Connection timeout",
                finalization_reason="exception",
            ),
        )

        result = TaskFinalizer.build_result(ctx)

        assert "error" in result
        assert result["error"] == "Connection timeout"
        assert result["final_reason"] == "exception"

    def test_build_result_no_steps(self):
        """✅ Test result building with no steps taken."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(steps_taken=0),
        )
        ctx.cumulative_usage = {"total_tokens": 100}

        result = TaskFinalizer.build_result(ctx)

        # Should handle division by zero gracefully
        assert result["usage_rate_tokens_per_step"] is None or result["usage_rate_tokens_per_step"] == 100.0

    def test_determine_final_status_success(self):
        """✅ Test status determination for successful task."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(steps_taken=3),
            stagnation_fail=False,
            repeat_abort=False,
        )

        status = TaskFinalizer.determine_final_status(ctx)

        assert status == "SUCCESS"

    def test_determine_final_status_stagnation_fail(self):
        """✅ Test status determination with stagnation failure."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(stagnation=True),
            stagnation_fail=True,
        )

        status = TaskFinalizer.determine_final_status(ctx)

        assert status == "FAILED"

    def test_determine_final_status_tool_limit_hit(self):
        """✅ Test status determination when tool limit exceeded."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(tool_call_limit_hit=True),
        )

        status = TaskFinalizer.determine_final_status(ctx)

        assert status == "FAILED"

    def test_determine_final_status_repeat_abort(self):
        """✅ Test status determination with repeat pattern abort."""
        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(repeat_pattern_triggered=True),
            repeat_abort=True,
        )

        status = TaskFinalizer.determine_final_status(ctx)

        assert status == "FAILED"


class TestMessageBuilder:
    """Test MessageBuilder with COSMIC precision."""

    def test_build_initial_messages(self):
        """✅ Test building initial message list."""
        task = SimpleNamespace(description="Create a new feature")
        system_prompt = "You are an expert developer."

        messages = MessageBuilder.build_initial_messages(task, system_prompt)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == system_prompt
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Create a new feature"

    def test_normalize_assistant_message_text_only(self):
        """✅ Test normalizing assistant message with only text."""
        raw_msg = SimpleNamespace(content="Here is my response")

        msg = MessageBuilder.normalize_assistant_message(raw_msg)

        assert msg["role"] == "assistant"
        assert msg["content"] == "Here is my response"
        assert "tool_calls" not in msg

    def test_normalize_assistant_message_with_tools(self):
        """✅ Test normalizing assistant message with tool calls."""
        tool_call = SimpleNamespace(
            id="call_123",
            type="function",
            function=SimpleNamespace(name="read_file", arguments='{"path": "/test.txt"}'),
        )
        raw_msg = SimpleNamespace(content="Let me read the file", tool_calls=[tool_call])

        msg = MessageBuilder.normalize_assistant_message(raw_msg)

        assert msg["role"] == "assistant"
        assert msg["content"] == "Let me read the file"
        assert "tool_calls" in msg
        assert len(msg["tool_calls"]) == 1
        assert msg["tool_calls"][0]["id"] == "call_123"
        assert msg["tool_calls"][0]["function"]["name"] == "read_file"
        assert msg["tool_calls"][0]["function"]["arguments"] == '{"path": "/test.txt"}'

    def test_normalize_assistant_message_empty(self):
        """✅ Test normalizing empty assistant message."""
        raw_msg = SimpleNamespace()

        msg = MessageBuilder.normalize_assistant_message(raw_msg)

        assert msg["role"] == "assistant"
        assert "content" not in msg
        assert "tool_calls" not in msg


class TestUsageTracker:
    """Test UsageTracker with MYTHICAL precision."""

    def test_extract_usage_complete(self):
        """✅ Test extracting complete usage information."""
        llm_response = SimpleNamespace(
            usage=SimpleNamespace(
                prompt_tokens=100,
                completion_tokens=200,
                total_tokens=300,
            )
        )

        usage = UsageTracker.extract_usage(llm_response)

        assert usage["prompt_tokens"] == 100
        assert usage["completion_tokens"] == 200
        assert usage["total_tokens"] == 300

    def test_extract_usage_partial(self):
        """✅ Test extracting partial usage information."""
        llm_response = SimpleNamespace(
            usage=SimpleNamespace(
                total_tokens=300,
            )
        )

        usage = UsageTracker.extract_usage(llm_response)

        assert usage["total_tokens"] == 300
        assert "prompt_tokens" not in usage
        assert "completion_tokens" not in usage

    def test_extract_usage_no_usage(self):
        """✅ Test extracting usage when not available."""
        llm_response = SimpleNamespace()

        usage = UsageTracker.extract_usage(llm_response)

        assert usage == {}

    def test_accumulate_usage_first_call(self):
        """✅ Test accumulating usage on first call."""
        cumulative = {}
        new_usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}

        UsageTracker.accumulate_usage(cumulative, new_usage)

        assert cumulative["prompt_tokens"] == 100
        assert cumulative["completion_tokens"] == 50
        assert cumulative["total_tokens"] == 150

    def test_accumulate_usage_multiple_calls(self):
        """✅ Test accumulating usage across multiple calls."""
        cumulative = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        new_usage = {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300}

        UsageTracker.accumulate_usage(cumulative, new_usage)

        assert cumulative["prompt_tokens"] == 300
        assert cumulative["completion_tokens"] == 150
        assert cumulative["total_tokens"] == 450

    def test_accumulate_usage_ignores_non_int(self):
        """✅ Test accumulation ignores non-integer values."""
        cumulative = {"prompt_tokens": 100}
        new_usage = {"prompt_tokens": 50, "metadata": "some_string"}

        UsageTracker.accumulate_usage(cumulative, new_usage)

        assert cumulative["prompt_tokens"] == 150
        assert "metadata" not in cumulative


# ==================== INTEGRATION TESTS ====================


class TestIntegration:
    """SUPERHUMAN integration tests for complete workflow."""

    def test_complete_task_execution_flow(self, monkeypatch):
        """✅ Test complete task execution flow with all components."""
        monkeypatch.delenv("MAESTRO_TOOL_CALL_LIMIT", raising=False)
        
        # Initialize task
        task = SimpleNamespace(
            id=1,
            mission=SimpleNamespace(id=10),
            description="Test task",
        )
        config_dict = {
            "model_name": "gpt-4",
            "max_steps": 5,
            "emit_events": False,
            "stagnation_fail": True,
            "repeat_threshold": 3,
            "repeat_abort": False,
        }

        # Step 1: Initialize context
        ctx = TaskInitializer.initialize_context(task, "gpt-4", config_dict)
        assert ctx.task is task
        assert ctx.cfg.model_name == "gpt-4"

        # Step 2: Simulate tool calls
        handler = ToolCallHandler(ctx)
        
        # First tool call
        should_abort = handler.check_repeat_pattern("read_file", {"path": "/test.txt"})
        assert should_abort is False
        ctx.telemetry.tools_invoked += 1
        ctx.tools_used.append("read_file")

        # Second tool call (different tool)
        should_abort = handler.check_repeat_pattern("write_file", {"path": "/output.txt"})
        assert should_abort is False
        ctx.telemetry.tools_invoked += 1
        ctx.tools_used.append("write_file")

        # Step 3: Track usage
        llm_response = SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        )
        usage = UsageTracker.extract_usage(llm_response)
        UsageTracker.accumulate_usage(ctx.cumulative_usage, usage)
        
        assert ctx.cumulative_usage["total_tokens"] == 150

        # Step 4: Add steps
        ctx.steps.append(StepState(step_index=0))
        ctx.steps.append(StepState(step_index=1))
        ctx.telemetry.steps_taken = 2

        # Step 5: Build final result
        ctx.telemetry.finalization_reason = "model_concluded"
        result = TaskFinalizer.build_result(ctx)

        assert result["telemetry"]["steps_taken"] == 2
        assert result["telemetry"]["tools_invoked"] == 2
        assert result["tools_used"] == ["read_file", "write_file"]
        assert result["usage"]["total_tokens"] == 150
        assert result["usage_rate_tokens_per_step"] == 75.0

        # Step 6: Determine status
        status = TaskFinalizer.determine_final_status(ctx)
        assert status == "SUCCESS"


# ==================== EDGE CASE TESTS ====================


class TestEdgeCases:
    """Tests for edge cases with EXTREME thoroughness."""

    def test_tool_signature_with_complex_args(self):
        """✅ Test tool signature with complex nested arguments."""
        args = {
            "path": "/test.txt",
            "options": {"recursive": True, "max_depth": 5},
            "filters": ["*.py", "*.js"],
        }
        
        sig = ToolCallHandler._tool_signature("search_files", args)
        
        # Should handle complex args without errors
        assert "search_files" in sig
        assert isinstance(sig, str)

    def test_tool_signature_with_unparseable_args(self):
        """✅ Test tool signature with unparseable arguments."""
        # Create an object that can't be JSON serialized
        class UnserializableObject:
            pass
        
        args = {"obj": UnserializableObject()}
        
        sig = ToolCallHandler._tool_signature("test_tool", args)
        
        # Should fallback to tool name only
        assert sig == "test_tool"

    def test_message_builder_with_missing_attributes(self):
        """✅ Test message builder with incomplete raw message."""
        # Raw message with missing attributes
        raw_msg = SimpleNamespace()
        
        msg = MessageBuilder.normalize_assistant_message(raw_msg)
        
        # Should handle gracefully
        assert msg["role"] == "assistant"
        assert len(msg) == 1  # Only role field

    def test_usage_tracker_with_string_values(self):
        """✅ Test usage tracker ignores string values."""
        cumulative = {"prompt_tokens": 100}
        new_usage = {
            "prompt_tokens": 50,
            "model": "gpt-4",  # String value
            "completion_tokens": "not_a_number",  # String instead of int
        }
        
        UsageTracker.accumulate_usage(cumulative, new_usage)
        
        # Should only accumulate valid integers
        assert cumulative["prompt_tokens"] == 150
        assert "model" not in cumulative
        assert "completion_tokens" not in cumulative


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
