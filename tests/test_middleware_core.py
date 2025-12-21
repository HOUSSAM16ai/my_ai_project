# tests/test_middleware_core.py
"""
Comprehensive tests for the middleware core module.

This module provides critical middleware infrastructure and was at low coverage:
- pipeline.py (17% coverage)
- hooks.py (41% coverage)
- result.py (62% coverage)

These tests verify:
- MiddlewareResult creation and factory methods
- Lifecycle hooks registration and triggering
- SmartPipeline execution and statistics
- Error handling and recovery
"""

import pytest

from app.middleware.core.context import RequestContext
from app.middleware.core.hooks import (
    LifecycleHooks,
    get_global_hooks,
    on_after_execution,
    on_after_failure,
    on_after_success,
    on_before_execution,
)
from app.middleware.core.pipeline import SmartPipeline
from app.middleware.core.result import MiddlewareResult

# =============================================================================
# MIDDLEWARE RESULT TESTS
# =============================================================================


class TestMiddlewareResultCreation:
    """Tests for MiddlewareResult dataclass and factory methods."""

    def test_default_initialization(self):
        """Test default MiddlewareResult values."""
        result = MiddlewareResult()

        assert result.is_success is True
        assert result.status_code == 200
        assert result.message == ""
        assert result.error_code is None
        assert result.details == {}
        assert result.metadata == {}
        assert result.should_continue is True
        assert result.response_data is None

    def test_success_factory(self):
        """Test success() factory method."""
        result = MiddlewareResult.success()

        assert result.is_success is True
        assert result.status_code == 200
        assert result.message == "Success"
        assert result.should_continue is True

    def test_success_factory_custom_message(self):
        """Test success() with custom message."""
        result = MiddlewareResult.success(message="Request processed")

        assert result.is_success is True
        assert result.message == "Request processed"

    def test_failure_factory(self):
        """Test failure() factory method."""
        result = MiddlewareResult.failure(
            status_code=400,
            message="Bad request",
            error_code="INVALID_INPUT",
            details={"field": "email"},
        )

        assert result.is_success is False
        assert result.status_code == 400
        assert result.message == "Bad request"
        assert result.error_code == "INVALID_INPUT"
        assert result.details == {"field": "email"}
        assert result.should_continue is False

    def test_forbidden_factory(self):
        """Test forbidden() factory method."""
        result = MiddlewareResult.forbidden()

        assert result.is_success is False
        assert result.status_code == 403
        assert result.error_code == "FORBIDDEN"
        assert result.should_continue is False

    def test_forbidden_custom_message(self):
        """Test forbidden() with custom message."""
        result = MiddlewareResult.forbidden(message="Access denied to resource")

        assert result.message == "Access denied to resource"

    def test_unauthorized_factory(self):
        """Test unauthorized() factory method."""
        result = MiddlewareResult.unauthorized()

        assert result.is_success is False
        assert result.status_code == 401
        assert result.error_code == "UNAUTHORIZED"
        assert result.should_continue is False

    def test_rate_limited_factory(self):
        """Test rate_limited() factory method."""
        result = MiddlewareResult.rate_limited()

        assert result.is_success is False
        assert result.status_code == 429
        assert result.error_code == "RATE_LIMITED"
        assert result.details == {"retry_after": 60}

    def test_rate_limited_custom_retry(self):
        """Test rate_limited() with custom retry_after."""
        result = MiddlewareResult.rate_limited(retry_after=120)

        assert result.details == {"retry_after": 120}

    def test_bad_request_factory(self):
        """Test bad_request() factory method."""
        result = MiddlewareResult.bad_request()

        assert result.is_success is False
        assert result.status_code == 400
        assert result.error_code == "BAD_REQUEST"

    def test_internal_error_factory(self):
        """Test internal_error() factory method."""
        result = MiddlewareResult.internal_error()

        assert result.is_success is False
        assert result.status_code == 500
        assert result.error_code == "INTERNAL_ERROR"


