"""
SUPERHUMAN TESTS FOR DUPLICATION ELIMINATION MODULES
=====================================================
اختبارات خارقة لضمان القضاء الكامل على التكرار

Tests for common_imports, error_handling, and base_profiler modules.
"""
import time
from unittest.mock import MagicMock, patch

import pytest

from app.core.common_imports import ImportHelper, FeatureFlags
from app.core.error_handling import (
    ErrorHandler,
    capture_errors,
    format_exception,
    retry_on_failure,
    safe_context,
    safe_execute,
    suppress_errors,
)
from app.core.base_profiler import (
    BaseMetricsCollector,
    BaseProfiler,
    CountProfiler,
    RingBuffer,
    TimeProfiler,
)


class TestCommonImports:
    """Test common imports module with EXTREME precision."""

    def test_import_helper_get_existing_module(self):
        """✅ Test getting existing module."""
        module = ImportHelper.get_module('os')
        assert module is not None
        assert hasattr(module, 'path')

    def test_import_helper_get_nonexistent_module(self):
        """✅ Test getting non-existent module with fallback."""
        result = ImportHelper.get_module('nonexistent_module_xyz', fallback="FALLBACK")
        assert result == "FALLBACK"

    def test_import_helper_has_module(self):
        """✅ Test checking module existence."""
        assert ImportHelper.has_module('os') is True
        assert ImportHelper.has_module('nonexistent_module') is False

    def test_import_helper_caching(self):
        """✅ Test that module imports are cached."""
        # Clear cache first
        ImportHelper._cache.clear()
        
        # First call
        module1 = ImportHelper.get_module('json')
        # Second call should return cached version
        module2 = ImportHelper.get_module('json')
        
        assert module1 is module2
        assert 'json' in ImportHelper._cache

    def test_feature_flags(self):
        """✅ Test feature flags."""
        # These should always be available in test environment
        assert isinstance(FeatureFlags.HAS_SQLALCHEMY, bool)
        assert isinstance(FeatureFlags.HAS_FASTAPI, bool)
        assert isinstance(FeatureFlags.HAS_PYDANTIC, bool)


