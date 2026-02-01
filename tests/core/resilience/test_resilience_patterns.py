import asyncio

import pytest

from app.core.resilience.bulkhead import Bulkhead, BulkheadFullError
from app.core.resilience.fallback import FallbackPolicy
from app.core.resilience.timeout import TimeoutError, TimeoutPolicy


# --- Bulkhead Tests ---
@pytest.mark.asyncio
async def test_bulkhead_concurrency():
    # max_queue tracks total requests (running + queued)
    # 2 running + 1 queued = 3 capacity
    bulkhead = Bulkhead(max_concurrent=2, max_queue=3)

    # Event to keep tasks holding the semaphore
    hold_event = asyncio.Event()

    async def blocking_task():
        await hold_event.wait()
        return "ok"

    # Start 2 tasks (consume implementation semaphore)
    t1 = asyncio.create_task(bulkhead.execute(blocking_task))
    t2 = asyncio.create_task(bulkhead.execute(blocking_task))

    # Give them a moment to start and acquire semaphore
    await asyncio.sleep(0.01)

    # 3rd task (files queue)
    t3 = asyncio.create_task(bulkhead.execute(blocking_task))
    await asyncio.sleep(0.01)

    # 4th task (should fail immediately)
    with pytest.raises(BulkheadFullError):
        await bulkhead.execute(blocking_task)

    # Release tasks
    hold_event.set()

    results = await asyncio.gather(t1, t2, t3)
    assert results == ["ok", "ok", "ok"]


# --- Timeout Tests ---
@pytest.mark.asyncio
async def test_timeout_success():
    policy = TimeoutPolicy(timeout_seconds=0.1)

    async def fast():
        return "ok"

    assert await policy.execute(fast) == "ok"


@pytest.mark.asyncio
async def test_timeout_failure():
    policy = TimeoutPolicy(timeout_seconds=0.01)

    async def slow():
        await asyncio.sleep(0.05)
        return "ok"

    with pytest.raises(TimeoutError):
        await policy.execute(slow)


# --- Fallback Tests ---
@pytest.mark.asyncio
async def test_fallback_triggered():
    async def backup():
        return "backup"

    policy = FallbackPolicy(fallback_func=backup)

    async def failing():
        raise ValueError("oops")

    assert await policy.execute(failing) == "backup"


@pytest.mark.asyncio
async def test_fallback_no_handler():
    policy = FallbackPolicy(fallback_func=None)

    async def failing():
        raise ValueError("oops")

    with pytest.raises(ValueError):
        await policy.execute(failing)
