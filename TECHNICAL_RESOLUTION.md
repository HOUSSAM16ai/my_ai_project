# Technical Resolution: Async Generator Await Error

## Problem Diagnosis
The application encountered a `TypeError: object async_generator can't be used in 'await' expression` in `app/services/admin/chat_streamer.py`.

### Root Cause
The error was traced to the `StrategyRegistry.execute` method in `app/core/patterns/strategy.py`.

1. The `ChatOrchestrator` uses `StrategyRegistry` to manage chat handlers.
2. The handlers (e.g., `FileReadHandler`, `DefaultChatHandler`) are implemented as **asynchronous generator functions** (they use `yield` inside an `async def`).
3. Calling an async generator function immediately returns an `async_generator` object. It does **not** return a coroutine.
4. The `StrategyRegistry.execute` method was attempting to `await` the result of `strategy.execute(context)`.
5. Since `strategy.execute` returned an `async_generator` object (which is not awaitable), Python raised the `TypeError`.

### Affected Code
**File:** `app/core/patterns/strategy.py`

**Before:**
```python
    async def execute(self, context: T) -> R | None:
        """Find and execute appropriate strategy."""
        strategy = await self.find_strategy(context)
        if strategy:
            return await strategy.execute(context)  # <--- BUG: Awaits generator
        return None
```

## Solution Applied
The `StrategyRegistry.execute` method was modified to robustly handle both Coroutines and Async Generators.

We used `inspect.isawaitable()` to check if the return value needs to be awaited.

**After:**
```python
    import inspect

    async def execute(self, context: T) -> R | None:
        """Find and execute appropriate strategy."""
        strategy = await self.find_strategy(context)
        if strategy:
            result = strategy.execute(context)
            if inspect.isawaitable(result):
                return await result
            return result
        return None
```

## Verification
A verification script `verify_fix.py` was created to test both scenarios:
1. **Async Generator Strategy:** Confirmed that `execute` returns the generator without awaiting it.
2. **Coroutine Strategy:** Confirmed that `execute` awaits the coroutine and returns the result.

Both tests passed successfully.

## Architectural Implications
This fix makes the `Strategy` pattern in `CogniForge` more flexible, allowing strategies to implement either:
- **Request/Response** logic (returning a value via Coroutine).
- **Streaming** logic (yielding values via Async Generator).

This supports the "Evolutionary Logic Distillation" and "Superhuman" streaming requirements of the project.