class TestMiddlewareResultChaining:
    """Tests for chainable methods."""

    def test_with_metadata(self):
        """Test with_metadata() chainable method."""
        result = MiddlewareResult.success().with_metadata("request_id", "abc123")

        assert result.metadata["request_id"] == "abc123"
        assert result.is_success is True  # Original state preserved

    def test_with_metadata_chaining(self):
        """Test multiple with_metadata() calls."""
        result = (
            MiddlewareResult.success()
            .with_metadata("key1", "value1")
            .with_metadata("key2", "value2")
        )

        assert result.metadata["key1"] == "value1"
        assert result.metadata["key2"] == "value2"

    def test_with_details(self):
        """Test with_details() chainable method."""
        result = MiddlewareResult.failure(status_code=400, message="Error").with_details(
            field="email", reason="invalid format"
        )

        assert result.details["field"] == "email"
        assert result.details["reason"] == "invalid format"

    def test_with_details_merges(self):
        """Test with_details() merges with existing details."""
        result = MiddlewareResult.failure(
            status_code=400, message="Error", details={"existing": "data"}
        ).with_details(new_field="new_value")

        assert result.details["existing"] == "data"
        assert result.details["new_field"] == "new_value"


class TestMiddlewareResultSerialization:
    """Tests for to_dict() serialization."""

    def test_to_dict_success(self):
        """Test to_dict() for successful result."""
        result = MiddlewareResult.success(message="OK")
        data = result.to_dict()

        assert data["success"] is True
        assert data["message"] == "OK"
        assert "error_code" not in data

    def test_to_dict_failure_with_error_code(self):
        """Test to_dict() includes error_code when present."""
        result = MiddlewareResult.forbidden()
        data = result.to_dict()

        assert data["success"] is False
        assert data["error_code"] == "FORBIDDEN"

    def test_to_dict_with_details(self):
        """Test to_dict() includes details when present."""
        result = MiddlewareResult.failure(
            status_code=400, message="Error", details={"field": "name"}
        )
        data = result.to_dict()

        assert data["details"] == {"field": "name"}

    def test_to_dict_with_response_data(self):
        """Test to_dict() includes response_data when present."""
        result = MiddlewareResult.success()
        result.response_data = {"user_id": 123}
        data = result.to_dict()

        assert data["data"] == {"user_id": 123}

    def test_to_dict_omits_empty_fields(self):
        """Test to_dict() omits empty optional fields."""
        result = MiddlewareResult.success()
        data = result.to_dict()

        assert "error_code" not in data
        assert "details" not in data
        assert "data" not in data


# =============================================================================
# LIFECYCLE HOOKS TESTS
# =============================================================================


class TestLifecycleHooksRegistration:
    """Tests for hook registration."""

    def test_register_callback(self):
        """Test registering a callback."""
        hooks = LifecycleHooks()

        def my_callback():
            pass

        hooks.register("test_event", my_callback)

        assert hooks.get_hook_count("test_event") == 1

    def test_register_multiple_callbacks(self):
        """Test registering multiple callbacks for same event."""
        hooks = LifecycleHooks()

        hooks.register("test_event", lambda: None)
        hooks.register("test_event", lambda: None)
        hooks.register("test_event", lambda: None)

        assert hooks.get_hook_count("test_event") == 3

    def test_register_callbacks_different_events(self):
        """Test registering callbacks for different events."""
        hooks = LifecycleHooks()

        hooks.register("event_a", lambda: None)
        hooks.register("event_b", lambda: None)

        assert hooks.get_hook_count("event_a") == 1
        assert hooks.get_hook_count("event_b") == 1


class TestLifecycleHooksUnregistration:
    """Tests for hook unregistration."""

    def test_unregister_callback(self):
        """Test unregistering a callback."""
        hooks = LifecycleHooks()

        def my_callback():
            pass

        hooks.register("test_event", my_callback)
        result = hooks.unregister("test_event", my_callback)

        assert result is True
        assert hooks.get_hook_count("test_event") == 0

    def test_unregister_nonexistent_callback(self):
        """Test unregistering a callback that doesn't exist."""
        hooks = LifecycleHooks()

        result = hooks.unregister("test_event", lambda: None)

        assert result is False

    def test_unregister_from_nonexistent_event(self):
        """Test unregistering from an event that doesn't exist."""
        hooks = LifecycleHooks()

        result = hooks.unregister("nonexistent", lambda: None)

        assert result is False


