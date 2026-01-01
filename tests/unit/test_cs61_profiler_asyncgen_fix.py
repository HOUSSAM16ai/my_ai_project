"""
اختبار شامل لإصلاح async generator في cs61_profiler
Tests for async generator support in CS61 profiler
"""
import pytest
from collections.abc import AsyncGenerator

from app.core.cs61_profiler import (
    profile_async,
    profile_sync,
    get_performance_stats,
    reset_performance_stats,
)


@pytest.mark.unit
def test_profile_sync_basic():
    """Test sync function profiling."""
    reset_performance_stats()
    
    @profile_sync
    def simple_func(x: int) -> int:
        return x * 2
    
    result = simple_func(5)
    assert result == 10
    
    stats = get_performance_stats()
    assert "simple_func" in stats
    assert stats["simple_func"]["calls"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_profile_async_coroutine():
    """Test async coroutine profiling (normal async def without yield)."""
    reset_performance_stats()
    
    @profile_async
    async def async_func(x: int) -> int:
        return x * 3
    
    result = await async_func(7)
    assert result == 21
    
    stats = get_performance_stats()
    assert "async_func" in stats
    assert stats["async_func"]["calls"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_profile_async_generator():
    """
    Test async generator profiling (async def with yield).
    This is the critical test for the bug fix!
    """
    reset_performance_stats()
    
    @profile_async
    async def async_gen_func(n: int) -> AsyncGenerator[int, None]:
        for i in range(n):
            yield i
    
    # استهلاك الـ async generator
    results = []
    async for item in async_gen_func(5):
        results.append(item)
    
    assert results == [0, 1, 2, 3, 4]
    
    # التحقق من تسجيل الإحصائيات
    stats = get_performance_stats()
    assert "async_gen_func" in stats
    assert stats["async_gen_func"]["calls"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_profile_async_generator_multiple_calls():
    """Test async generator with multiple calls."""
    reset_performance_stats()
    
    @profile_async
    async def data_stream() -> AsyncGenerator[str, None]:
        yield "first"
        yield "second"
        yield "third"
    
    # First call
    items1 = [item async for item in data_stream()]
    assert items1 == ["first", "second", "third"]
    
    # Second call
    items2 = [item async for item in data_stream()]
    assert items2 == ["first", "second", "third"]
    
    stats = get_performance_stats()
    assert "data_stream" in stats
    assert stats["data_stream"]["calls"] == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_profile_async_generator_with_exception():
    """Test async generator profiling with exception handling."""
    reset_performance_stats()
    
    @profile_async
    async def failing_gen() -> AsyncGenerator[int, None]:
        yield 1
        yield 2
        raise ValueError("Test error")
    
    # يجب أن يُسجل الإحصائيات حتى عند حدوث خطأ
    with pytest.raises(ValueError, match="Test error"):
        async for item in failing_gen():
            pass
    
    stats = get_performance_stats()
    assert "failing_gen" in stats
    assert stats["failing_gen"]["calls"] == 1


@pytest.mark.unit
@pytest.mark.asyncio
async def test_database_session_pattern():
    """
    Test the actual database session pattern (simulated).
    This mimics the get_db() function pattern.
    """
    reset_performance_stats()
    
    class FakeSession:
        def __init__(self):
            self.closed = False
        
        async def close(self):
            self.closed = True
    
    @profile_async
    async def get_db_simulation() -> AsyncGenerator[FakeSession, None]:
        """Simulates app.core.database.get_db()"""
        session = FakeSession()
        try:
            yield session
        finally:
            await session.close()
    
    # استخدام النمط المعتاد في FastAPI
    async for session in get_db_simulation():
        assert isinstance(session, FakeSession)
        assert not session.closed
    
    # التحقق من أن الجلسة أُغلقت
    assert session.closed
    
    # التحقق من تسجيل الإحصائيات
    stats = get_performance_stats()
    assert "get_db_simulation" in stats
    assert stats["get_db_simulation"]["calls"] == 1
