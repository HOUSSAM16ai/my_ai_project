import pytest

from app.core.patterns.strategy_pattern.base import Strategy
from app.core.patterns.strategy_pattern.registry import StrategyRegistry


# Concrete Strategy for testing
class HighPriorityStrategy(Strategy[str, str]):
    async def can_handle(self, context: str) -> bool:
        return context == "priority"

    async def execute(self, context: str) -> str:
        return "high_result"

    @property
    def priority(self) -> int:
        return 100


class LowPriorityStrategy(Strategy[str, str]):
    async def can_handle(self, context: str) -> bool:
        return context == "priority"

    async def execute(self, context: str) -> str:
        return "low_result"

    @property
    def priority(self) -> int:
        return 10


class FailingStrategy(Strategy[str, str]):
    async def can_handle(self, context: str) -> bool:
        return True

    async def execute(self, context: str) -> str:
        raise ValueError("failed")

    @property
    def priority(self) -> int:
        return 50


@pytest.fixture
def registry():
    return StrategyRegistry()


@pytest.mark.asyncio
async def test_execution_priority(registry):
    # Both handle "priority", but High should win
    registry.register(LowPriorityStrategy())
    registry.register(HighPriorityStrategy())

    result = await registry.execute("priority")
    assert result == "high_result"


@pytest.mark.asyncio
async def test_failover(registry):
    # FailingStrategy (50) fails, fallback to Low (10)?
    # No, Low handles "priority" context. Failing handles "priority" (True).
    # If context="priority", Failing (50) tried first. Fails.
    # Then Low (10) tried. Succeeds.

    registry.register(LowPriorityStrategy())
    registry.register(FailingStrategy())

    result = await registry.execute("priority")
    assert result == "low_result"


@pytest.mark.asyncio
async def test_no_strategy_found(registry):
    registry.register(HighPriorityStrategy())
    result = await registry.execute("unknown_context")
    assert result is None


def test_registry_clear(registry):
    registry.register(HighPriorityStrategy())
    registry.clear()
    assert len(registry.get_strategies()) == 0