class TestLifecycleHooksTrigger:
    """Tests for hook triggering."""

    def test_trigger_executes_callbacks(self):
        """Test trigger() executes registered callbacks."""
        hooks = LifecycleHooks()
        results = []

        def callback1():
            results.append("callback1")

        def callback2():
            results.append("callback2")

        hooks.register("test_event", callback1)
        hooks.register("test_event", callback2)

        hooks.trigger("test_event")

        assert "callback1" in results
        assert "callback2" in results

    def test_trigger_passes_arguments(self):
        """Test trigger() passes arguments to callbacks."""
        hooks = LifecycleHooks()
        received_args = []

        def callback(*args, **kwargs):
            received_args.append((args, kwargs))

        hooks.register("test_event", callback)

        hooks.trigger("test_event", "arg1", "arg2", key="value")

        assert received_args[0] == (("arg1", "arg2"), {"key": "value"})

    def test_trigger_handles_callback_errors(self):
        """Test trigger() continues despite callback errors."""
        hooks = LifecycleHooks()
        results = []

        def failing_callback():
            raise ValueError("Test error")

        def succeeding_callback():
            results.append("success")

        hooks.register("test_event", failing_callback)
        hooks.register("test_event", succeeding_callback)

        # Should not raise, should continue to next callback
        hooks.trigger("test_event")

        assert "success" in results

    def test_trigger_empty_event(self):
        """Test trigger() with no registered callbacks."""
        hooks = LifecycleHooks()

        # Should not raise
        hooks.trigger("nonexistent_event")


class TestLifecycleHooksClear:
    """Tests for hook clearing."""

    def test_clear_specific_event(self):
        """Test clear() for specific event."""
        hooks = LifecycleHooks()

        hooks.register("event_a", lambda: None)
        hooks.register("event_b", lambda: None)

        hooks.clear("event_a")

        assert hooks.get_hook_count("event_a") == 0
        assert hooks.get_hook_count("event_b") == 1

    def test_clear_all_events(self):
        """Test clear() for all events."""
        hooks = LifecycleHooks()

        hooks.register("event_a", lambda: None)
        hooks.register("event_b", lambda: None)

        hooks.clear()

        assert hooks.get_hook_count("event_a") == 0
        assert hooks.get_hook_count("event_b") == 0


class TestGlobalHooksAndDecorators:
    """Tests for global hooks and decorator functions."""

    def test_get_global_hooks(self):
        """Test get_global_hooks() returns singleton."""
        hooks1 = get_global_hooks()
        hooks2 = get_global_hooks()

        assert hooks1 is hooks2

    def test_on_before_execution_decorator(self):
        """Test @on_before_execution decorator."""
        global_hooks = get_global_hooks()
        initial_count = global_hooks.get_hook_count("before_execution")

        @on_before_execution
        def my_hook(ctx):
            pass

        assert global_hooks.get_hook_count("before_execution") == initial_count + 1

    def test_on_after_success_decorator(self):
        """Test @on_after_success decorator."""
        global_hooks = get_global_hooks()
        initial_count = global_hooks.get_hook_count("after_success")

        @on_after_success
        def my_hook(ctx, result):
            pass

        assert global_hooks.get_hook_count("after_success") == initial_count + 1

    def test_on_after_failure_decorator(self):
        """Test @on_after_failure decorator."""
        global_hooks = get_global_hooks()
        initial_count = global_hooks.get_hook_count("after_failure")

        @on_after_failure
        def my_hook(ctx, result):
            pass

        assert global_hooks.get_hook_count("after_failure") == initial_count + 1

    def test_on_after_execution_decorator(self):
        """Test @on_after_execution decorator."""
        global_hooks = get_global_hooks()
        initial_count = global_hooks.get_hook_count("after_execution")

        @on_after_execution
        def my_hook(ctx, result):
            pass

        assert global_hooks.get_hook_count("after_execution") == initial_count + 1


# =============================================================================
# SMART PIPELINE TESTS
# =============================================================================