class TestErrorHandling:
    """Test error handling framework with DIVINE precision."""

    def test_safe_execute_success(self):
        """✅ Test safe_execute with successful function."""
        @safe_execute(default_return="FALLBACK")
        def successful_func():
            return "SUCCESS"
        
        result = successful_func()
        assert result == "SUCCESS"

    def test_safe_execute_with_error(self):
        """✅ Test safe_execute with failing function."""
        @safe_execute(default_return="FALLBACK", log_error=False)
        def failing_func():
            raise ValueError("Test error")
        
        result = failing_func()
        assert result == "FALLBACK"

    def test_safe_execute_with_none_default(self):
        """✅ Test safe_execute returns None by default."""
        @safe_execute(log_error=False)
        def failing_func():
            raise ValueError("Test error")
        
        result = failing_func()
        assert result is None

    def test_retry_on_failure_success_first_try(self):
        """✅ Test retry decorator with immediate success."""
        call_count = [0]
        
        @retry_on_failure(max_retries=3, delay=0.01, log_retry=False)
        def func_succeeds():
            call_count[0] += 1
            return "SUCCESS"
        
        result = func_succeeds()
        assert result == "SUCCESS"
        assert call_count[0] == 1

    def test_retry_on_failure_success_after_retries(self):
        """✅ Test retry decorator with success after failures."""
        call_count = [0]
        
        @retry_on_failure(max_retries=3, delay=0.01, log_retry=False)
        def func_fails_twice():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "SUCCESS"
        
        result = func_fails_twice()
        assert result == "SUCCESS"
        assert call_count[0] == 3

    def test_retry_on_failure_exhausted(self):
        """✅ Test retry decorator when all retries exhausted."""
        @retry_on_failure(max_retries=2, delay=0.01, log_retry=False)
        def always_fails():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_fails()

    def test_suppress_errors_success(self):
        """✅ Test suppress_errors with successful function."""
        @suppress_errors(ValueError, KeyError)
        def successful_func():
            return "SUCCESS"
        
        result = successful_func()
        assert result == "SUCCESS"

    def test_suppress_errors_suppresses_specified(self):
        """✅ Test suppress_errors suppresses specified exceptions."""
        @suppress_errors(ValueError, log_error=False)
        def raises_value_error():
            raise ValueError("This should be suppressed")
        
        result = raises_value_error()
        assert result is None  # Error suppressed

    def test_suppress_errors_doesnt_suppress_others(self):
        """✅ Test suppress_errors doesn't suppress other exceptions."""
        @suppress_errors(ValueError, log_error=False)
        def raises_type_error():
            raise TypeError("This should NOT be suppressed")
        
        with pytest.raises(TypeError, match="NOT be suppressed"):
            raises_type_error()

    def test_safe_context_success(self):
        """✅ Test safe_context with successful block."""
        result = None
        with safe_context("Test operation", log_error=False):
            result = "SUCCESS"
        
        assert result == "SUCCESS"

    def test_safe_context_with_error(self):
        """✅ Test safe_context with error in block."""
        with safe_context("Test operation", default_return="FALLBACK", log_error=False):
            raise ValueError("Test error")

    def test_capture_errors_captures(self):
        """✅ Test capture_errors captures exceptions."""
        errors = []
        
        with capture_errors(errors):
            raise ValueError("Captured error")
        
        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)
        assert str(errors[0]) == "Captured error"

    def test_capture_errors_without_list(self):
        """✅ Test capture_errors without error list."""
        # Should not crash
        with capture_errors():
            raise ValueError("Error without list")

    def test_error_handler_handle(self):
        """✅ Test ErrorHandler.handle method."""
        handler = ErrorHandler("test_service")
        
        error = ValueError("Test error")
        handler.handle(error, context={"key": "value"})
        
        assert handler.error_count == 1

    def test_error_handler_wrap_function_success(self):
        """✅ Test ErrorHandler.wrap_function with success."""
        handler = ErrorHandler("test")
        
        def func():
            return "SUCCESS"
        
        wrapped = handler.wrap_function(func)
        result = wrapped()
        
        assert result == "SUCCESS"
        assert handler.error_count == 0

    def test_error_handler_wrap_function_error(self):
        """✅ Test ErrorHandler.wrap_function with error."""
        handler = ErrorHandler("test")
        
        def func():
            raise ValueError("Test")
        
        wrapped = handler.wrap_function(func, default_return="FALLBACK")
        result = wrapped()
        
        assert result == "FALLBACK"
        assert handler.error_count == 1

    def test_format_exception_without_traceback(self):
        """✅ Test format_exception without traceback."""
        error = ValueError("Test error")
        formatted = format_exception(error, include_traceback=False)
        
        assert "ValueError" in formatted
        assert "Test error" in formatted
        assert "Traceback" not in formatted

    def test_format_exception_with_traceback(self):
        """✅ Test format_exception with traceback."""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            formatted = format_exception(e, include_traceback=True)
            
            assert "ValueError" in formatted
            assert "Test error" in formatted
            assert "Traceback" in formatted


