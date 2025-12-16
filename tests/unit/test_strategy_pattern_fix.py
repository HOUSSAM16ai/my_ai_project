
from collections.abc import AsyncGenerator

import pytest

from app.core.patterns.strategy import Strategy, StrategyRegistry


# Mock Strategies
class AsyncGenStrategy(Strategy[str, AsyncGenerator[str, None]]):
    async def can_handle(self, context: str) -> bool:
        return context == "gen"

    async def execute(self, context: str) -> AsyncGenerator[str, None]:
        yield "part1"
        yield "part2"

class CoroutineStrategy(Strategy[str, str]):
    async def can_handle(self, context: str) -> bool:
        return context == "coro"

    async def execute(self, context: str) -> str:
        return "result"

@pytest.mark.asyncio
async def test_strategy_registry_async_generator():
    """Verify that StrategyRegistry handles async generator return values correctly."""
    registry = StrategyRegistry[str, AsyncGenerator[str, None]]()
    registry.register(AsyncGenStrategy())

    result = await registry.execute("gen")

    assert result is not None
    # We should be able to iterate over the result
    parts = []
    async for part in result:
        parts.append(part)

    assert parts == ["part1", "part2"]

@pytest.mark.asyncio
async def test_strategy_registry_coroutine():
    """Verify that StrategyRegistry handles coroutine return values correctly."""
    registry = StrategyRegistry[str, str]()
    registry.register(CoroutineStrategy())

    result = await registry.execute("coro")

    assert result == "result"