class MockMiddleware:
    """Mock middleware for testing the pipeline."""

    def __init__(self, name: str, order: int = 0, result: MiddlewareResult = None):
        self.name = name
        self.order = order
        self._result = result or MiddlewareResult.success()
        self.process_called = False
        self.on_success_called = False
        self.on_error_called = False
        self.on_complete_called = False

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        self.process_called = True
        return self._result

    async def process_request_async(self, ctx: RequestContext) -> MiddlewareResult:
        self.process_called = True
        return self._result

    def should_process(self, ctx: RequestContext) -> bool:
        return True

    def on_success(self, ctx: RequestContext):
        self.on_success_called = True

    def on_error(self, ctx: RequestContext, error: Exception):
        self.on_error_called = True

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult):
        self.on_complete_called = True


class FailingMockMiddleware(MockMiddleware):
    """Mock middleware that raises an exception."""

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        self.process_called = True
        raise RuntimeError("Middleware failed")

    async def process_request_async(self, ctx: RequestContext) -> MiddlewareResult:
        self.process_called = True
        raise RuntimeError("Middleware failed")


class SkippingMockMiddleware(MockMiddleware):
    """Mock middleware that skips processing."""

    def should_process(self, ctx: RequestContext) -> bool:
        return False


class TestSmartPipelineInit:
    """Tests for SmartPipeline initialization."""

    def test_default_initialization(self):
        """Test pipeline initializes empty."""
        pipeline = SmartPipeline()

        assert pipeline.middlewares == []
        stats = pipeline.get_statistics()
        assert stats["total_requests"] == 0

    def test_initialization_with_middlewares(self):
        """Test pipeline initializes with middleware list."""
        mw1 = MockMiddleware("mw1", order=1)
        mw2 = MockMiddleware("mw2", order=2)

        pipeline = SmartPipeline(middlewares=[mw1, mw2])

        assert len(pipeline.middlewares) == 2


class TestSmartPipelineAddRemove:
    """Tests for adding and removing middlewares."""

    def test_add_middleware(self):
        """Test add_middleware() adds middleware."""
        pipeline = SmartPipeline()
        mw = MockMiddleware("test")

        pipeline.add_middleware(mw)

        assert len(pipeline.middlewares) == 1
        assert pipeline.middlewares[0].name == "test"

    def test_add_middleware_sorted_by_order(self):
        """Test middlewares are sorted by order."""
        pipeline = SmartPipeline()

        pipeline.add_middleware(MockMiddleware("third", order=30))
        pipeline.add_middleware(MockMiddleware("first", order=10))
        pipeline.add_middleware(MockMiddleware("second", order=20))

        names = [mw.name for mw in pipeline.middlewares]
        assert names == ["first", "second", "third"]

    def test_remove_middleware(self):
        """Test remove_middleware() removes middleware."""
        pipeline = SmartPipeline()
        mw = MockMiddleware("test")
        pipeline.add_middleware(mw)

        result = pipeline.remove_middleware("test")

        assert result is True
        assert len(pipeline.middlewares) == 0

    def test_remove_nonexistent_middleware(self):
        """Test remove_middleware() returns False for nonexistent."""
        pipeline = SmartPipeline()

        result = pipeline.remove_middleware("nonexistent")

        assert result is False


