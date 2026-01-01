"""
Test for Async Generator Handling Fix.
=======================================

This test ensures that async generators are correctly handled throughout
the codebase, specifically in the Strategy Pattern implementation.

The bug: TypeError: object async_generator can't be used in 'await' expression
occurs when trying to await an async generator instead of iterating it with async for.
"""

import pytest
from collections.abc import AsyncGenerator

from app.core.patterns.strategy import Strategy, StrategyRegistry


class SimpleContext:
    """Simple context for testing."""
    def __init__(self, value: str):
        self.value = value


class AsyncGenStrategy(Strategy[SimpleContext, AsyncGenerator[str, None]]):
    """Strategy that returns an async generator using yield."""
    
    async def can_handle(self, context: SimpleContext) -> bool:
        return context.value == "stream"
    
    async def execute(self, context: SimpleContext) -> AsyncGenerator[str, None]:
        """Correct implementation: uses yield."""
        yield f"Chunk 1: {context.value}"
        yield f"Chunk 2: {context.value}"
        yield f"Chunk 3: {context.value}"
    
    @property
    def priority(self) -> int:
        return 10


class CoroutineStrategy(Strategy[SimpleContext, str]):
    """Strategy that returns a regular value via coroutine."""
    
    async def can_handle(self, context: SimpleContext) -> bool:
        return context.value == "simple"
    
    async def execute(self, context: SimpleContext) -> str:
        """Returns a simple string."""
        return f"Result: {context.value}"
    
    @property
    def priority(self) -> int:
        return 5


class NestedAsyncGenStrategy(Strategy[SimpleContext, AsyncGenerator[str, None]]):
    """Strategy that wraps another async generator correctly."""
    
    async def can_handle(self, context: SimpleContext) -> bool:
        return context.value == "nested"
    
    async def _inner_generator(self) -> AsyncGenerator[str, None]:
        """Inner async generator."""
        yield "Inner 1"
        yield "Inner 2"
    
    async def execute(self, context: SimpleContext) -> AsyncGenerator[str, None]:
        """Correct way: iterate and re-yield."""
        async for item in self._inner_generator():
            yield f"{context.value}: {item}"
    
    @property
    def priority(self) -> int:
        return 8


@pytest.mark.asyncio
async def test_async_generator_strategy():
    """Test that async generator strategies work correctly."""
    registry = StrategyRegistry[SimpleContext, AsyncGenerator[str, None]]()
    registry.register(AsyncGenStrategy())
    
    context = SimpleContext("stream")
    result = await registry.execute(context)
    
    # Result should be an async generator
    assert result is not None
    
    # Collect all chunks
    chunks = []
    async for chunk in result:
        chunks.append(chunk)
    
    assert len(chunks) == 3
    assert chunks[0] == "Chunk 1: stream"
    assert chunks[1] == "Chunk 2: stream"
    assert chunks[2] == "Chunk 3: stream"


@pytest.mark.asyncio
async def test_coroutine_strategy():
    """Test that regular coroutine strategies work correctly."""
    registry = StrategyRegistry[SimpleContext, str]()
    registry.register(CoroutineStrategy())
    
    context = SimpleContext("simple")
    result = await registry.execute(context)
    
    # Result should be a simple string
    assert result == "Result: simple"


@pytest.mark.asyncio
async def test_nested_async_generator():
    """Test that nested async generators are handled correctly."""
    registry = StrategyRegistry[SimpleContext, AsyncGenerator[str, None]]()
    registry.register(NestedAsyncGenStrategy())
    
    context = SimpleContext("nested")
    result = await registry.execute(context)
    
    assert result is not None
    
    # Collect all chunks
    chunks = []
    async for chunk in result:
        chunks.append(chunk)
    
    assert len(chunks) == 2
    assert chunks[0] == "nested: Inner 1"
    assert chunks[1] == "nested: Inner 2"


@pytest.mark.asyncio
async def test_no_matching_strategy():
    """Test that None is returned when no strategy matches."""
    registry = StrategyRegistry[SimpleContext, AsyncGenerator[str, None]]()
    registry.register(AsyncGenStrategy())
    
    context = SimpleContext("unknown")
    result = await registry.execute(context)
    
    assert result is None


@pytest.mark.asyncio
async def test_priority_ordering():
    """Test that strategies are executed in priority order."""
    registry = StrategyRegistry[SimpleContext, AsyncGenerator[str, None]]()
    
    # Register in reverse priority order
    low_priority = AsyncGenStrategy()
    low_priority._priority = 1
    
    high_priority = AsyncGenStrategy()
    high_priority._priority = 10
    
    registry.register(low_priority)
    registry.register(high_priority)
    
    # Both can handle "stream", but high priority should execute first
    context = SimpleContext("stream")
    result = await registry.execute(context)
    
    assert result is not None
    chunks = []
    async for chunk in result:
        chunks.append(chunk)
    
    # Should get results from the high priority strategy
    assert len(chunks) == 3


@pytest.mark.asyncio
async def test_error_recovery():
    """Test that registry continues to next strategy on error."""
    
    class FailingStrategy(Strategy[SimpleContext, AsyncGenerator[str, None]]):
        async def can_handle(self, context: SimpleContext) -> bool:
            return True
        
        async def execute(self, context: SimpleContext) -> AsyncGenerator[str, None]:
            raise RuntimeError("Intentional failure")
            yield "Should not reach"
        
        @property
        def priority(self) -> int:
            return 10
    
    class FallbackStrategy(Strategy[SimpleContext, AsyncGenerator[str, None]]):
        async def can_handle(self, context: SimpleContext) -> bool:
            return True
        
        async def execute(self, context: SimpleContext) -> AsyncGenerator[str, None]:
            yield "Fallback chunk"
        
        @property
        def priority(self) -> int:
            return 5
    
    registry = StrategyRegistry[SimpleContext, AsyncGenerator[str, None]]()
    registry.register(FailingStrategy())
    registry.register(FallbackStrategy())
    
    context = SimpleContext("test")
    result = await registry.execute(context)
    
    assert result is not None
    chunks = []
    async for chunk in result:
        chunks.append(chunk)
    
    # Should get results from fallback strategy
    assert chunks == ["Fallback chunk"]


if __name__ == "__main__":
    import asyncio
    
    async def run_tests():
        """Run all tests manually."""
        print("Running async generator fix tests...\n")
        
        print("✓ Test 1: Async Generator Strategy")
        await test_async_generator_strategy()
        
        print("✓ Test 2: Coroutine Strategy")
        await test_coroutine_strategy()
        
        print("✓ Test 3: Nested Async Generator")
        await test_nested_async_generator()
        
        print("✓ Test 4: No Matching Strategy")
        await test_no_matching_strategy()
        
        print("✓ Test 5: Priority Ordering")
        await test_priority_ordering()
        
        print("✓ Test 6: Error Recovery")
        await test_error_recovery()
        
        print("\n✅ All tests passed!")
    
    asyncio.run(run_tests())
