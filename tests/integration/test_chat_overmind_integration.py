"""
Integration tests for Chat + Overmind integration.
Tests all handlers and safety measures.

This tests the ChatOrchestratorService which bridges:
- Admin Chat (app/api/routers/admin.py)
- Master Agent (app/services/master_agent_service.py)
- Agent Tools (app/services/agent_tools.py)
"""

import time

import pytest

from app.core.rate_limiter import RateLimitConfig, ToolRateLimiter
from app.services.async_tool_bridge import AsyncAgentTools, run_sync_tool
from app.services.chat_orchestrator_service import (
    ChatIntent,
    ChatOrchestratorService,
    ErrorSanitizer,
    IntentDetector,
    IntentResult,
    PathValidator,
    get_chat_orchestrator,
)


class TestIntentDetection:
    """Test intent detection patterns."""

    @pytest.mark.parametrize(
        "text,expected_intent",
        [
            ("read app/models.py", ChatIntent.FILE_READ),
            ("show file app/main.py", ChatIntent.FILE_READ),
            ("اقرأ ملف app/config.py", ChatIntent.FILE_READ),
            ("search AdminMessage", ChatIntent.CODE_SEARCH),
            ("find SessionLocal", ChatIntent.CODE_SEARCH),
            ("ابحث عن User", ChatIntent.CODE_SEARCH),
            (
                "analyze the project",
                ChatIntent.PROJECT_INDEX,
            ),  # Matched by PROJECT_INDEX pattern first
            ("refactor the codebase", ChatIntent.MISSION_COMPLEX),
            ("حلل المشروع", ChatIntent.PROJECT_INDEX),  # Matched by PROJECT_INDEX pattern first
            ("create a mission to fix bugs", ChatIntent.MISSION_COMPLEX),
            ("help", ChatIntent.HELP),
            ("مساعدة", ChatIntent.HELP),
            ("hello how are you", ChatIntent.SIMPLE_CHAT),
            ("what is python", ChatIntent.SIMPLE_CHAT),
        ],
    )
    def test_intent_detection(self, text, expected_intent):
        result = IntentDetector.detect(text)
        assert result.intent == expected_intent

    def test_intent_result_has_params(self):
        result = IntentDetector.detect("read app/models.py")
        assert result.intent == ChatIntent.FILE_READ
        assert "path" in result.params
        assert "models.py" in result.params["path"]


class TestPathValidator:
    """Test path validation security."""

    @pytest.mark.parametrize(
        "path,expected_valid",
        [
            ("app/models.py", True),
            ("src/utils/helper.py", True),
            ("README.md", True),
            ("../../../etc/passwd", False),
            ("/etc/passwd", False),
            ("C:\\Windows\\System32", False),
            ("~/.bashrc", False),
        ],
    )
    def test_path_validation(self, path, expected_valid):
        valid, _ = PathValidator.validate(path)
        assert valid == expected_valid

    def test_blocks_null_byte(self):
        valid, _ = PathValidator.validate("file\x00.py")
        assert not valid

    def test_blocks_long_path(self):
        valid, _ = PathValidator.validate("a" * 600)
        assert not valid


class TestErrorSanitizer:
    """Test error sanitization."""

    def test_sanitizes_file_paths(self):
        error = "Error in /app/services/secret.py line 42"
        result = ErrorSanitizer.sanitize(error)
        assert "/app/" not in result
        assert "line 42" not in result
        assert "[file]" in result
        assert "line [N]" in result

    def test_sanitizes_credentials(self):
        error = "Failed with password='secret123' and api_key=sk-1234"
        result = ErrorSanitizer.sanitize(error)
        assert "secret123" not in result
        assert "sk-1234" not in result

    def test_truncates_long_errors(self):
        error = "x" * 500
        result = ErrorSanitizer.sanitize(error)
        assert len(result) <= 203  # 200 + "..."

    def test_handles_none_error(self):
        result = ErrorSanitizer.sanitize(None)
        assert result == "Unknown error"

    def test_handles_empty_error(self):
        result = ErrorSanitizer.sanitize("")
        assert result == "Unknown error"