class TestSmartPipelineExecution:
    """Tests for pipeline execution."""

    def test_run_executes_middlewares(self):
        """Test run() executes all middlewares."""
        mw1 = MockMiddleware("mw1", order=1)
        mw2 = MockMiddleware("mw2", order=2)
        pipeline = SmartPipeline(middlewares=[mw1, mw2])

        ctx = RequestContext(method="GET", path="/test")
        result = pipeline.run(ctx)

        assert result.is_success
        assert mw1.process_called
        assert mw2.process_called

    def test_run_calls_lifecycle_hooks(self):
        """Test run() calls lifecycle hooks on success."""
        mw = MockMiddleware("test")
        pipeline = SmartPipeline(middlewares=[mw])

        ctx = RequestContext(method="GET", path="/test")
        pipeline.run(ctx)

        assert mw.on_success_called
        assert mw.on_complete_called

    def test_run_short_circuits_on_failure(self):
        """Test run() stops on middleware failure."""
        mw1 = MockMiddleware("mw1", order=1, result=MiddlewareResult.forbidden())
        mw2 = MockMiddleware("mw2", order=2)
        pipeline = SmartPipeline(middlewares=[mw1, mw2])

        ctx = RequestContext(method="GET", path="/test")
        result = pipeline.run(ctx)

        assert result.is_success is False
        assert mw1.process_called
        assert not mw2.process_called  # Should not be called due to short-circuit

    def test_run_handles_middleware_exception(self):
        """Test run() handles middleware exception gracefully."""
        mw = FailingMockMiddleware("failing")
        pipeline = SmartPipeline(middlewares=[mw])

        ctx = RequestContext(method="GET", path="/test")
        result = pipeline.run(ctx)

        assert result.is_success is False
        assert result.status_code == 500
        assert mw.on_error_called

    def test_run_skips_disabled_middleware(self):
        """Test run() skips middleware that returns False from should_process."""
        mw1 = SkippingMockMiddleware("skipping", order=1)
        mw2 = MockMiddleware("active", order=2)
        pipeline = SmartPipeline(middlewares=[mw1, mw2])

        ctx = RequestContext(method="GET", path="/test")
        result = pipeline.run(ctx)

        assert result.is_success
        assert not mw1.process_called
        assert mw2.process_called


class TestSmartPipelineAsyncExecution:
    """Tests for async pipeline execution."""

    @pytest.mark.asyncio
    async def test_run_async_executes_middlewares(self):
        """Test run_async() executes all middlewares."""
        mw1 = MockMiddleware("mw1", order=1)
        mw2 = MockMiddleware("mw2", order=2)
        pipeline = SmartPipeline(middlewares=[mw1, mw2])

        ctx = RequestContext(method="GET", path="/test")
        result = await pipeline.run_async(ctx)

        assert result.is_success
        assert mw1.process_called
        assert mw2.process_called

    @pytest.mark.asyncio
    async def test_run_async_handles_exception(self):
        """Test run_async() handles middleware exception."""
        mw = FailingMockMiddleware("failing")
        pipeline = SmartPipeline(middlewares=[mw])

        ctx = RequestContext(method="GET", path="/test")
        result = await pipeline.run_async(ctx)

        assert result.is_success is False
        assert result.status_code == 500


class TestSmartPipelineStatistics:
    """Tests for pipeline statistics."""

    def test_get_statistics(self):
        """Test get_statistics() returns proper structure."""
        pipeline = SmartPipeline()

        stats = pipeline.get_statistics()

        assert "total_requests" in stats
        assert "successful_requests" in stats
        assert "failed_requests" in stats
        assert "success_rate" in stats
        assert "total_execution_time" in stats
        assert "average_execution_time" in stats
        assert "middleware_count" in stats
        assert "middleware_stats" in stats

    def test_statistics_track_requests(self):
        """Test statistics track request counts."""
        mw = MockMiddleware("test")
        pipeline = SmartPipeline(middlewares=[mw])

        ctx = RequestContext(method="GET", path="/test")

        pipeline.run(ctx)
        pipeline.run(ctx)
        pipeline.run(ctx)

        stats = pipeline.get_statistics()
        assert stats["total_requests"] == 3
        assert stats["successful_requests"] == 3
        assert stats["failed_requests"] == 0

    def test_statistics_track_failures(self):
        """Test statistics track failed requests."""
        mw = MockMiddleware("test", result=MiddlewareResult.forbidden())
        pipeline = SmartPipeline(middlewares=[mw])

        ctx = RequestContext(method="GET", path="/test")

        pipeline.run(ctx)
        pipeline.run(ctx)

        stats = pipeline.get_statistics()
        assert stats["total_requests"] == 2
        assert stats["failed_requests"] == 2

    def test_statistics_per_middleware(self):
        """Test per-middleware statistics are tracked."""
        mw = MockMiddleware("test_mw")
        pipeline = SmartPipeline(middlewares=[mw])

        ctx = RequestContext(method="GET", path="/test")
        pipeline.run(ctx)

        stats = pipeline.get_statistics()
        mw_stats = stats["middleware_stats"].get("test_mw")

        assert mw_stats is not None
        assert mw_stats["executions"] == 1
        assert mw_stats["successes"] == 1

    def test_reset_statistics(self):
        """Test reset_statistics() clears all stats."""
        mw = MockMiddleware("test")
        pipeline = SmartPipeline(middlewares=[mw])

        ctx = RequestContext(method="GET", path="/test")
        pipeline.run(ctx)

        pipeline.reset_statistics()

        stats = pipeline.get_statistics()
        assert stats["total_requests"] == 0
        assert stats["successful_requests"] == 0


