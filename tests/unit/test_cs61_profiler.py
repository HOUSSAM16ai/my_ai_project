"""
Tests for CS61 Profiler | اختبارات أداة القياس
=============================================

Complete test coverage for cs61_profiler module.
هدف: تغطية اختبارات 100%
"""
import asyncio
import time
import pytest
from app.core.cs61_profiler import (
    PerformanceStats,
    profile_sync,
    profile_async,
    profile_memory,
    get_memory_usage,
    get_performance_stats,
    print_performance_report,
    reset_performance_stats,
)


# ==============================================================================
# Test PerformanceStats
# ==============================================================================

class TestPerformanceStats:
    """اختبارات فئة PerformanceStats"""
    
    def test_initialization(self):
        """Test stats initialization."""
        stats = PerformanceStats(function_name="test_func")
        
        assert stats.function_name == "test_func"
        assert stats.call_count == 0
        assert stats.total_time_ms == 0.0
        assert stats.min_time_ms == float('inf')
        assert stats.max_time_ms == 0.0
        assert len(stats.latencies) == 0
    
    def test_record_call(self):
        """Test recording function calls."""
        stats = PerformanceStats(function_name="test_func")
        
        stats.record_call(10.0)
        assert stats.call_count == 1
        assert stats.total_time_ms == 10.0
        assert stats.min_time_ms == 10.0
        assert stats.max_time_ms == 10.0
        
        stats.record_call(20.0)
        assert stats.call_count == 2
        assert stats.total_time_ms == 30.0
        assert stats.min_time_ms == 10.0
        assert stats.max_time_ms == 20.0
    
    def test_avg_time_ms(self):
        """Test average time calculation."""
        stats = PerformanceStats(function_name="test_func")
        
        # Empty stats
        assert stats.avg_time_ms == 0.0
        
        # With data
        stats.record_call(10.0)
        stats.record_call(20.0)
        stats.record_call(30.0)
        assert stats.avg_time_ms == 20.0
    
    def test_percentile_latencies(self):
        """Test P50, P95, P99 calculations."""
        stats = PerformanceStats(function_name="test_func")
        
        # Empty stats
        assert stats.p50_latency_ms == 0.0
        assert stats.p95_latency_ms == 0.0
        assert stats.p99_latency_ms == 0.0
        
        # With data (1-100ms)
        for i in range(1, 101):
            stats.record_call(float(i))
        
        assert 45 <= stats.p50_latency_ms <= 55  # Around 50
        assert 90 <= stats.p95_latency_ms <= 100  # Around 95
        assert 95 <= stats.p99_latency_ms <= 100  # Around 99
    
    def test_bounded_latencies(self):
        """Test that latencies deque is bounded to 100."""
        stats = PerformanceStats(function_name="test_func")
        
        # Add 200 entries
        for i in range(200):
            stats.record_call(float(i))
        
        # Only last 100 should be kept
        assert len(stats.latencies) == 100
        assert stats.call_count == 200  # But count is accurate
    
    def test_to_dict(self):
        """Test dictionary export."""
        stats = PerformanceStats(function_name="test_func")
        stats.record_call(10.0)
        stats.record_call(20.0)
        
        result = stats.to_dict()
        
        assert result['function'] == "test_func"
        assert result['calls'] == 2
        assert result['total_ms'] == 30.0
        assert result['avg_ms'] == 15.0
        assert result['min_ms'] == 10.0
        assert result['max_ms'] == 20.0
        assert 'p50_ms' in result
        assert 'p95_ms' in result
        assert 'p99_ms' in result


# ==============================================================================
# Test Profiling Decorators
# ==============================================================================