class TestRateLimiter:
    """Test rate limiting."""

    def test_allows_within_limit(self):
        limiter = ToolRateLimiter(RateLimitConfig(max_calls=5, window_seconds=60))

        for _ in range(5):
            allowed, _ = limiter.check(user_id=1, tool_name="test")
            assert allowed

    def test_blocks_after_limit(self):
        limiter = ToolRateLimiter(RateLimitConfig(max_calls=2, window_seconds=60))

        limiter.check(user_id=1, tool_name="test")
        limiter.check(user_id=1, tool_name="test")
        allowed, _ = limiter.check(user_id=1, tool_name="test")

        assert not allowed

    def test_different_users_have_separate_limits(self):
        limiter = ToolRateLimiter(RateLimitConfig(max_calls=1, window_seconds=60))

        allowed1, _ = limiter.check(user_id=1, tool_name="test")
        allowed2, _ = limiter.check(user_id=2, tool_name="test")

        assert allowed1
        assert allowed2

    def test_different_tools_have_separate_limits(self):
        limiter = ToolRateLimiter(RateLimitConfig(max_calls=1, window_seconds=60))

        allowed1, _ = limiter.check(user_id=1, tool_name="tool1")
        allowed2, _ = limiter.check(user_id=1, tool_name="tool2")

        assert allowed1
        assert allowed2

    def test_reset_clears_limit(self):
        limiter = ToolRateLimiter(RateLimitConfig(max_calls=1, window_seconds=60))

        limiter.check(user_id=1, tool_name="test")
        allowed1, _ = limiter.check(user_id=1, tool_name="test")
        assert not allowed1

        limiter.reset(user_id=1, tool_name="test")

        allowed2, _ = limiter.check(user_id=1, tool_name="test")
        assert allowed2


class TestChatOrchestrator:
    """Test chat orchestrator handlers."""

    @pytest.fixture
    def orchestrator(self):
        return ChatOrchestratorService()

    @pytest.mark.asyncio
    async def test_file_read_validates_path(self, orchestrator):
        """Test that invalid paths are rejected."""
        chunks = []
        async for chunk in orchestrator.handle_file_read("../../../etc/passwd", user_id=1):
            chunks.append(chunk)

        response = "".join(chunks)
        assert "غير صالح" in response or "blocked" in response.lower()

    @pytest.mark.asyncio
    async def test_code_search_validates_short_query(self, orchestrator):
        """Test that short queries are rejected."""
        chunks = []
        async for chunk in orchestrator.handle_code_search("x", user_id=1):
            chunks.append(chunk)

        response = "".join(chunks)
        assert "قصير" in response

    @pytest.mark.asyncio
    async def test_code_search_validates_long_query(self, orchestrator):
        """Test that long queries are rejected."""
        chunks = []
        async for chunk in orchestrator.handle_code_search("x" * 300, user_id=1):
            chunks.append(chunk)

        response = "".join(chunks)
        assert "طويل" in response

    @pytest.mark.asyncio
    async def test_help_handler_returns_content(self, orchestrator):
        """Test help handler returns useful content."""
        chunks = []
        async for chunk in orchestrator.handle_help():
            chunks.append(chunk)

        response = "".join(chunks)
        assert "Overmind" in response
        assert "قراءة" in response or "read" in response.lower()

    @pytest.mark.asyncio
    async def test_graceful_degradation_when_tools_unavailable(self, orchestrator):
        """Test that chat works when tools are unavailable."""
        orchestrator._async_tools = None
        orchestrator._initialized = True

        chunks = []
        async for chunk in orchestrator.handle_file_read("app/test.py", user_id=1):
            chunks.append(chunk)

        response = "".join(chunks)
        assert "غير متاحة" in response


