import pytest
from unittest.mock import MagicMock, patch
from app.services.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError

@pytest.fixture
def mock_core_breaker():
    with patch("app.services.resilience.circuit_breaker.get_circuit_breaker") as mock:
        yield mock

def test_circuit_breaker_initialization(mock_core_breaker):
    config = CircuitBreakerConfig()
    cb = CircuitBreaker("test-service", config)
    mock_core_breaker.assert_called_once()
    assert cb.name == "test-service"

def test_circuit_breaker_call_success(mock_core_breaker):
    mock_instance = MagicMock()
    mock_instance.allow_request.return_value = True
    mock_core_breaker.return_value = mock_instance

    cb = CircuitBreaker("test-service", CircuitBreakerConfig())

    result = cb.call(lambda: "success")

    assert result == "success"
    mock_instance.record_success.assert_called_once()
    mock_instance.record_failure.assert_not_called()

def test_circuit_breaker_call_failure(mock_core_breaker):
    mock_instance = MagicMock()
    mock_instance.allow_request.return_value = True
    mock_core_breaker.return_value = mock_instance

    cb = CircuitBreaker("test-service", CircuitBreakerConfig(expected_exceptions=(ValueError,)))

    with pytest.raises(ValueError):
        cb.call(lambda: (_ for _ in ()).throw(ValueError("oops")))

    mock_instance.record_failure.assert_called_once()
    mock_instance.record_success.assert_not_called()

def test_circuit_breaker_open(mock_core_breaker):
    mock_instance = MagicMock()
    mock_instance.allow_request.return_value = False
    mock_core_breaker.return_value = mock_instance

    cb = CircuitBreaker("test-service", CircuitBreakerConfig())

    with pytest.raises(CircuitBreakerOpenError):
        cb.call(lambda: "should not run")
