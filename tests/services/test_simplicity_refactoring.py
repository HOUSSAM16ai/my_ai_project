import pytest
from unittest.mock import MagicMock, patch
from app.services.llm.invocation_handler import LLMRequestExecutor, LLMPayload, LLMSettings
from app.services.agent_tools.executor import ToolExecutor
from app.services.agent_tools.registry import ToolRegistry
from app.services.agent_tools.definitions import ToolResult

# -----------------------------------------------------------------------------
# Test LLM Request Executor (The new modular logic)
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_ai_client():
    with patch("app.services.llm.invocation_handler.get_ai_client") as mock:
        yield mock

class TestLLMRequestExecutor:
    def test_execute_success(self, mock_ai_client):
        # Setup
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = "Hello World"
        mock_completion.choices[0].message.tool_calls = None
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 5
        mock_completion.usage.total_tokens = 15

        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.return_value = mock_completion
        mock_ai_client.return_value = mock_client_instance

        executor = LLMRequestExecutor()
        payload = LLMPayload(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hi"}],
            tools=None,
            tool_choice=None,
            temperature=0.7,
            max_tokens=100,
            extra=None
        )

        # Execute
        result = executor.execute(payload)

        # Verify
        assert result["content"] == "Hello World"
        assert result["model"] == "gpt-4"
        assert result["usage"]["total_tokens"] == 15
        mock_client_instance.chat.completions.create.assert_called_once()

    def test_execute_empty_response_retry(self, mock_ai_client):
        # Setup: First call returns empty, second returns valid
        mock_empty = MagicMock()
        mock_empty.choices[0].message.content = ""
        mock_empty.choices[0].message.tool_calls = None

        mock_valid = MagicMock()
        mock_valid.choices[0].message.content = "Valid Response"
        mock_valid.choices[0].message.tool_calls = None
        mock_valid.usage.total_tokens = 10

        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create.side_effect = [mock_empty, mock_valid]
        mock_ai_client.return_value = mock_client_instance

        # Force shorter backoff for test speed
        with patch.dict("os.environ", {"LLM_RETRY_BACKOFF_BASE": "0.01", "LLM_MAX_RETRIES": "2"}):
            executor = LLMRequestExecutor()
            # Reload settings to pick up patched env vars
            executor.settings = LLMSettings()

            payload = LLMPayload("gpt-4", [], None, None, 0.7, 100, None)

            result = executor.execute(payload)

        assert result["content"] == "Valid Response"
        assert result["meta"]["attempts"] == 2


# -----------------------------------------------------------------------------
# Test Tool Registry & Executor (The new modular logic)
# -----------------------------------------------------------------------------

def simple_tool(x: int, y: int) -> int:
    return x + y

class TestAgentTools:
    def setup_method(self):
        # Clean registry before each test to avoid conflicts
        from app.services.agent_tools.globals import _TOOL_REGISTRY, _ALIAS_INDEX
        _TOOL_REGISTRY.clear()
        _ALIAS_INDEX.clear()

    def test_registry_and_execution(self):
        # 1. Register
        ToolRegistry.register(
            name="add_numbers",
            description="Adds two numbers",
            parameters={"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}},
            handler=None # Handler is updated by decorator usually, but we can manually test executor
        )

        # 2. Execute using Executor directly
        executor = ToolExecutor("add_numbers", simple_tool)
        result = executor.execute(x=5, y=3)

        assert isinstance(result, ToolResult)
        assert result.ok is True
        assert result.output == 8 # _coerce_to_tool_result handles primitive returns
        assert result.meta["tool"] == "add_numbers"

    def test_validation_failure(self):
        ToolRegistry.register(
            name="add_numbers",
            description="Adds two numbers",
            parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
            handler=None
        )

        executor = ToolExecutor("add_numbers", simple_tool)
        # Pass wrong type for x
        result = executor.execute(x="string_instead_of_int", y=3)

        assert result.ok is False
        assert "Argument validation failed" in result.error

    def test_alias_resolution(self):
        ToolRegistry.register(
            name="add_numbers",
            description="desc",
            parameters={},
            handler=None,
            aliases=["sum"]
        )

        from app.services.agent_tools.core import resolve_tool_name
        assert resolve_tool_name("sum") == "add_numbers"
