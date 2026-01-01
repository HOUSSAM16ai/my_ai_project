"""
CS61 Performance Profiler | أداة قياس الأداء
============================================

High-precision profiling utilities following CS61 principles:
- Memory tracking
- CPU profiling
- Cache analysis
- Concurrency monitoring

أدوات قياس الأداء عالية الدقة وفق مبادئ CS61
"""
from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar, ParamSpec

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')

# ==============================================================================
# CS61: Performance Metrics (مقاييس الأداء)
# ==============================================================================

@dataclass
class PerformanceStats:
    """
    مقاييس الأداء التفصيلية (Detailed Performance Metrics).
    
    CS61 Principles:
    - Memory efficiency: bounded deque (maxlen=100)
    - Cache locality: sequential data structure
    - Statistical analysis: P50, P95, P99 latencies
    """
    function_name: str
    call_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    
    # Bounded memory: keep last 100 measurements only
    latencies: deque[float] = field(default_factory=lambda: deque(maxlen=100))
    
    def record_call(self, duration_ms: float) -> None:
        """تسجيل مكالمة جديدة (Record new function call)."""
        self.call_count += 1
        self.total_time_ms += duration_ms
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)
        self.latencies.append(duration_ms)
    
    @property
    def avg_time_ms(self) -> float:
        """متوسط وقت التنفيذ (Average execution time)."""
        return self.total_time_ms / self.call_count if self.call_count > 0 else 0.0
    
    @property
    def p50_latency_ms(self) -> float:
        """الوسيط - P50 (Median latency)."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        return sorted_latencies[len(sorted_latencies) // 2]
    
    @property
    def p95_latency_ms(self) -> float:
        """النسبة المئوية 95 (95th percentile)."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    @property
    def p99_latency_ms(self) -> float:
        """النسبة المئوية 99 (99th percentile)."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def to_dict(self) -> dict[str, Any]:
        """تصدير كقاموس (Export as dictionary)."""
        return {
            'function': self.function_name,
            'calls': self.call_count,
            'total_ms': round(self.total_time_ms, 2),
            'avg_ms': round(self.avg_time_ms, 2),
            'min_ms': round(self.min_time_ms, 2),
            'max_ms': round(self.max_time_ms, 2),
            'p50_ms': round(self.p50_latency_ms, 2),
            'p95_ms': round(self.p95_latency_ms, 2),
            'p99_ms': round(self.p99_latency_ms, 2),
        }


# Global stats registry (thread-safe via GIL)
_performance_registry: dict[str, PerformanceStats] = defaultdict(
    lambda: PerformanceStats(function_name="unknown")
)


# ==============================================================================
# CS61: Profiling Decorators (مُزخرفات القياس)
# ==============================================================================

def profile_sync(func: Callable[P, T]) -> Callable[P, T]:
    """
    مُزخرف قياس الأداء للدوال المتزامنة (Profiler for synchronous functions).
    
    CS61 Principle: Minimal overhead, precise timing with perf_counter.
    
    Example:
        @profile_sync
        def expensive_computation(n: int) -> int:
            return sum(range(n))
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            stats = _performance_registry[func.__name__]
            stats.function_name = func.__name__
            stats.record_call(elapsed_ms)
            
            if elapsed_ms > 100:  # Log slow operations
                logger.warning(
                    f"⚠️ Slow operation: {func.__name__} took {elapsed_ms:.2f}ms"
                )
    
    return wrapper


def profile_async(func: Callable[P, asyncio.Future[T]]) -> Callable[P, asyncio.Future[T]]:
    """
    مُزخرف قياس الأداء للدوال اللاتزامنية (Profiler for async functions).
    
    CS61 Principle: Non-blocking profiling for async/await patterns.
    يدعم تلقائياً async generators (functions with yield).
    
    Example:
        @profile_async
        async def fetch_data(user_id: int) -> User:
            return await db.get(User, user_id)
        
        @profile_async
        async def get_db() -> AsyncGenerator[Session, None]:
            yield session  # Automatically handles generators!
    """
    # فحص ذكي: هل الدالة async generator؟
    if inspect.isasyncgenfunction(func):
        # معالجة خاصة للـ async generators (دوال بها yield)
        @functools.wraps(func)
        async def gen_wrapper(*args: P.args, **kwargs: P.kwargs):
            start = time.perf_counter()
            item_count = 0
            try:
                # استخدام async for بدلاً من await
                async for item in func(*args, **kwargs):
                    item_count += 1
                    yield item
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                stats = _performance_registry[func.__name__]
                stats.function_name = func.__name__
                stats.record_call(elapsed_ms)
                
                logger.debug(
                    f"🔄 Async generator {func.__name__}: "
                    f"{item_count} items in {elapsed_ms:.2f}ms"
                )
                
                if elapsed_ms > 100:  # Log slow operations
                    logger.warning(
                        f"⚠️ Slow async generator: {func.__name__} took {elapsed_ms:.2f}ms"
                    )
        
        return gen_wrapper
    
    # المعالجة الاعتيادية للـ coroutines
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            stats = _performance_registry[func.__name__]
            stats.function_name = func.__name__
            stats.record_call(elapsed_ms)
            
            if elapsed_ms > 100:  # Log slow operations
                logger.warning(
                    f"⚠️ Slow async operation: {func.__name__} took {elapsed_ms:.2f}ms"
                )
    
    return wrapper