class TestProfilingDecorators:
    """اختبارات مُزخرفات القياس"""
    
    def setup_method(self):
        """Reset stats before each test."""
        reset_performance_stats()
    
    def test_profile_sync_basic(self):
        """Test basic sync profiling."""
        @profile_sync
        def sample_function(x: int) -> int:
            time.sleep(0.01)  # 10ms
            return x * 2
        
        result = sample_function(5)
        
        assert result == 10
        
        stats = get_performance_stats()
        assert 'sample_function' in stats
        assert stats['sample_function']['calls'] == 1
        assert stats['sample_function']['avg_ms'] >= 10.0
    
    def test_profile_sync_multiple_calls(self):
        """Test sync profiling with multiple calls."""
        @profile_sync
        def fast_function(x: int) -> int:
            return x + 1
        
        for i in range(10):
            fast_function(i)
        
        stats = get_performance_stats()
        assert stats['fast_function']['calls'] == 10
    
    def test_profile_sync_with_exception(self):
        """Test that profiling works even with exceptions."""
        @profile_sync
        def failing_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Stats should still be recorded
        stats = get_performance_stats()
        assert 'failing_function' in stats
        assert stats['failing_function']['calls'] == 1
    
    @pytest.mark.asyncio
    async def test_profile_async_basic(self):
        """Test basic async profiling."""
        @profile_async
        async def async_sample(x: int) -> int:
            await asyncio.sleep(0.01)  # 10ms
            return x * 2
        
        result = await async_sample(5)
        
        assert result == 10
        
        stats = get_performance_stats()
        assert 'async_sample' in stats
        assert stats['async_sample']['calls'] == 1
        assert stats['async_sample']['avg_ms'] >= 10.0
    
    @pytest.mark.asyncio
    async def test_profile_async_concurrent(self):
        """Test async profiling with concurrent calls."""
        @profile_async
        async def async_task(x: int) -> int:
            await asyncio.sleep(0.001)
            return x * 2
        
        # Run 10 concurrent tasks
        results = await asyncio.gather(*[async_task(i) for i in range(10)])
        
        assert len(results) == 10
        
        stats = get_performance_stats()
        assert stats['async_task']['calls'] == 10
    
    @pytest.mark.asyncio
    async def test_profile_async_with_exception(self):
        """Test async profiling with exceptions."""
        @profile_async
        async def async_failing():
            await asyncio.sleep(0.001)
            raise ValueError("Async error")
        
        with pytest.raises(ValueError):
            await async_failing()
        
        stats = get_performance_stats()
        assert 'async_failing' in stats
        assert stats['async_failing']['calls'] == 1
    
    def test_profile_memory_basic(self):
        """Test memory profiling."""
        @profile_memory
        def memory_function():
            # Allocate some memory
            data = [i for i in range(1000)]
            return len(data)
        
        result = memory_function()
        assert result == 1000
    
    def test_profile_memory_large_allocation(self):
        """Test memory profiling with large allocation."""
        @profile_memory
        def large_allocation():
            # Allocate ~10MB
            data = [{'id': i, 'data': 'x' * 1000} for i in range(10000)]
            return len(data)
        
        result = large_allocation()
        assert result == 10000


# ==============================================================================
# Test Memory Utilities
# ==============================================================================

class TestMemoryUtilities:
    """اختبارات أدوات الذاكرة"""
    
    def test_get_memory_usage(self):
        """Test memory usage retrieval."""
        mem = get_memory_usage()
        
        assert isinstance(mem, dict)
        assert 'rss_mb' in mem
        assert 'vms_mb' in mem
        assert 'percent' in mem
        
        # All values should be non-negative
        assert mem['rss_mb'] >= 0
        assert mem['vms_mb'] >= 0
        assert mem['percent'] >= 0


# ==============================================================================
# Test Statistics & Reporting
# ==============================================================================