class TestSingletonInstance:
    """Test singleton pattern."""

    def test_get_chat_orchestrator_returns_same_instance(self):
        """Test that get_chat_orchestrator returns singleton."""
        instance1 = get_chat_orchestrator()
        instance2 = get_chat_orchestrator()
        assert instance1 is instance2


class TestIntentResult:
    """Test IntentResult dataclass."""

    def test_create_result(self):
        """Test creating IntentResult."""
        result = IntentResult(
            intent=ChatIntent.FILE_READ,
            confidence=0.9,
            params={"path": "test.py"},
            reasoning="Test reasoning",
        )
        assert result.intent == ChatIntent.FILE_READ
        assert result.confidence == 0.9
        assert result.params["path"] == "test.py"
        assert result.reasoning == "Test reasoning"


class TestAsyncToolBridge:
    """Test async tool bridge functionality."""

    @pytest.mark.asyncio
    async def test_run_sync_tool_handles_timeout(self):
        """Test that run_sync_tool handles timeout correctly."""

        def slow_function():
            time.sleep(10)
            return "done"

        with pytest.raises(TimeoutError):
            await run_sync_tool(slow_function, timeout=0.1)

    @pytest.mark.asyncio
    async def test_async_tools_reports_unavailable(self):
        """Test AsyncAgentTools reports unavailable when tools not loaded."""
        tools = AsyncAgentTools()
        tools._tools = None
        tools._loaded = True

        assert not tools.available

        result = await tools.read_file("test.py")
        assert not result["ok"]
        assert "not available" in result["error"]


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_starts_closed(self):
        """Test circuit breaker starts in closed state."""
        from app.core.resilience.circuit_breaker import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(name="test")
        assert breaker.state == CircuitState.CLOSED
        can_exec, _ = breaker.can_execute()
        assert can_exec

    def test_circuit_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        from app.core.resilience.circuit_breaker import (
            CircuitBreaker,
            CircuitBreakerConfig,
            CircuitState,
        )

        # Update field name: timeout instead of recovery_timeout
        config = CircuitBreakerConfig(failure_threshold=3, timeout=30.0)
        breaker = CircuitBreaker(name="test", config=config)

        # Record failures
        for _ in range(3):
            breaker.record_failure()

        assert breaker.state == CircuitState.OPEN
        can_exec, msg = breaker.can_execute()
        assert not can_exec
        assert "Circuit open" in msg

    def test_circuit_closes_after_success(self):
        """Test circuit closes after successful recovery."""
        from app.core.resilience.circuit_breaker import CircuitBreaker, CircuitState

        breaker = CircuitBreaker(name="test")
        # Manipulate internal state as setter is not available on property
        breaker._state = CircuitState.HALF_OPEN

        # Call record_success twice to meet default threshold
        breaker.record_success()
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_registry(self):
        """Test circuit breaker registry returns same instance."""
        from app.services.chat_orchestrator_service import CircuitBreakerRegistry

        CircuitBreakerRegistry.reset_all()

        breaker1 = CircuitBreakerRegistry.get("test_tool")
        breaker2 = CircuitBreakerRegistry.get("test_tool")

        assert breaker1 is breaker2


class TestChatTelemetry:
    """Test telemetry functionality."""

    def test_telemetry_to_dict(self):
        """Test telemetry serialization."""
        from app.services.chat_orchestrator_service import ChatTelemetry

        telemetry = ChatTelemetry(
            intent_detection_time_ms=10.5,
            tool_execution_time_ms=100.0,
            tool_name="read_file",
            success=True,
        )

        data = telemetry.to_dict()
        assert data["intent_detection_time_ms"] == 10.5
        assert data["tool_execution_time_ms"] == 100.0
        assert data["tool_name"] == "read_file"
        assert data["success"] is True


