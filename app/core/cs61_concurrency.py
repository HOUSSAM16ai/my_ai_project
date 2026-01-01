"""
CS61 Concurrency Manager | مدير التزامن
=========================================

Thread-safe operations and concurrency primitives following CS61 principles:
- Thread synchronization
- Race condition prevention
- Async/await patterns
- Deadlock prevention

أدوات التزامن وفق مبادئ CS61
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from typing import Any, Callable, TypeVar, Iterator, ParamSpec

logger = logging.getLogger(__name__)

T = TypeVar('T')
P = ParamSpec('P')

# ==============================================================================
# CS61: Thread-Safe Counter (عداد آمن للخيوط)
# ==============================================================================

class ThreadSafeCounter:
    """
    عداد آمن للخيوط (Thread-safe counter).
    
    CS61 Principle: Mutual exclusion using locks.
    Prevents race conditions in concurrent environments.
    
    Example:
        counter = ThreadSafeCounter()
        counter.increment()  # Thread-safe
        value = counter.value  # Thread-safe read
    """
    
    def __init__(self, initial_value: int = 0):
        """
        Args:
            initial_value: Starting value
        """
        self._value = initial_value
        self._lock = threading.Lock()
    
    def increment(self, delta: int = 1) -> int:
        """
        زيادة العداد (Increment counter atomically).
        
        Args:
            delta: Amount to increment by
            
        Returns:
            New value after increment
        """
        with self._lock:
            self._value += delta
            return self._value
    
    def decrement(self, delta: int = 1) -> int:
        """
        إنقاص العداد (Decrement counter atomically).
        
        Args:
            delta: Amount to decrement by
            
        Returns:
            New value after decrement
        """
        with self._lock:
            self._value -= delta
            return self._value
    
    @property
    def value(self) -> int:
        """القيمة الحالية (Get current value thread-safely)."""
        with self._lock:
            return self._value
    
    def reset(self) -> None:
        """إعادة تعيين العداد (Reset counter to zero)."""
        with self._lock:
            self._value = 0


# ==============================================================================
# CS61: Rate Limiter (محدد المعدل)
# ==============================================================================

@dataclass
class RateLimitInfo:
    """معلومات حد المعدل (Rate limit information)."""
    requests: int
    window_start: float
    limit: int
    window_seconds: float
    
    @property
    def remaining(self) -> int:
        """الطلبات المتبقية (Remaining requests)."""
        return max(0, self.limit - self.requests)
    
    @property
    def is_exceeded(self) -> bool:
        """هل تم تجاوز الحد؟ (Is limit exceeded?)"""
        return self.requests >= self.limit


class ThreadSafeRateLimiter:
    """
    محدد معدل آمن للخيوط (Thread-safe rate limiter).
    
    CS61 Principle: Thread synchronization with sliding window.
    Prevents resource exhaustion and DoS attacks.
    
    Example:
        limiter = ThreadSafeRateLimiter(requests_per_second=10)
        if limiter.allow_request('user_123'):
            # Process request
            pass
    """
    
    def __init__(self, requests_per_window: int = 100, window_seconds: float = 60.0):
        """
        Args:
            requests_per_window: Max requests per window
            window_seconds: Window duration in seconds
        """
        self._limit = requests_per_window
        self._window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.RLock()  # Reentrant lock
    
    def allow_request(self, key: str) -> bool:
        """
        التحقق من السماح بالطلب (Check if request is allowed).
        
        Args:
            key: Identifier for rate limiting (e.g., user_id, ip_address)
            
        Returns:
            True if request allowed, False if rate limit exceeded
        """
        current_time = time.time()
        
        with self._lock:
            # Clean old requests outside window
            cutoff_time = current_time - self._window_seconds
            self._requests[key] = [
                req_time for req_time in self._requests[key]
                if req_time > cutoff_time
            ]
            
            # Check limit
            if len(self._requests[key]) >= self._limit:
                return False
            
            # Record request
            self._requests[key].append(current_time)
            return True
    
    def get_info(self, key: str) -> RateLimitInfo:
        """
        الحصول على معلومات الحد (Get rate limit info).
        
        Args:
            key: Identifier
            
        Returns:
            RateLimitInfo object
        """
        current_time = time.time()
        
        with self._lock:
            requests = self._requests.get(key, [])
            cutoff_time = current_time - self._window_seconds
            
            # Count requests in current window
            active_requests = sum(1 for t in requests if t > cutoff_time)
            
            window_start = min(requests) if requests else current_time
            
            return RateLimitInfo(
                requests=active_requests,
                window_start=window_start,
                limit=self._limit,
                window_seconds=self._window_seconds
            )
    
    def reset(self, key: str | None = None) -> None:
        """
        إعادة تعيين الحد (Reset rate limit).
        
        Args:
            key: Specific key to reset, or None to reset all
        """
        with self._lock:
            if key is None:
                self._requests.clear()
            else:
                self._requests.pop(key, None)


# ==============================================================================
# CS61: Async Lock Manager (مدير الأقفال اللاتزامنية)
# ==============================================================================

class AsyncLockManager:
    """
    مدير الأقفال اللاتزامنية (Async lock manager).
    
    CS61 Principle: Non-blocking synchronization for async operations.
    Prevents race conditions in async/await code.
    
    Example:
        manager = AsyncLockManager()
        async with manager.acquire('resource_id'):
            # Critical section
            await modify_resource()
    """
    
    def __init__(self):
        """Initialize with lock registry."""
        self._locks: dict[str, asyncio.Lock] = {}
        self._sync_lock = threading.Lock()
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """الحصول على قفل (Get or create lock for key)."""
        with self._sync_lock:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]
    
    @asynccontextmanager
    async def acquire(self, key: str) -> Iterator[None]:
        """
        الحصول على قفل لاتزامني (Acquire async lock).
        
        Args:
            key: Lock identifier
            
        Example:
            async with manager.acquire('user_123'):
                # Only one coroutine can execute this at a time
                await update_user()
        """
        lock = self._get_lock(key)
        
        try:
            await lock.acquire()
            yield
        finally:
            lock.release()
    
    def is_locked(self, key: str) -> bool:
        """
        هل القفل مقفل؟ (Check if lock is currently held).
        
        Args:
            key: Lock identifier
            
        Returns:
            True if locked, False otherwise
        """
        with self._sync_lock:
            if key not in self._locks:
                return False
            return self._locks[key].locked()


# ==============================================================================
# CS61: Semaphore Pool (مجمِّع السيمافور)
# ==============================================================================

class SemaphorePool:
    """
    مجمِّع السيمافور (Semaphore-based resource pool).
    
    CS61 Principle: Limit concurrent access to resources.
    Useful for controlling parallelism and preventing overload.
    
    Example:
        pool = SemaphorePool(max_concurrent=5)
        async with pool.acquire():
            # At most 5 coroutines execute this simultaneously
            await expensive_operation()
    """
    
    def __init__(self, max_concurrent: int = 10):
        """
        Args:
            max_concurrent: Maximum concurrent operations
        """
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be positive")
        
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._max_concurrent = max_concurrent
        self._active_count = ThreadSafeCounter()
    
    @asynccontextmanager
    async def acquire(self) -> Iterator[None]:
        """
        الحصول على مورد (Acquire resource from pool).
        
        Blocks if pool is full until a slot becomes available.
        """
        async with self._semaphore:
            self._active_count.increment()
            try:
                yield
            finally:
                self._active_count.decrement()
    
    @property
    def active_count(self) -> int:
        """عدد العمليات النشطة (Number of active operations)."""
        return self._active_count.value
    
    @property
    def available_count(self) -> int:
        """عدد الفتحات المتاحة (Number of available slots)."""
        return self._max_concurrent - self.active_count


# ==============================================================================
# CS61: Deadlock Prevention (منع الجمود)
# ==============================================================================

class TimeoutLock:
    """
    قفل مع مهلة زمنية (Lock with timeout for deadlock prevention).
    
    CS61 Principle: Timeout-based deadlock prevention.
    If lock cannot be acquired within timeout, raises exception.
    
    Example:
        lock = TimeoutLock(timeout_seconds=5.0)
        try:
            with lock.acquire():
                # Critical section
                pass
        except TimeoutError:
            # Handle timeout
            pass
    """
    
    def __init__(self, timeout_seconds: float = 5.0):
        """
        Args:
            timeout_seconds: Maximum wait time for lock
        """
        self._lock = threading.Lock()
        self._timeout = timeout_seconds
    
    @contextmanager
    def acquire(self) -> Iterator[None]:
        """
        الحصول على القفل (Acquire lock with timeout).
        
        Raises:
            TimeoutError: If lock cannot be acquired within timeout
        """
        acquired = self._lock.acquire(timeout=self._timeout)
        
        if not acquired:
            raise TimeoutError(
                f"Failed to acquire lock within {self._timeout} seconds"
            )
        
        try:
            yield
        finally:
            self._lock.release()


# ==============================================================================
# CS61: Async Queue with Backpressure (طابور لاتزامني مع ضغط عكسي)
# ==============================================================================

class BoundedAsyncQueue:
    """
    طابور لاتزامني محدود الحجم (Bounded async queue with backpressure).
    
    CS61 Principle: Bounded queues prevent memory exhaustion.
    Producers block when queue is full (backpressure).
    
    Example:
        queue = BoundedAsyncQueue[str](maxsize=100)
        await queue.put("item")
        item = await queue.get()
    """
    
    def __init__(self, maxsize: int = 100):
        """
        Args:
            maxsize: Maximum queue size
        """
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._maxsize = maxsize
    
    async def put(self, item: Any) -> None:
        """
        إضافة عنصر (Put item in queue).
        
        Blocks if queue is full (backpressure).
        """
        await self._queue.put(item)
    
    async def get(self) -> Any:
        """
        الحصول على عنصر (Get item from queue).
        
        Blocks if queue is empty.
        """
        return await self._queue.get()
    
    def task_done(self) -> None:
        """إشارة إتمام المهمة (Signal task completion)."""
        self._queue.task_done()
    
    async def join(self) -> None:
        """انتظار إفراغ الطابور (Wait for queue to be empty)."""
        await self._queue.join()
    
    def qsize(self) -> int:
        """حجم الطابور (Current queue size)."""
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """هل الطابور فارغ؟ (Is queue empty?)"""
        return self._queue.empty()
    
    def full(self) -> bool:
        """هل الطابور ممتلئ؟ (Is queue full?)"""
        return self._queue.full()
    
    @property
    def maxsize(self) -> int:
        """الحد الأقصى للحجم (Maximum size)."""
        return self._maxsize


# ==============================================================================
# CS61: Worker Pool (مجمِّع العمال)
# ==============================================================================

class AsyncWorkerPool:
    """
    مجمِّع عمال لاتزامني (Async worker pool).
    
    CS61 Principle: Fixed number of workers for controlled concurrency.
    Useful for processing tasks with limited parallelism.
    
    Example:
        pool = AsyncWorkerPool(num_workers=5)
        await pool.start()
        await pool.submit(process_task, item)
        await pool.shutdown()
    """
    
    def __init__(self, num_workers: int = 10):
        """
        Args:
            num_workers: Number of worker coroutines
        """
        self._num_workers = num_workers
        self._queue = BoundedAsyncQueue(maxsize=1000)
        self._workers: list[asyncio.Task] = []
        self._running = False
    
    async def _worker(self) -> None:
        """عامل (Worker coroutine)."""
        while self._running:
            try:
                # Get task with timeout to check _running periodically
                task = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0
                )
                
                func, args, kwargs = task
                
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Worker task failed: {e}")
                finally:
                    self._queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    async def start(self) -> None:
        """بدء مجمِّع العمال (Start worker pool)."""
        if self._running:
            return
        
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker())
            for _ in range(self._num_workers)
        ]
        
        logger.info(f"Started worker pool with {self._num_workers} workers")
    
    async def submit(
        self,
        func: Callable[P, asyncio.Future[T]],
        *args: P.args,
        **kwargs: P.kwargs
    ) -> None:
        """
        إرسال مهمة (Submit task to pool).
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        if not self._running:
            raise RuntimeError("Worker pool not started")
        
        await self._queue.put((func, args, kwargs))
    
    async def shutdown(self, wait: bool = True) -> None:
        """
        إيقاف مجمِّع العمال (Shutdown worker pool).
        
        Args:
            wait: If True, wait for all tasks to complete
        """
        if not self._running:
            return
        
        if wait:
            await self._queue.join()
        
        self._running = False
        
        # Cancel workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        logger.info("Worker pool shutdown complete")


# ==============================================================================
# Exports
# ==============================================================================

__all__ = [
    'ThreadSafeCounter',
    'ThreadSafeRateLimiter',
    'RateLimitInfo',
    'AsyncLockManager',
    'SemaphorePool',
    'TimeoutLock',
    'BoundedAsyncQueue',
    'AsyncWorkerPool',
]
