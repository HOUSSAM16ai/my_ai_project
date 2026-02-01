from unittest.mock import AsyncMock

import pytest

from app.core.resilience.composite import CompositeResilienceConfig, CompositeResiliencePolicy
from app.core.resilience.fallback import FallbackPolicy
from app.core.resilience.retry import RetryConfig, RetryPolicy


@pytest.mark.asyncio
async def test_composite_execution_order():
    # Setup: Retry 2 times, Fallback to "recovered"
    retry = RetryPolicy(RetryConfig(max_attempts=2, initial_delay=0.01))
    fallback = FallbackPolicy(fallback_func=AsyncMock(return_value="recovered"))

    config = CompositeResilienceConfig(retry=retry, fallback=fallback)
    policy = CompositeResiliencePolicy(config)

    mock_func = AsyncMock(side_effect=[ValueError("fail"), "success"])

    # Retry should catch the first fail
    result = await policy.execute(mock_func)
    assert result == "success"
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_composite_full_failure_fallback():
    retry = RetryPolicy(RetryConfig(max_attempts=2, initial_delay=0.01))
    fallback = FallbackPolicy(fallback_func=AsyncMock(return_value="recovered"))

    config = CompositeResilienceConfig(retry=retry, fallback=fallback)
    policy = CompositeResiliencePolicy(config)

    mock_func = AsyncMock(side_effect=ValueError("fail"))

    result = await policy.execute(mock_func)
    assert result == "recovered"
    # Called 2 times (retry), then fallback
    assert mock_func.call_count == 2