class TestSmartPipelineHelpers:
    """Tests for helper methods."""

    def test_get_middleware_list(self):
        """Test get_middleware_list() returns ordered names."""
        pipeline = SmartPipeline()
        pipeline.add_middleware(MockMiddleware("second", order=20))
        pipeline.add_middleware(MockMiddleware("first", order=10))

        names = pipeline.get_middleware_list()

        assert names == ["first", "second"]

    def test_repr(self):
        """Test __repr__() returns meaningful string."""
        pipeline = SmartPipeline()
        pipeline.add_middleware(MockMiddleware("test"))

        repr_str = repr(pipeline)

        assert "SmartPipeline" in repr_str
        assert "1" in repr_str


# =============================================================================
# REQUEST CONTEXT TESTS
# =============================================================================


class TestRequestContext:
    """Tests for RequestContext dataclass."""

    def test_default_initialization(self):
        """Test RequestContext default values."""
        ctx = RequestContext()

        assert ctx.method == "GET"
        assert ctx.path == "/"
        assert ctx.headers == {}
        assert ctx.query_params == {}
        assert ctx.ip_address == "unknown"
        assert ctx.request_id is not None

    def test_custom_initialization(self):
        """Test RequestContext with custom values."""
        ctx = RequestContext(
            method="POST",
            path="/api/users",
            headers={"Content-Type": "application/json"},
            ip_address="192.168.1.1",
        )

        assert ctx.method == "POST"
        assert ctx.path == "/api/users"
        assert ctx.headers["Content-Type"] == "application/json"
        assert ctx.ip_address == "192.168.1.1"

    def test_set_trace_context(self):
        """Test set_trace_context() sets tracing info."""
        ctx = RequestContext()

        ctx.set_trace_context("trace-123", "span-456")

        assert ctx.trace_id == "trace-123"
        assert ctx.span_id == "span-456"

    def test_set_user_context(self):
        """Test set_user_context() sets user info."""
        ctx = RequestContext()

        ctx.set_user_context("user-123", "session-456")

        assert ctx.user_id == "user-123"
        assert ctx.session_id == "session-456"

    def test_add_and_get_metadata(self):
        """Test add_metadata() and get_metadata()."""
        ctx = RequestContext()

        ctx.add_metadata("custom_key", "custom_value")

        assert ctx.get_metadata("custom_key") == "custom_value"
        assert ctx.get_metadata("nonexistent", "default") == "default"

    def test_get_header_case_insensitive(self):
        """Test get_header() is case-insensitive."""
        ctx = RequestContext(headers={"Content-Type": "application/json", "X-Request-ID": "abc"})

        assert ctx.get_header("content-type") == "application/json"
        assert ctx.get_header("CONTENT-TYPE") == "application/json"
        assert ctx.get_header("x-request-id") == "abc"

    def test_get_header_default(self):
        """Test get_header() returns default for missing header."""
        ctx = RequestContext()

        assert ctx.get_header("Missing-Header", "default") == "default"

    def test_to_dict(self):
        """Test to_dict() serialization."""
        ctx = RequestContext(
            method="GET",
            path="/test",
            ip_address="127.0.0.1",
        )
        ctx.set_trace_context("trace-1", "span-1")
        ctx.set_user_context("user-1")

        data = ctx.to_dict()

        assert data["method"] == "GET"
        assert data["path"] == "/test"
        assert data["ip_address"] == "127.0.0.1"
        assert data["trace_id"] == "trace-1"
        assert data["user_id"] == "user-1"
        assert "timestamp" in data
