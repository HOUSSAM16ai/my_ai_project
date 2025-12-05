import pytest
import time
from unittest.mock import Mock, patch
from app.services.resilience.retry import (
    RetryManager,
    RetryConfig,
    RetryStrategy,
    RetryBudgetExhaustedError,
    RetryableError
)

class TestRetryManager:
    @pytest.fixture
    def config(self):
        return RetryConfig(
            max_retries=3,
            base_delay_ms=10,
            retry_budget_percent=50.0, # High budget for testing
            strategy=RetryStrategy.LINEAR
        )

    @pytest.fixture
    def retry_manager(self, config):
        return RetryManager(config)

    def test_successful_execution(self, retry_manager):
        """Test successful execution without retries"""
        func = Mock(return_value="success")
        result = retry_manager.execute_with_retry(func)

        assert result == "success"
        func.assert_called_once()

        # Verify attempt tracking
        stats = retry_manager.retry_budget.get_stats()
        # 1 request, 0 retries
        assert stats["total_requests"] == 1
        assert stats["total_retries"] == 0

    def test_retry_on_exception(self, retry_manager):
        """Test retry logic on exception"""
        func = Mock(side_effect=[Exception("fail"), "success"])

        result = retry_manager.execute_with_retry(func)

        assert result == "success"
        assert func.call_count == 2

        stats = retry_manager.retry_budget.get_stats()
        # 1st attempt (request +1) -> Fail -> Retry (retry +1)
        # 2nd attempt (request +1) -> Success
        # total_requests = 2. total_retries = 1.
        assert stats["total_retries"] == 1
        assert stats["total_requests"] == 2

    def test_max_retries_exceeded(self, retry_manager):
        """Test failure after max retries"""
        func = Mock(side_effect=Exception("fail"))

        with pytest.raises(Exception) as exc:
            retry_manager.execute_with_retry(func)

        assert "fail" in str(exc.value) # Expect the original exception message
        # 1 initial + 3 retries = 4 calls
        assert func.call_count == 4

    def test_retry_on_status_code(self, retry_manager):
        """Test retry on specific status codes"""
        # Mock response object
        Response = type('Response', (), {})

        fail_response = Response()
        fail_response.status_code = 500

        success_response = Response()
        success_response.status_code = 200

        func = Mock(side_effect=[fail_response, success_response])

        result = retry_manager.execute_with_retry(func)

        assert result == success_response
        assert func.call_count == 2

    def test_no_retry_on_4xx(self, retry_manager):
        """Test that 4xx errors are not retried"""
        Response = type('Response', (), {})
        response = Response()
        response.status_code = 400

        func = Mock(return_value=response)

        result = retry_manager.execute_with_retry(func)

        assert result == response
        assert func.call_count == 1

    def test_retry_budget_exhausted(self, config):
        """Test failing fast when retry budget is exhausted"""
        config.retry_budget_percent = 10.0 # 10%
        manager = RetryManager(config)

        # Manually inflate stats
        # 100 requests, 15 retries = 15% rate
        manager.retry_budget.total_requests = 100
        manager.retry_budget.total_retries = 15

        func = Mock()
        with pytest.raises(RetryBudgetExhaustedError):
            manager.execute_with_retry(func)

        func.assert_not_called()

    def test_idempotency(self, retry_manager):
        """Test idempotent execution"""
        func = Mock(return_value="result")
        key = "unique-key-123"

        # First call
        result1 = retry_manager.execute_with_retry(func, idempotency_key=key)

        # Second call
        result2 = retry_manager.execute_with_retry(func, idempotency_key=key)

        assert result1 == result2
        assert func.call_count == 1 # Only called once

    def test_delay_calculation_strategies(self):
        """Test different backoff strategies"""
        # Linear
        config_linear = RetryConfig(strategy=RetryStrategy.LINEAR, base_delay_ms=100)
        manager_linear = RetryManager(config_linear)
        # Attempt 0: 100 * 1 = 100
        delay = manager_linear._calculate_delay(0)
        assert 50 <= delay <= 150 # +/- 50% jitter

        # Exponential
        config_exp = RetryConfig(strategy=RetryStrategy.EXPONENTIAL_BACKOFF, base_delay_ms=100)
        manager_exp = RetryManager(config_exp)
        # Attempt 1: 100 * 2^1 = 200
        delay = manager_exp._calculate_delay(1)
        assert 100 <= delay <= 300

        # Fibonacci
        config_fib = RetryConfig(strategy=RetryStrategy.FIBONACCI, base_delay_ms=100)
        manager_fib = RetryManager(config_fib)
        # Attempt 3: fib(5) = 5 -> 500
        # fib sequence: 0, 1, 1, 2, 3, 5
        delay = manager_fib._calculate_delay(3)
        assert 250 <= delay <= 750

    def test_retry_budget_reset(self, retry_manager):
        """Test retry budget window reset"""
        # Window size is 1000 by default. Set to small for test
        retry_manager.retry_budget.window_size = 10

        # Simulate filling up the window
        # 11 requests, 5 retries.
        retry_manager.retry_budget.total_requests = 11
        retry_manager.retry_budget.total_retries = 5

        # Trigger tracking (which checks window)
        # track_request increments total_requests to 12.
        # 12 > 10 -> Reset.
        # New requests = window_size(10) * 0.9 = 9 (int)
        # New retries = 5 * 0.9 = 4 (int)

        retry_manager.retry_budget.track_request()

        assert retry_manager.retry_budget.total_requests == 9
        assert retry_manager.retry_budget.total_retries == 4