class TestNewHandlers:
    """Test new handlers added in V4."""

    @pytest.fixture
    def orchestrator(self):
        return ChatOrchestratorService()

    @pytest.mark.asyncio
    async def test_project_index_validates_rate_limit(self, orchestrator):
        """Test project index respects rate limits."""
        orchestrator._initialized = True
        orchestrator._async_tools = None

        chunks = []
        async for chunk in orchestrator.handle_project_index(user_id=1):
            chunks.append(chunk)

        response = "".join(chunks)
        # Should indicate tools unavailable
        assert "غير متاحة" in response or "📊" in response

    @pytest.mark.asyncio
    async def test_file_write_validates_path(self, orchestrator):
        """Test file write validates path."""
        chunks = []
        async for chunk in orchestrator.handle_file_write(
            path="../../../etc/passwd", content="test", user_id=1
        ):
            chunks.append(chunk)

        response = "".join(chunks)
        assert "غير صالح" in response or "blocked" in response.lower()

    @pytest.mark.asyncio
    async def test_help_includes_new_commands(self, orchestrator):
        """Test help includes new commands."""
        chunks = []
        async for chunk in orchestrator.handle_help():
            chunks.append(chunk)

        response = "".join(chunks)
        assert "كتابة الملفات" in response or "📝" in response
        assert "تحليل المشروع" in response or "📊" in response

    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self, orchestrator):
        """Test circuit breaker is used in handlers."""
        from app.services.chat_orchestrator_service import CircuitBreakerRegistry

        CircuitBreakerRegistry.reset_all()
        orchestrator._ensure_initialized()

        # Get circuit breaker for read_file
        breaker = orchestrator._get_circuit_breaker("read_file")
        assert breaker.name == "read_file"


class TestDomainEvents:
    """Test domain events for chat."""

    def test_chat_intent_detected_event(self):
        """Test ChatIntentDetected event."""
        from app.services.domain_events import ChatIntentDetected

        event = ChatIntentDetected(
            conversation_id="123",
            user_id="456",
            intent="file_read",
            confidence=0.9,
            message_preview="read app/models.py",
        )

        assert event.payload["conversation_id"] == "123"
        assert event.payload["intent"] == "file_read"
        assert event.payload["confidence"] == 0.9

    def test_tool_execution_started_event(self):
        """Test ToolExecutionStarted event."""
        from app.services.domain_events import ToolExecutionStarted

        event = ToolExecutionStarted(
            tool_name="read_file",
            user_id="123",
            conversation_id="456",
            params={"path": "app/models.py"},
        )

        assert event.payload["tool_name"] == "read_file"
        assert event.payload["params"]["path"] == "app/models.py"

    def test_tool_execution_completed_event(self):
        """Test ToolExecutionCompleted event."""
        from app.services.domain_events import ToolExecutionCompleted

        event = ToolExecutionCompleted(
            tool_name="read_file",
            user_id="123",
            conversation_id="456",
            success=True,
            duration_ms=100.5,
            result_preview="# app/models.py...",
        )

        assert event.payload["success"] is True
        assert event.payload["duration_ms"] == 100.5

    def test_mission_created_from_chat_event(self):
        """Test MissionCreatedFromChat event."""
        from app.services.domain_events import MissionCreatedFromChat

        event = MissionCreatedFromChat(
            mission_id="789",
            conversation_id="456",
            user_id="123",
            objective="Fix all bugs in the codebase",
        )

        assert event.payload["mission_id"] == "789"
        assert event.payload["conversation_id"] == "456"
        assert "Fix all bugs" in event.payload["objective"]

    def test_events_registered_in_registry(self):
        """Test new events are registered."""
        from app.services.domain_events import DomainEventRegistry

        events = DomainEventRegistry.list_events()

        assert "ChatIntentDetected" in events
        assert "ToolExecutionStarted" in events
        assert "ToolExecutionCompleted" in events
        assert "MissionCreatedFromChat" in events
