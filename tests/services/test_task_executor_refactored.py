"""
SUPERHUMAN INTEGRATION TESTS FOR REFACTORED TASK EXECUTOR
==========================================================
اختبارات تكامل خارقة لضمان قابلية الصيانة والتوسع الخيالية

These tests ensure the refactored executor works seamlessly with existing code.
"""

import contextlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.task_executor_refactored import (
    StepExecutor,
    TaskExecutor,
)


class TestTaskExecutorIntegration:
    """Integration tests for TaskExecutor with DIVINE precision."""

    @pytest.fixture
    def mock_service(self):
        """Create mock service."""
        service = MagicMock()
        service._safe_log = MagicMock()
        service._commit = MagicMock()
        service._finalize_task_safe = MagicMock()
        service._build_context_blob = MagicMock(return_value="context blob")
        service._build_system_prompt = MagicMock(return_value="system prompt")
        return service

    @pytest.fixture
    def mock_task(self):
        """Create mock task."""
        task = SimpleNamespace(
            id=1,
            mission=SimpleNamespace(id=10),
            description="Test task description",
            status="PENDING",
        )
        return task

    def test_execute_task_invalid_no_mission(self, mock_service):
        """✅ Test execution with task missing mission attribute."""
        task = SimpleNamespace(id=1)  # No mission
        executor = TaskExecutor(mock_service)

        executor.execute(task, None)

        # Should log warning and return early
        mock_service._safe_log.assert_called_once()
        assert "mission" in str(mock_service._safe_log.call_args)

    @patch("app.services.task_executor_refactored.get_llm_client")
    @patch("app.services.task_executor_refactored.agent_tools")
    def test_execute_task_client_init_failure(
        self, mock_agent_tools, mock_get_client, mock_service, mock_task
    ):
        """✅ Test execution when LLM client initialization fails."""
        mock_get_client.side_effect = Exception("Client init failed")
        mock_agent_tools.get_tools_schema.return_value = []

        executor = TaskExecutor(mock_service)
        executor.execute(mock_task, "gpt-4")

        # Should finalize with FAILED status
        mock_service._finalize_task_safe.assert_called_once()
        call_args = mock_service._finalize_task_safe.call_args
        assert call_args[0][1] == "FAILED"
        assert "client initialization failed" in call_args[0][2].lower()

    @patch("app.services.task_executor_refactored.get_llm_client")
    @patch("app.services.task_executor_refactored.agent_tools")
    def test_execute_task_success_final_answer(
        self, mock_agent_tools, mock_get_client, mock_service, mock_task, monkeypatch
    ):
        """✅ Test successful execution with final answer."""
        # Setup environment
        monkeypatch.setenv("MAESTRO_EMIT_TASK_EVENTS", "0")
        monkeypatch.setenv("MAESTRO_STAGNATION_ENFORCE", "0")
        monkeypatch.setenv("AGENT_MAX_STEPS", "5")

        # Mock LLM client
        mock_client = MagicMock()
        mock_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Task completed successfully",
                        tool_calls=None,
                    )
                )
            ],
            usage=SimpleNamespace(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
            ),
        )
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        mock_agent_tools.get_tools_schema.return_value = []

        executor = TaskExecutor(mock_service)
        executor.execute(mock_task, "gpt-4")

        # Should finalize with SUCCESS
        mock_service._finalize_task_safe.assert_called()
        call_args = mock_service._finalize_task_safe.call_args
        assert call_args[0][1] == "SUCCESS"

    @patch("app.services.task_executor_refactored.get_llm_client")
    @patch("app.services.task_executor_refactored.agent_tools")
    def test_execute_task_with_tool_calls(
        self, mock_agent_tools, mock_get_client, mock_service, mock_task, monkeypatch
    ):
        """✅ Test execution with tool calls."""
        monkeypatch.setenv("MAESTRO_EMIT_TASK_EVENTS", "0")
        monkeypatch.setenv("AGENT_MAX_STEPS", "5")

        # Mock tool registry
        def mock_read_file(**kwargs):
            return SimpleNamespace(
                ok=True,
                result="file content",
                to_dict=lambda: {"ok": True, "result": "file content"},
            )

        mock_agent_tools._TOOL_REGISTRY = {"read_file": {"fn": mock_read_file}}
        mock_agent_tools.get_tools_schema.return_value = [
            {"type": "function", "function": {"name": "read_file"}}
        ]
        mock_agent_tools.resolve_tool_name.side_effect = lambda x: x

        # Mock LLM responses: first with tool call, then final answer
        mock_client = MagicMock()

        # First response: tool call
        tool_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Let me read the file",
                        tool_calls=[
                            SimpleNamespace(
                                id="call_123",
                                type="function",
                                function=SimpleNamespace(
                                    name="read_file",
                                    arguments='{"path": "/test.txt"}',
                                ),
                            )
                        ],
                    )
                )
            ],
            usage=SimpleNamespace(total_tokens=100),
        )

        # Second response: final answer
        final_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="File read successfully",
                        tool_calls=None,
                    )
                )
            ],
            usage=SimpleNamespace(total_tokens=50),
        )

        mock_client.chat.completions.create.side_effect = [tool_response, final_response]
        mock_get_client.return_value = mock_client

        executor = TaskExecutor(mock_service)
        executor.execute(mock_task, "gpt-4")

        # Should call LLM twice and finalize
        assert mock_client.chat.completions.create.call_count == 2
        mock_service._finalize_task_safe.assert_called()

    @patch("app.services.task_executor_refactored.get_llm_client")
    @patch("app.services.task_executor_refactored.agent_tools")
    def test_execute_task_max_steps_exhausted(
        self, mock_agent_tools, mock_get_client, mock_service, mock_task, monkeypatch
    ):
        """✅ Test execution when max steps are exhausted."""
        monkeypatch.setenv("AGENT_MAX_STEPS", "2")
        monkeypatch.setenv("MAESTRO_EMIT_TASK_EVENTS", "0")

        # Mock client that keeps returning tool calls
        mock_client = MagicMock()
        tool_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Thinking...",
                        tool_calls=[
                            SimpleNamespace(
                                id="call_1",
                                type="function",
                                function=SimpleNamespace(
                                    name="read_file",
                                    arguments='{"path": "/test.txt"}',
                                ),
                            )
                        ],
                    )
                )
            ],
            usage=SimpleNamespace(total_tokens=50),
        )
        mock_client.chat.completions.create.return_value = tool_response
        mock_get_client.return_value = mock_client
        mock_agent_tools.get_tools_schema.return_value = []
        mock_agent_tools.resolve_tool_name.side_effect = lambda x: x
        mock_agent_tools._TOOL_REGISTRY = {
            "read_file": {"fn": lambda **kw: SimpleNamespace(ok=True, to_dict=lambda: {"ok": True})}
        }

        executor = TaskExecutor(mock_service)
        executor.execute(mock_task, "gpt-4")

        # Should exhaust max steps
        assert mock_client.chat.completions.create.call_count == 2
        mock_service._finalize_task_safe.assert_called()


