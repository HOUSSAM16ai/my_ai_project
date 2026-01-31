
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.core.resilience.retry import RetryPolicy, RetryConfig

@pytest.fixture
def retry_policy():
    config = RetryConfig(
        max_attempts=3,
        initial_delay=0.01, # Fast for tests
        max_delay=0.1,
        jitter=False
    )
    return RetryPolicy(config)

@pytest.mark.asyncio
async def test_retry_success_first_try(retry_policy):
    mock_func = AsyncMock(return_value="success")
    result = await retry_policy.execute(mock_func)
    assert result == "success"
    assert mock_func.call_count == 1

@pytest.mark.asyncio
async def test_retry_eventual_success(retry_policy):
    # Fail twice, succeed third time
    mock_func = AsyncMock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])
    
    result = await retry_policy.execute(mock_func)
    assert result == "success"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_retry_max_attempts_reached(retry_policy):
    mock_func = AsyncMock(side_effect=ValueError("persistent fail"))
    
    with pytest.raises(ValueError, match="persistent fail"):
        await retry_policy.execute(mock_func)
    
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_retry_delay(retry_policy):
    mock_func = AsyncMock(side_effect=[ValueError("fail"), "success"])
    
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await retry_policy.execute(mock_func)
        assert mock_sleep.call_count == 1
