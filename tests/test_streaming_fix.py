import asyncio
import contextlib

import pytest

from app.services.breakthrough_streaming import BreakthroughStreamingService


class MockGenerator:
    def __init__(self, content: list[str]):
        self.content = content

    async def __aiter__(self):
        for chunk in self.content:
            yield chunk
            await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_streaming_service_basic():
    service = BreakthroughStreamingService()
    gen = MockGenerator(["Hello", " ", "World"]).__aiter__()

    result = []
    async for chunk in service.stream_with_smart_chunking(gen):
        result.append(chunk)

    assert len(result) > 0
    assert "event: delta" in result[0]


@pytest.mark.asyncio
async def test_streaming_cancellation():
    service = BreakthroughStreamingService()

    async def infinite_gen():
        while True:
            yield "infinite"
            await asyncio.sleep(0.1)

    # Create a task that we can cancel
    async def consume():
        async for _ in service.stream_with_smart_chunking(infinite_gen()):
            pass

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.2)
    task.cancel()

    with contextlib.suppress(asyncio.CancelledError):
        await task
