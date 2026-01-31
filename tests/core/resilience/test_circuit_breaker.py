
import pytest
import time
from unittest.mock import patch, MagicMock
from app.core.resilience.circuit_breaker import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState, CircuitBreakerRegistry
)

@pytest.fixture
def breaker():
    config = CircuitBreakerConfig(
        failure_threshold=2,
        success_threshold=1,
        timeout=1.0,
        half_open_max_calls=1
    )
    return CircuitBreaker("test-breaker", config)

def test_initial_state(breaker):
    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request() is True

def test_open_circuit_on_failure(breaker):
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED # 1/2
    
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN # 2/2 -> Open

    assert breaker.allow_request() is False

def test_half_open_transition(breaker):
    # Open the circuit
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    
    # Wait for timeout (mock time)
    with patch("time.time", return_value=time.time() + 2.0):
        # First call triggers transition check
        assert breaker.allow_request() is True
        assert breaker.state == CircuitState.HALF_OPEN

def test_recovery_success(breaker):
    # Open -> Half-Open
    breaker.record_failure()
    breaker.record_failure()
    
    # Force state for test simplicity
    breaker._state = CircuitState.HALF_OPEN
    
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0

def test_recovery_failure(breaker):
    breaker._state = CircuitState.HALF_OPEN
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN

def test_registry_singleton():
    reg1 = CircuitBreakerRegistry.get_instance()
    reg2 = CircuitBreakerRegistry.get_instance()
    assert reg1 is reg2

def test_registry_management():
    registry = CircuitBreakerRegistry.get_instance()
    registry.clear()
    
    cb = registry.get("service-a")
    assert registry.get("service-a") is cb
    
    registry.remove("service-a")
    # Should be new instance
    assert registry.get("service-a") is not cb