class TestBaseProfiler:
    """Test base profiler classes with LEGENDARY precision."""

    def test_ring_buffer_append(self):
        """✅ Test RingBuffer append."""
        buffer = RingBuffer[int](max_size=3)
        
        buffer.append(1)
        buffer.append(2)
        buffer.append(3)
        
        assert len(buffer) == 3
        assert buffer.to_list() == [1, 2, 3]

    def test_ring_buffer_overflow(self):
        """✅ Test RingBuffer handles overflow."""
        buffer = RingBuffer[int](max_size=3)
        
        buffer.append(1)
        buffer.append(2)
        buffer.append(3)
        buffer.append(4)  # Should remove 1
        
        assert len(buffer) == 3
        assert buffer.to_list() == [2, 3, 4]

    def test_ring_buffer_clear(self):
        """✅ Test RingBuffer clear."""
        buffer = RingBuffer[int](max_size=5)
        buffer.append(1)
        buffer.append(2)
        
        buffer.clear()
        
        assert len(buffer) == 0

    def test_base_profiler_init(self):
        """✅ Test BaseProfiler initialization."""
        profiler = BaseProfiler(max_samples=100)
        
        assert profiler.enabled is True
        assert profiler.sample_count == 0

    def test_base_profiler_enable_disable(self):
        """✅ Test BaseProfiler enable/disable."""
        profiler = BaseProfiler()
        
        assert profiler.enabled is True
        
        profiler.disable()
        assert profiler.enabled is False
        
        profiler.enable()
        assert profiler.enabled is True

    def test_base_profiler_clear(self):
        """✅ Test BaseProfiler clear."""
        profiler = BaseProfiler()
        profiler._buffer.append("sample")
        
        assert profiler.sample_count == 1
        
        profiler.clear()
        assert profiler.sample_count == 0

    def test_base_metrics_collector_record(self):
        """✅ Test BaseMetricsCollector record."""
        collector = BaseMetricsCollector()
        
        collector.record("value1")
        collector.record("value2")
        
        assert collector.sample_count == 2
        assert collector.total_count == 2

    def test_base_metrics_collector_record_disabled(self):
        """✅ Test BaseMetricsCollector doesn't record when disabled."""
        collector = BaseMetricsCollector()
        collector.disable()
        
        collector.record("value")
        
        assert collector.sample_count == 0
        assert collector.total_count == 0

    def test_base_metrics_collector_reset(self):
        """✅ Test BaseMetricsCollector reset."""
        collector = BaseMetricsCollector()
        collector.record("value")
        
        collector.reset()
        
        assert collector.sample_count == 0
        assert collector.total_count == 0

    def test_base_metrics_collector_statistics(self):
        """✅ Test BaseMetricsCollector statistics."""
        collector = BaseMetricsCollector(max_samples=100)
        collector.record("value")
        
        stats = collector.get_statistics()
        
        assert stats["enabled"] is True
        assert stats["total_count"] == 1
        assert stats["buffer_size"] == 1
        assert stats["max_samples"] == 100

    def test_time_profiler_record_duration(self):
        """✅ Test TimeProfiler record_duration."""
        profiler = TimeProfiler()
        
        profiler.record_duration(100.5, "operation1")
        profiler.record_duration(200.3, "operation2")
        
        assert profiler.sample_count == 2
        assert profiler.total_count == 2

    def test_time_profiler_statistics(self):
        """✅ Test TimeProfiler statistics with averages."""
        profiler = TimeProfiler()
        
        profiler.record_duration(100.0, "op1")
        profiler.record_duration(200.0, "op2")
        profiler.record_duration(300.0, "op3")
        
        stats = profiler.get_statistics()
        
        assert stats["avg_duration_ms"] == 200.0
        assert stats["min_duration_ms"] == 100.0
        assert stats["max_duration_ms"] == 300.0

    def test_time_profiler_statistics_empty(self):
        """✅ Test TimeProfiler statistics when empty."""
        profiler = TimeProfiler()
        
        stats = profiler.get_statistics()
        
        assert "avg_duration_ms" not in stats
        assert stats["total_count"] == 0

    def test_count_profiler_increment(self):
        """✅ Test CountProfiler increment."""
        profiler = CountProfiler()
        
        profiler.increment("api_calls")
        profiler.increment("api_calls")
        profiler.increment("db_queries")
        
        assert profiler.sample_count == 3
        assert profiler.total_count == 3

    def test_count_profiler_statistics(self):
        """✅ Test CountProfiler statistics by category."""
        profiler = CountProfiler()
        
        profiler.increment("api_calls")
        profiler.increment("api_calls")
        profiler.increment("db_queries")
        
        stats = profiler.get_statistics()
        
        assert stats["categories"]["api_calls"] == 2
        assert stats["categories"]["db_queries"] == 1


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""

    def test_error_handler_with_retry(self):
        """✅ Test combining error handler with retry decorator."""
        handler = ErrorHandler("integration_test")
        
        attempt = [0]
        
        @retry_on_failure(max_retries=2, delay=0.01, log_retry=False)
        def unstable_operation():
            attempt[0] += 1
            if attempt[0] < 2:
                raise ValueError("Temporary failure")
            return "SUCCESS"
        
        result = unstable_operation()
        
        assert result == "SUCCESS"
        assert attempt[0] == 2

    def test_profiler_with_error_handling(self):
        """✅ Test profiler with error handling."""
        profiler = TimeProfiler()
        
        @safe_execute(default_return=None, log_error=False)
        def timed_operation():
            start = time.time()
            # Simulate work
            time.sleep(0.01)
            duration = (time.time() - start) * 1000
            profiler.record_duration(duration, "test_op")
            return "SUCCESS"
        
        result = timed_operation()
        
        assert result == "SUCCESS"
        assert profiler.sample_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
