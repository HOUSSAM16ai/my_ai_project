# tests/ai/test_circuit_breaker.py
"""
Tests for Circuit Breaker Implementation
=========================================
"""

import pytest
import time
from app.ai.application.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_starts_closed(self):
        """Circuit should start in CLOSED state."""
        breaker = CircuitBreaker("test")
        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.is_available()
    
    def test_successful_calls_keep_circuit_closed(self):
        """Successful calls should keep circuit CLOSED."""
        breaker = CircuitBreaker("test")
        
        for _ in range(10):
            result = breaker.call(lambda: "success")
            assert result == "success"
        
        assert breaker.get_state() == CircuitState.CLOSED
        metrics = breaker.get_metrics()
        assert metrics.successful_requests == 10
        assert metrics.failed_requests == 0
    
    def test_circuit_opens_after_threshold_failures(self):
        """Circuit should open after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=1.0)
        breaker = CircuitBreaker("test", config)
        
        def failing_func():
            raise ValueError("Test error")
        
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.get_state() == CircuitState.OPEN
        assert not breaker.is_available()
    
    def test_circuit_rejects_calls_when_open(self):
        """Circuit should reject calls when OPEN."""
        config = CircuitBreakerConfig(failure_threshold=2, timeout=10.0)
        breaker = CircuitBreaker("test", config)
        
        def failing_func():
            raise ValueError("Test error")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.get_state() == CircuitState.OPEN
        
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "success")
        
        metrics = breaker.get_metrics()
        assert metrics.rejected_requests == 1
    
    def test_circuit_transitions_to_half_open(self):
        """Circuit should transition to HALF_OPEN after timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.1,
            half_open_max_calls=2
        )
        breaker = CircuitBreaker("test", config)
        
        def failing_func():
            raise ValueError("Test error")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.get_state() == CircuitState.OPEN
        
        time.sleep(0.15)
        
        result = breaker.call(lambda: "success")
        assert result == "success"
        assert breaker.get_state() == CircuitState.HALF_OPEN
    
    def test_circuit_closes_after_successful_half_open(self):
        """Circuit should close after successful HALF_OPEN calls."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1,
        )
        breaker = CircuitBreaker("test", config)
        
        def failing_func():
            raise ValueError("Test error")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        time.sleep(0.15)
        
        for _ in range(2):
            breaker.call(lambda: "success")
        
        assert breaker.get_state() == CircuitState.CLOSED
    
    def test_circuit_reopens_on_half_open_failure(self):
        """Circuit should reopen if HALF_OPEN call fails."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=0.1,
        )
        breaker = CircuitBreaker("test", config)
        
        def failing_func():
            raise ValueError("Test error")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        time.sleep(0.15)
        
        with pytest.raises(ValueError):
            breaker.call(failing_func)
        
        assert breaker.get_state() == CircuitState.OPEN
    
    def test_manual_reset(self):
        """Manual reset should close circuit."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test", config)
        
        def failing_func():
            raise ValueError("Test error")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.get_state() == CircuitState.OPEN
        
        breaker.reset()
        
        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.is_available()
        
        metrics = breaker.get_metrics()
        assert metrics.total_requests == 0
    
    @pytest.mark.asyncio
    async def test_async_circuit_breaker(self):
        """Circuit breaker should work with async functions."""
        breaker = CircuitBreaker("test")
        
        async def async_func():
            return "async success"
        
        result = await breaker.call_async(async_func)
        assert result == "async success"
        
        metrics = breaker.get_metrics()
        assert metrics.successful_requests == 1