# ==============================================================================
# CS61: Memory Profiling (قياس استخدام الذاكرة)
# ==============================================================================

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - memory profiling disabled")


def get_memory_usage() -> dict[str, float]:
    """
    قياس استخدام الذاكرة الحالي (Get current memory usage).
    
    CS61 Concepts:
    - RSS (Resident Set Size): Physical memory
    - VMS (Virtual Memory Size): Total memory including swap
    
    Returns:
        dict with memory metrics in MB
    """
    if not PSUTIL_AVAILABLE:
        return {'rss_mb': 0.0, 'vms_mb': 0.0, 'percent': 0.0}
    
    try:
        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            'rss_mb': mem_info.rss / (1024 * 1024),  # Physical memory
            'vms_mb': mem_info.vms / (1024 * 1024),  # Virtual memory
            'percent': process.memory_percent(),
        }
    except Exception as e:
        logger.error(f"Memory profiling error: {e}")
        return {'rss_mb': 0.0, 'vms_mb': 0.0, 'percent': 0.0}


def profile_memory(func: Callable[P, T]) -> Callable[P, T]:
    """
    مُزخرف قياس استخدام الذاكرة (Memory profiler decorator).
    
    CS61 Principle: Track memory allocation/deallocation.
    
    Example:
        @profile_memory
        def load_large_dataset() -> list[dict]:
            return [{'data': i} for i in range(1000000)]
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        mem_before = get_memory_usage()
        result = func(*args, **kwargs)
        mem_after = get_memory_usage()
        
        mem_delta = mem_after['rss_mb'] - mem_before['rss_mb']
        if abs(mem_delta) > 10:  # Log significant memory changes (>10MB)
            logger.info(
                f"💾 Memory change in {func.__name__}: "
                f"{mem_delta:+.2f}MB (RSS: {mem_after['rss_mb']:.2f}MB)"
            )
        
        return result
    
    return wrapper


# ==============================================================================
# CS61: Statistics & Reporting (الإحصائيات والتقارير)
# ==============================================================================

def get_performance_stats() -> dict[str, dict[str, Any]]:
    """
    الحصول على جميع إحصائيات الأداء (Get all performance statistics).
    
    Returns:
        Dictionary mapping function names to their stats
    """
    return {
        name: stats.to_dict()
        for name, stats in _performance_registry.items()
    }


def print_performance_report() -> None:
    """طباعة تقرير الأداء (Print performance report)."""
    stats = get_performance_stats()
    
    if not stats:
        print("No performance data collected yet.")
        return
    
    print("\n" + "=" * 80)
    print("CS61 PERFORMANCE REPORT | تقرير الأداء")
    print("=" * 80)
    
    # Sort by total time (most expensive first)
    sorted_stats = sorted(
        stats.items(),
        key=lambda x: x[1]['total_ms'],
        reverse=True
    )
    
    for func_name, data in sorted_stats:
        print(f"\n📊 {func_name}")
        print(f"   Calls: {data['calls']}")
        print(f"   Total: {data['total_ms']:.2f}ms")
        print(f"   Avg:   {data['avg_ms']:.2f}ms")
        print(f"   Range: [{data['min_ms']:.2f}ms - {data['max_ms']:.2f}ms]")
        print(f"   P50:   {data['p50_ms']:.2f}ms")
        print(f"   P95:   {data['p95_ms']:.2f}ms")
        print(f"   P99:   {data['p99_ms']:.2f}ms")
    
    print("\n" + "=" * 80)
    
    # Memory summary
    mem = get_memory_usage()
    print(f"\n💾 Current Memory Usage:")
    print(f"   RSS: {mem['rss_mb']:.2f}MB")
    print(f"   VMS: {mem['vms_mb']:.2f}MB")
    print(f"   Percent: {mem['percent']:.1f}%")
    print("=" * 80 + "\n")


def reset_performance_stats() -> None:
    """إعادة تعيين جميع الإحصائيات (Reset all statistics)."""
    _performance_registry.clear()
    logger.info("Performance statistics reset")


# ==============================================================================
# Exports
# ==============================================================================

__all__ = [
    'PerformanceStats',
    'profile_sync',
    'profile_async',
    'profile_memory',
    'get_memory_usage',
    'get_performance_stats',
    'print_performance_report',
    'reset_performance_stats',
]