class TestStatisticsReporting:
    """اختبارات الإحصائيات والتقارير"""
    
    def setup_method(self):
        """Reset before each test."""
        reset_performance_stats()
    
    def test_get_performance_stats_empty(self):
        """Test getting stats when empty."""
        stats = get_performance_stats()
        assert isinstance(stats, dict)
        assert len(stats) == 0
    
    def test_get_performance_stats_with_data(self):
        """Test getting stats with recorded data."""
        @profile_sync
        def test_func():
            pass
        
        test_func()
        test_func()
        
        stats = get_performance_stats()
        assert 'test_func' in stats
        assert stats['test_func']['calls'] == 2
    
    def test_print_performance_report_empty(self, capsys):
        """Test printing report when empty."""
        print_performance_report()
        
        captured = capsys.readouterr()
        assert "No performance data" in captured.out
    
    def test_print_performance_report_with_data(self, capsys):
        """Test printing report with data."""
        @profile_sync
        def sample_func():
            time.sleep(0.001)
        
        sample_func()
        
        print_performance_report()
        
        captured = capsys.readouterr()
        assert "CS61 PERFORMANCE REPORT" in captured.out
        assert "sample_func" in captured.out
        assert "Calls:" in captured.out
        assert "Current Memory Usage" in captured.out
    
    def test_reset_performance_stats(self):
        """Test resetting statistics."""
        @profile_sync
        def test_func():
            pass
        
        test_func()
        
        stats_before = get_performance_stats()
        assert len(stats_before) > 0
        
        reset_performance_stats()
        
        stats_after = get_performance_stats()
        assert len(stats_after) == 0


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """اختبارات التكامل"""
    
    def setup_method(self):
        """Setup for integration tests."""
        reset_performance_stats()
    
    def test_full_workflow(self):
        """Test complete profiling workflow."""
        @profile_sync
        @profile_memory
        def complex_operation(n: int) -> list[int]:
            time.sleep(0.01)
            return [i * 2 for i in range(n)]
        
        # Run multiple times
        for i in range(5):
            result = complex_operation(100)
            assert len(result) == 100
        
        # Get stats
        stats = get_performance_stats()
        assert 'complex_operation' in stats
        assert stats['complex_operation']['calls'] == 5
        
        # Print report (should not crash)
        print_performance_report()
    
    @pytest.mark.asyncio
    async def test_mixed_sync_async(self):
        """Test mixing sync and async profiling."""
        @profile_sync
        def sync_task(x: int) -> int:
            return x * 2
        
        @profile_async
        async def async_task(x: int) -> int:
            await asyncio.sleep(0.001)
            return x * 3
        
        # Run both
        sync_result = sync_task(5)
        async_result = await async_task(5)
        
        assert sync_result == 10
        assert async_result == 15
        
        # Both should be tracked
        stats = get_performance_stats()
        assert 'sync_task' in stats
        assert 'async_task' in stats


# ==============================================================================
# Edge Cases
# ==============================================================================

class TestEdgeCases:
    """اختبارات الحالات الحدية"""
    
    def test_very_fast_function(self):
        """Test profiling very fast functions."""
        @profile_sync
        def instant_function():
            return 42
        
        result = instant_function()
        assert result == 42
        
        stats = get_performance_stats()
        assert 'instant_function' in stats
        assert stats['instant_function']['calls'] == 1
        # Time might be 0 or very small
        assert stats['instant_function']['avg_ms'] >= 0
    
    def test_function_with_args_and_kwargs(self):
        """Test profiling functions with various arguments."""
        @profile_sync
        def complex_signature(a: int, b: str, *args, **kwargs) -> dict:
            return {'a': a, 'b': b, 'args': args, 'kwargs': kwargs}
        
        result = complex_signature(1, "test", 3, 4, x=5, y=6)
        
        assert result['a'] == 1
        assert result['b'] == "test"
        assert result['args'] == (3, 4)
        assert result['kwargs'] == {'x': 5, 'y': 6}
        
        stats = get_performance_stats()
        assert 'complex_signature' in stats
    
    def test_recursive_function(self):
        """Test profiling recursive functions."""
        @profile_sync
        def fibonacci(n: int) -> int:
            if n <= 1:
                return n
            return fibonacci(n - 1) + fibonacci(n - 2)
        
        result = fibonacci(10)
        assert result == 55
        
        stats = get_performance_stats()
        # Each recursive call is tracked
        assert stats['fibonacci']['calls'] > 10