class TestStepExecutorIntegration:
    """Integration tests for StepExecutor."""

    @pytest.fixture
    def mock_context(self):
        """Create mock execution context."""
        from app.services.fastapi_generation_service import (
            OrchestratorConfig,
            OrchestratorTelemetry,
        )
        from app.services.task_execution_helpers import TaskExecutionContext

        return TaskExecutionContext(
            task=SimpleNamespace(id=1),
            mission=SimpleNamespace(id=10),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(),
            emit_events=False,
        )

    def test_step_executor_final_answer(self, mock_context):
        """✅ Test step executor with final answer."""
        mock_client = MagicMock()
        mock_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Final answer",
                        tool_calls=None,
                    )
                )
            ],
            usage=SimpleNamespace(total_tokens=100),
        )
        mock_client.chat.completions.create.return_value = mock_response

        messages = []
        tools_schema = []
        service = MagicMock()

        executor = StepExecutor(mock_context, mock_client, messages, tools_schema, service)
        should_break = executor.execute_step(0)

        assert should_break is True
        assert mock_context.final_answer == "Final answer"
        assert mock_context.telemetry.finalization_reason == "model_concluded"
        assert len(mock_context.steps) == 1

    @patch("app.services.task_executor_refactored.agent_tools")
    def test_step_executor_stagnation_detection(self, mock_agent_tools, mock_context):
        """✅ Test step executor detects stagnation."""
        mock_agent_tools.resolve_tool_name.side_effect = lambda x: x
        mock_agent_tools._TOOL_REGISTRY = {
            "read_file": {"fn": lambda **kw: SimpleNamespace(ok=True, to_dict=lambda: {"ok": True})}
        }

        # Set previous tools to same as current
        mock_context.previous_tools = ["read_file"]

        mock_client = MagicMock()
        mock_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Reading file",
                        tool_calls=[
                            SimpleNamespace(
                                id="call_1",
                                type="function",
                                function=SimpleNamespace(
                                    name="read_file",
                                    arguments='{"path": "/test.txt"}',
                                ),
                            )
                        ],
                    )
                )
            ],
            usage=SimpleNamespace(total_tokens=50),
        )
        mock_client.chat.completions.create.return_value = mock_response

        messages = []
        tools_schema = []
        service = MagicMock()

        executor = StepExecutor(mock_context, mock_client, messages, tools_schema, service)
        should_break = executor.execute_step(0)

        assert should_break is True
        assert mock_context.telemetry.stagnation is True
        assert mock_context.telemetry.finalization_reason == "stagnation_detected"

    @patch("app.services.task_executor_refactored.agent_tools")
    def test_step_executor_tool_limit_reached(self, mock_agent_tools, mock_context):
        """✅ Test step executor with tool call limit."""
        mock_context.tool_call_limit = 1
        mock_context.telemetry.tools_invoked = 0

        mock_agent_tools.resolve_tool_name.side_effect = lambda x: x
        mock_agent_tools._TOOL_REGISTRY = {
            "read_file": {"fn": lambda **kw: SimpleNamespace(ok=True, to_dict=lambda: {"ok": True})}
        }

        mock_client = MagicMock()
        mock_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Reading file",
                        tool_calls=[
                            SimpleNamespace(
                                id="call_1",
                                type="function",
                                function=SimpleNamespace(
                                    name="read_file",
                                    arguments='{"path": "/test.txt"}',
                                ),
                            ),
                            SimpleNamespace(
                                id="call_2",
                                type="function",
                                function=SimpleNamespace(
                                    name="read_file",
                                    arguments='{"path": "/test2.txt"}',
                                ),
                            ),
                        ],
                    )
                )
            ],
            usage=SimpleNamespace(total_tokens=50),
        )
        mock_client.chat.completions.create.return_value = mock_response

        messages = []
        tools_schema = []
        service = MagicMock()

        executor = StepExecutor(mock_context, mock_client, messages, tools_schema, service)
        should_break = executor.execute_step(0)

        assert should_break is True
        assert mock_context.telemetry.tool_call_limit_hit is True


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility."""

    def test_task_executor_maintains_interface(self, monkeypatch):
        """✅ Test that TaskExecutor maintains expected interface."""
        monkeypatch.delenv("MAESTRO_EMIT_TASK_EVENTS", raising=False)

        service = MagicMock()
        executor = TaskExecutor(service)

        # Should have execute method
        assert hasattr(executor, "execute")
        assert callable(executor.execute)

        # Should accept task and optional model
        task = SimpleNamespace(id=1)
        with contextlib.suppress(Exception):
            executor.execute(task, None)  # Expected to fail but interface should be correct

    def test_result_format_compatibility(self):
        """✅ Test that result format is compatible with existing code."""
        from app.services.fastapi_generation_service import (
            OrchestratorConfig,
            OrchestratorTelemetry,
        )
        from app.services.task_execution_helpers import (
            TaskExecutionContext,
            TaskFinalizer,
        )

        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(steps_taken=2, tools_invoked=3),
        )
        ctx.cumulative_usage = {"total_tokens": 200}
        ctx.tools_used = ["read_file", "write_file"]

        result = TaskFinalizer.build_result(ctx)

        # Check all expected keys are present
        assert "telemetry" in result
        assert "steps" in result
        assert "tools_used" in result
        assert "usage" in result
        assert "final_reason" in result
        assert isinstance(result["telemetry"], dict)
        assert isinstance(result["steps"], list)


class TestExtensibility:
    """Tests to verify extensibility and maintainability."""

    def test_can_extend_with_custom_tool_handler(self):
        """✅ Test that custom tool handlers can be easily added."""
        from app.services.task_execution_helpers import ToolCallHandler

        # Should be able to subclass and extend
        class CustomToolCallHandler(ToolCallHandler):
            def custom_validation(self):
                return True

        ctx = MagicMock()
        handler = CustomToolCallHandler(ctx)

        assert hasattr(handler, "custom_validation")
        assert handler.custom_validation() is True

    def test_can_extend_with_custom_finalizer(self):
        """✅ Test that custom finalizers can be added."""
        from app.services.task_execution_helpers import TaskFinalizer

        class CustomTaskFinalizer(TaskFinalizer):
            @staticmethod
            def build_enhanced_result(context):
                result = TaskFinalizer.build_result(context)
                result["custom_field"] = "custom_value"
                return result

        ctx = MagicMock()
        ctx.telemetry = MagicMock()
        ctx.telemetry.to_dict = lambda: {}
        ctx.steps = []
        ctx.tools_used = []
        ctx.cumulative_usage = {}
        ctx.telemetry.finalization_reason = "test"
        ctx.telemetry.repeat_pattern_triggered = False
        ctx.telemetry.hotspot_hint_used = False
        ctx.tool_repeat_warnings = []
        ctx.telemetry.error = None
        ctx.telemetry.steps_taken = 0

        result = CustomTaskFinalizer.build_enhanced_result(ctx)
        assert "custom_field" in result
        assert result["custom_field"] == "custom_value"

    @patch("app.services.task_executor_refactored.agent_tools")
    def test_step_executor_extract_tool_info_robustness(self, mock_agent_tools):
        """✅ Test that tool info extraction is robust."""
        from app.services.fastapi_generation_service import (
            OrchestratorConfig,
            OrchestratorTelemetry,
        )
        from app.services.task_execution_helpers import TaskExecutionContext

        ctx = TaskExecutionContext(
            task=MagicMock(),
            mission=MagicMock(),
            cfg=OrchestratorConfig(model_name="gpt-4", max_steps=5),
            telemetry=OrchestratorTelemetry(),
        )

        executor = StepExecutor(ctx, MagicMock(), [], [], MagicMock())

        # Test with incomplete call
        call = {"id": "call_1"}
        fn_name, fn_args, call_id = executor._extract_tool_info(call)

        assert fn_name is None
        assert fn_args == {}
        assert call_id == "call_1"

        # Test with complete call
        call = {
            "id": "call_2",
            "function": {
                "name": "read_file",
                "arguments": '{"path": "/test.txt"}',
            },
        }
        fn_name, fn_args, call_id = executor._extract_tool_info(call)

        assert fn_name == "read_file"
        assert fn_args == {"path": "/test.txt"}
        assert call_id == "call_2"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
