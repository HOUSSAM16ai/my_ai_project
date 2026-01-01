"""
Tests for CS61 Concurrency | اختبارات التزامن
============================================

Complete test coverage for cs61_concurrency module.
هدف: تغطية اختبارات 100%
"""
import asyncio
import time
import threading
import pytest
from app.core.cs61_concurrency import (
    ThreadSafeCounter,
    ThreadSafeRateLimiter,
    RateLimitInfo,
    AsyncLockManager,
    SemaphorePool,
    TimeoutLock,
    BoundedAsyncQueue,
    AsyncWorkerPool,
)


# ==============================================================================
# Test ThreadSafeCounter
# ==============================================================================

class TestThreadSafeCounter:
    """اختبارات العداد الآمن للخيوط"""
    
    def test_initialization(self):
        """Test counter initialization."""
        counter = ThreadSafeCounter()
        assert counter.value == 0
        
        counter2 = ThreadSafeCounter(initial_value=10)
        assert counter2.value == 10
    
    def test_increment(self):
        """Test increment operation."""
        counter = ThreadSafeCounter()
        
        result = counter.increment()
        assert result == 1
        assert counter.value == 1
        
        result = counter.increment(delta=5)
        assert result == 6
        assert counter.value == 6
    
    def test_decrement(self):
        """Test decrement operation."""
        counter = ThreadSafeCounter(initial_value=10)
        
        result = counter.decrement()
        assert result == 9
        assert counter.value == 9
        
        result = counter.decrement(delta=5)
        assert result == 4
        assert counter.value == 4
    
    def test_reset(self):
        """Test reset operation."""
        counter = ThreadSafeCounter(initial_value=100)
        counter.increment(50)
        
        assert counter.value == 150
        
        counter.reset()
        assert counter.value == 0
    
    def test_thread_safety(self):
        """Test thread safety with concurrent increments."""
        counter = ThreadSafeCounter()
        num_threads = 10
        increments_per_thread = 100
        
        def increment_many():
            for _ in range(increments_per_thread):
                counter.increment()
        
        threads = [
            threading.Thread(target=increment_many)
            for _ in range(num_threads)
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should be exactly num_threads * increments_per_thread
        expected = num_threads * increments_per_thread
        assert counter.value == expected


# ==============================================================================
# Test ThreadSafeRateLimiter
# ==============================================================================

class TestThreadSafeRateLimiter:
    """اختبارات محدد المعدل الآمن"""
    
    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = ThreadSafeRateLimiter(requests_per_window=10, window_seconds=60)
        
        info = limiter.get_info('test_key')
        assert info.requests == 0
        assert info.limit == 10
        assert info.window_seconds == 60
    
    def test_allow_request_basic(self):
        """Test basic request allowing."""
        limiter = ThreadSafeRateLimiter(requests_per_window=3, window_seconds=60)
        
        # First 3 should be allowed
        assert limiter.allow_request('user_1') is True
        assert limiter.allow_request('user_1') is True
        assert limiter.allow_request('user_1') is True
        
        # 4th should be denied
        assert limiter.allow_request('user_1') is False
    
    def test_allow_request_different_keys(self):
        """Test that different keys have independent limits."""
        limiter = ThreadSafeRateLimiter(requests_per_window=2, window_seconds=60)
        
        assert limiter.allow_request('user_1') is True
        assert limiter.allow_request('user_1') is True
        assert limiter.allow_request('user_1') is False
        
        # user_2 should have its own limit
        assert limiter.allow_request('user_2') is True
        assert limiter.allow_request('user_2') is True
        assert limiter.allow_request('user_2') is False
    
    def test_sliding_window(self):
        """Test sliding window behavior."""
        limiter = ThreadSafeRateLimiter(requests_per_window=2, window_seconds=0.1)
        
        # Use up limit
        assert limiter.allow_request('user_1') is True
        assert limiter.allow_request('user_1') is True
        assert limiter.allow_request('user_1') is False
        
        # Wait for window to slide
        time.sleep(0.15)
        
        # Should be allowed again
        assert limiter.allow_request('user_1') is True
    
    def test_get_info(self):
        """Test getting rate limit info."""
        limiter = ThreadSafeRateLimiter(requests_per_window=5, window_seconds=60)
        
        limiter.allow_request('user_1')
        limiter.allow_request('user_1')
        
        info = limiter.get_info('user_1')
        
        assert info.requests == 2
        assert info.limit == 5
        assert info.remaining == 3
        assert not info.is_exceeded
        
        # Use up remaining
        limiter.allow_request('user_1')
        limiter.allow_request('user_1')
        limiter.allow_request('user_1')
        
        info = limiter.get_info('user_1')
        assert info.is_exceeded
        assert info.remaining == 0
    
    def test_reset(self):
        """Test resetting rate limit."""
        limiter = ThreadSafeRateLimiter(requests_per_window=2, window_seconds=60)
        
        limiter.allow_request('user_1')
        limiter.allow_request('user_1')
        assert limiter.allow_request('user_1') is False
        
        # Reset specific key
        limiter.reset('user_1')
        assert limiter.allow_request('user_1') is True
    
    def test_reset_all(self):
        """Test resetting all rate limits."""
        limiter = ThreadSafeRateLimiter(requests_per_window=1, window_seconds=60)
        
        limiter.allow_request('user_1')
        limiter.allow_request('user_2')
        
        assert limiter.allow_request('user_1') is False
        assert limiter.allow_request('user_2') is False
        
        # Reset all
        limiter.reset()
        
        assert limiter.allow_request('user_1') is True
        assert limiter.allow_request('user_2') is True


# ==============================================================================
# Test AsyncLockManager
# ==============================================================================

class TestAsyncLockManager:
    """اختبارات مدير الأقفال اللاتزامنية"""
    
    @pytest.mark.asyncio
    async def test_acquire_basic(self):
        """Test basic lock acquisition."""
        manager = AsyncLockManager()
        
        async with manager.acquire('resource_1'):
            # Inside critical section
            assert manager.is_locked('resource_1')
        
        # Lock released
        assert not manager.is_locked('resource_1')
    
    @pytest.mark.asyncio
    async def test_mutual_exclusion(self):
        """Test mutual exclusion."""
        manager = AsyncLockManager()
        counter = {'value': 0}
        
        async def increment():
            async with manager.acquire('counter'):
                temp = counter['value']
                await asyncio.sleep(0.001)  # Simulate work
                counter['value'] = temp + 1
        
        # Run concurrently
        await asyncio.gather(*[increment() for _ in range(10)])
        
        # Should be exactly 10 (no race condition)
        assert counter['value'] == 10
    
    @pytest.mark.asyncio
    async def test_different_locks(self):
        """Test that different locks are independent."""
        manager = AsyncLockManager()
        
        async def task1():
            async with manager.acquire('lock_1'):
                await asyncio.sleep(0.1)
                return 1
        
        async def task2():
            async with manager.acquire('lock_2'):
                await asyncio.sleep(0.1)
                return 2
        
        # Should run concurrently
        start = time.time()
        results = await asyncio.gather(task1(), task2())
        elapsed = time.time() - start
        
        assert results == [1, 2]
        assert elapsed < 0.15  # Should be ~0.1, not 0.2


# ==============================================================================
# Test SemaphorePool
# ==============================================================================

class TestSemaphorePool:
    """اختبارات مجمِّع السيمافور"""
    
    def test_initialization(self):
        """Test pool initialization."""
        pool = SemaphorePool(max_concurrent=5)
        
        assert pool.active_count == 0
        assert pool.available_count == 5
    
    def test_initialization_invalid(self):
        """Test invalid initialization."""
        with pytest.raises(ValueError, match="max_concurrent must be positive"):
            SemaphorePool(max_concurrent=0)
    
    @pytest.mark.asyncio
    async def test_acquire_basic(self):
        """Test basic acquire."""
        pool = SemaphorePool(max_concurrent=3)
        
        async with pool.acquire():
            assert pool.active_count == 1
            assert pool.available_count == 2
        
        assert pool.active_count == 0
        assert pool.available_count == 3
    
    @pytest.mark.asyncio
    async def test_concurrency_limit(self):
        """Test that pool limits concurrency."""
        pool = SemaphorePool(max_concurrent=3)
        max_concurrent = {'value': 0}
        
        async def task():
            async with pool.acquire():
                current = pool.active_count
                max_concurrent['value'] = max(max_concurrent['value'], current)
                await asyncio.sleep(0.01)
        
        # Try to run 10 tasks concurrently
        await asyncio.gather(*[task() for _ in range(10)])
        
        # Max concurrent should be 3
        assert max_concurrent['value'] == 3


# ==============================================================================
# Test TimeoutLock
# ==============================================================================

class TestTimeoutLock:
    """اختبارات قفل المهلة الزمنية"""
    
    def test_acquire_immediate(self):
        """Test acquiring available lock."""
        lock = TimeoutLock(timeout_seconds=1.0)
        
        with lock.acquire():
            # Successfully acquired
            pass
    
    def test_timeout_on_blocked_lock(self):
        """Test timeout when lock is held."""
        lock = TimeoutLock(timeout_seconds=0.1)
        
        def holder():
            with lock.acquire():
                time.sleep(1.0)  # Hold for a while
        
        # Start holder thread
        thread = threading.Thread(target=holder)
        thread.start()
        
        time.sleep(0.05)  # Let holder acquire
        
        # Try to acquire (should timeout)
        with pytest.raises(TimeoutError, match="Failed to acquire lock"):
            with lock.acquire():
                pass
        
        thread.join()


# ==============================================================================
# Test BoundedAsyncQueue
# ==============================================================================

class TestBoundedAsyncQueue:
    """اختبارات الطابور اللاتزامني المحدود"""
    
    @pytest.mark.asyncio
    async def test_put_and_get(self):
        """Test basic put and get."""
        queue = BoundedAsyncQueue(maxsize=10)
        
        await queue.put('item1')
        await queue.put('item2')
        
        assert queue.qsize() == 2
        
        item1 = await queue.get()
        item2 = await queue.get()
        
        assert item1 == 'item1'
        assert item2 == 'item2'
        assert queue.empty()
    
    @pytest.mark.asyncio
    async def test_backpressure(self):
        """Test backpressure when queue is full."""
        queue = BoundedAsyncQueue(maxsize=2)
        
        await queue.put(1)
        await queue.put(2)
        
        assert queue.full()
        
        # Try to put 3rd item (should block)
        put_task = asyncio.create_task(queue.put(3))
        
        await asyncio.sleep(0.01)
        assert not put_task.done()  # Still blocked
        
        # Get one item to make space
        await queue.get()
        
        await asyncio.sleep(0.01)
        assert put_task.done()  # Now completed
    
    @pytest.mark.asyncio
    async def test_task_done_and_join(self):
        """Test task_done and join."""
        queue = BoundedAsyncQueue(maxsize=10)
        
        # Add items
        for i in range(5):
            await queue.put(i)
        
        async def consumer():
            while not queue.empty():
                await queue.get()
                queue.task_done()
        
        consumer_task = asyncio.create_task(consumer())
        
        await queue.join()  # Wait for all tasks to be done
        await consumer_task


# ==============================================================================
# Test AsyncWorkerPool
# ==============================================================================

class TestAsyncWorkerPool:
    """اختبارات مجمِّع العمال اللاتزامني"""
    
    @pytest.mark.asyncio
    async def test_start_and_shutdown(self):
        """Test starting and shutting down pool."""
        pool = AsyncWorkerPool(num_workers=3)
        
        await pool.start()
        await asyncio.sleep(0.1)
        
        await pool.shutdown(wait=False)
    
    @pytest.mark.asyncio
    async def test_submit_tasks(self):
        """Test submitting and executing tasks."""
        pool = AsyncWorkerPool(num_workers=3)
        results = []
        
        async def task(value: int):
            await asyncio.sleep(0.01)
            results.append(value * 2)
        
        await pool.start()
        
        # Submit tasks
        for i in range(10):
            await pool.submit(task, i)
        
        await pool.shutdown(wait=True)
        
        # All tasks should be completed
        assert len(results) == 10
        assert sorted(results) == [i * 2 for i in range(10)]
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test that worker handles errors gracefully."""
        pool = AsyncWorkerPool(num_workers=2)
        success_count = {'value': 0}
        
        async def failing_task():
            raise ValueError("Test error")
        
        async def success_task():
            await asyncio.sleep(0.01)
            success_count['value'] += 1
        
        await pool.start()
        
        # Submit mix of failing and successful tasks
        await pool.submit(failing_task)
        await pool.submit(success_task)
        await pool.submit(failing_task)
        await pool.submit(success_task)
        
        await pool.shutdown(wait=True)
        
        # Successful tasks should complete despite failures
        assert success_count['value'] == 2


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """اختبارات التكامل"""
    
    @pytest.mark.asyncio
    async def test_producer_consumer_pattern(self):
        """Test producer-consumer pattern."""
        queue = BoundedAsyncQueue(maxsize=10)
        produced = []
        consumed = []
        
        async def producer():
            for i in range(20):
                await queue.put(i)
                produced.append(i)
                await asyncio.sleep(0.001)
        
        async def consumer():
            for _ in range(20):
                item = await queue.get()
                consumed.append(item)
                queue.task_done()
                await asyncio.sleep(0.001)
        
        await asyncio.gather(producer(), consumer())
        await queue.join()
        
        assert len(produced) == 20
        assert len(consumed) == 20
        assert sorted(consumed) == list(range(20))
    
    @pytest.mark.asyncio
    async def test_rate_limited_worker_pool(self):
        """Test combining rate limiter with worker pool."""
        limiter = ThreadSafeRateLimiter(requests_per_window=5, window_seconds=0.1)
        pool = AsyncWorkerPool(num_workers=3)
        
        executed = {'count': 0}
        
        async def rate_limited_task(task_id: int):
            if limiter.allow_request('worker_pool'):
                executed['count'] += 1
                await asyncio.sleep(0.01)
        
        await pool.start()
        
        # Submit 10 tasks
        for i in range(10):
            await pool.submit(rate_limited_task, i)
        
        await pool.shutdown(wait=True)
        
        # Only 5 should have executed (rate limit)
        assert executed['count'] == 5


# ==============================================================================
# Edge Cases
# ==============================================================================

class TestEdgeCases:
    """اختبارات الحالات الحدية"""
    
    def test_counter_negative_values(self):
        """Test counter with negative values."""
        counter = ThreadSafeCounter(initial_value=10)
        counter.decrement(20)
        
        assert counter.value == -10
        
        counter.increment(30)
        assert counter.value == 20
    
    @pytest.mark.asyncio
    async def test_semaphore_pool_size_one(self):
        """Test semaphore pool with size 1."""
        pool = SemaphorePool(max_concurrent=1)
        
        async def task():
            async with pool.acquire():
                await asyncio.sleep(0.01)
        
        start = time.time()
        await asyncio.gather(task(), task(), task())
        elapsed = time.time() - start
        
        # Should be sequential (~0.03s)
        assert elapsed >= 0.03
    
    @pytest.mark.asyncio
    async def test_queue_maxsize_one(self):
        """Test queue with maxsize 1."""
        queue = BoundedAsyncQueue(maxsize=1)
        
        await queue.put('item')
        assert queue.full()
        
        item = await queue.get()
        assert item == 'item'
        assert queue.empty()
