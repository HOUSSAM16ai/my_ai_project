# tests/ai/test_retry_strategy.py
"""
Tests for Retry Strategy Implementation
========================================
"""

import pytest
import time
from app.ai.application.retry_strategy import (
    ExponentialBackoffRetry,
    LinearBackoffRetry,
    FibonacciBackoffRetry,
    AdaptiveRetry,
    RetryConfig,
    RetryExecutor,
    ErrorCategory,
)


class TestRetryStrategies:
    """Test retry strategy implementations."""
    
    def test_exponential_backoff_delay(self):
        """Exponential backoff should increase exponentially."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
        strategy = ExponentialBackoffRetry(config)
        
        delay0 = strategy.calculate_delay(0)
        delay1 = strategy.calculate_delay(1)
        delay2 = strategy.calculate_delay(2)
        
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0
    
    def test_linear_backoff_delay(self):
        """Linear backoff should increase linearly."""
        config = RetryConfig(base_delay=1.0, jitter=False)
        strategy = LinearBackoffRetry(config)
        
        delay0 = strategy.calculate_delay(0)
        delay1 = strategy.calculate_delay(1)
        delay2 = strategy.calculate_delay(2)
        
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 3.0
    
    def test_fibonacci_backoff_delay(self):
        """Fibonacci backoff should follow fibonacci sequence."""
        config = RetryConfig(base_delay=1.0, jitter=False)
        strategy = FibonacciBackoffRetry(config)
        
        delay0 = strategy.calculate_delay(0)
        delay1 = strategy.calculate_delay(1)
        delay2 = strategy.calculate_delay(2)
        delay3 = strategy.calculate_delay(3)
        
        assert delay0 == 1.0
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 3.0
    
    def test_max_delay_cap(self):
        """Delay should be capped at max_delay."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False
        )
        strategy = ExponentialBackoffRetry(config)
        
        delay10 = strategy.calculate_delay(10)
        assert delay10 <= 5.0
    
    def test_jitter_adds_randomness(self):
        """Jitter should add randomness to delay."""
        config = RetryConfig(base_delay=1.0, jitter=True, jitter_factor=0.1)
        strategy = ExponentialBackoffRetry(config)
        
        delays = [strategy.calculate_delay(0) for _ in range(10)]
        
        assert len(set(delays)) > 1
        assert all(0.9 <= d <= 1.1 for d in delays)
    
    def test_error_classification(self):
        """Errors should be classified correctly."""
        strategy = ExponentialBackoffRetry()
        
        rate_limit_error = Exception("429 Rate limit exceeded")
        assert strategy.classify_error(rate_limit_error) == ErrorCategory.RATE_LIMIT
        
        timeout_error = Exception("Request timeout")
        assert strategy.classify_error(timeout_error) == ErrorCategory.TIMEOUT
        
        network_error = Exception("Connection refused")
        assert strategy.classify_error(network_error) == ErrorCategory.NETWORK
    
    def test_should_retry_respects_max_attempts(self):
        """Should not retry after max attempts."""
        config = RetryConfig(max_attempts=3)
        strategy = ExponentialBackoffRetry(config)
        
        error = Exception("Retryable error")
        
        assert strategy.should_retry(error, 0)
        assert strategy.should_retry(error, 1)
        assert strategy.should_retry(error, 2)
        assert not strategy.should_retry(error, 3)
    
    def test_should_retry_respects_error_category(self):
        """Should only retry allowed error categories."""
        config = RetryConfig(
            retry_on_categories={ErrorCategory.RATE_LIMIT, ErrorCategory.NETWORK}
        )
        strategy = ExponentialBackoffRetry(config)
        
        rate_limit_error = Exception("429 Rate limit")
        client_error = Exception("400 Bad request")
        
        assert strategy.should_retry(rate_limit_error, 0)
        assert not strategy.should_retry(client_error, 0)


class TestRetryExecutor:
    """Test retry executor functionality."""
    
    def test_successful_execution_no_retry(self):
        """Successful execution should not retry."""
        strategy = ExponentialBackoffRetry(RetryConfig(base_delay=0.01))
        executor = RetryExecutor(strategy)
        
        call_count = 0
        
        def func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = executor.execute(func)
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure(self):
        """Should retry on failure."""
        config = RetryConfig(max_attempts=3, base_delay=0.01, jitter=False)
        strategy = ExponentialBackoffRetry(config)
        executor = RetryExecutor(strategy)
        
        call_count = 0
        
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"
        
        result = executor.execute(func)
        
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Should raise error after max retries."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        strategy = ExponentialBackoffRetry(config)
        executor = RetryExecutor(strategy)
        
        def func():
            raise ValueError("Persistent error")
        
        with pytest.raises(ValueError):
            executor.execute(func)
        
        metrics = strategy.get_metrics()
        assert metrics.failed_retries > 0
    
    def test_non_retryable_error(self):
        """Should not retry non-retryable errors."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.01,
            retry_on_categories={ErrorCategory.RATE_LIMIT}
        )
        strategy = ExponentialBackoffRetry(config)
        executor = RetryExecutor(strategy)
        
        call_count = 0
        
        def func():
            nonlocal call_count
            call_count += 1
            raise Exception("400 Bad request")
        
        with pytest.raises(Exception):
            executor.execute(func)
        
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Async retry should work."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        strategy = ExponentialBackoffRetry(config)
        executor = RetryExecutor(strategy)
        
        call_count = 0
        
        async def async_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary error")
            return "async success"
        
        result = await executor.execute_async(async_func)
        
        assert result == "async success"
        assert call_count == 2


class TestAdaptiveRetry:
    """Test adaptive retry strategy."""
    
    def test_adaptive_learns_from_errors(self):
        """Adaptive strategy should learn from error patterns."""
        strategy = AdaptiveRetry(RetryConfig(base_delay=1.0, jitter=False))
        
        rate_limit_error = Exception("429 Rate limit")
        strategy.record_error(rate_limit_error)
        
        delay = strategy.calculate_delay(0)
        
        assert delay >= 5.0
    
    def test_adaptive_different_delays_per_category(self):
        """Adaptive should use different delays per error category."""
        config = RetryConfig(base_delay=1.0, jitter=False)
        strategy = AdaptiveRetry(config)
        
        rate_limit_error = Exception("429 Rate limit")
        network_error = Exception("Connection timeout")
        
        strategy.record_error(rate_limit_error)
        rate_limit_delay = strategy.calculate_delay(0)
        
        strategy._error_history.clear()
        strategy.record_error(network_error)
        network_delay = strategy.calculate_delay(0)
        
        assert rate_limit_delay > network_delay
