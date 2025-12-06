import time
from unittest.mock import Mock

import pytest

from app.services.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)


class TestCircuitBreaker:
    @pytest.fixture
    def config(self):
        return CircuitBreakerConfig(
            failure_threshold=2, success_threshold=2, timeout_seconds=1, half_open_max_calls=1
        )

    @pytest.fixture
    def circuit_breaker(self, config):
        # Ensure we start with a clean state by using a unique name
        name = f"test-breaker-{time.time()}"
        return CircuitBreaker(name, config)

    def _force_open(self, cb):
        """Helper to force the circuit breaker into OPEN state."""
        # We can force the state on the core breaker
        with cb._core_breaker._lock:
            cb._core_breaker._state = CircuitState.OPEN
            cb._core_breaker._last_failure_time = time.time()
            cb._core_breaker._failure_count = cb.config.failure_threshold

    def _get_state(self, cb):
        """Helper to get the state from the wrapper."""
        return cb.state.state

    def test_initial_state(self, circuit_breaker):
        """Test initial state is CLOSED"""
        assert self._get_state(circuit_breaker) == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 0
        assert circuit_breaker.state.success_count == 0

    def test_success_flow(self, circuit_breaker):
        """Test successful execution keeps circuit CLOSED and resets failures"""
        func = Mock(return_value="success")

        # Simulate a failure first using the core breaker directly
        circuit_breaker._core_breaker.record_failure()
        assert circuit_breaker.state.failure_count == 1

        # Successful call
        result = circuit_breaker.call(func)

        assert result == "success"
        assert self._get_state(circuit_breaker) == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 0  # Should reset on success
        func.assert_called_once()

    def test_failure_threshold_opens_circuit(self, circuit_breaker):
        """Test reaching failure threshold opens the circuit"""
        func = Mock(side_effect=Exception("error"))

        # First failure
        with pytest.raises(Exception, match="error"):
            circuit_breaker.call(func)
        assert self._get_state(circuit_breaker) == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 1

        # Second failure (threshold reached)
        with pytest.raises(Exception, match="error"):
            circuit_breaker.call(func)
        assert self._get_state(circuit_breaker) == CircuitState.OPEN
        assert circuit_breaker.state.last_failure_time is not None

        # Next call should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(func)

        # Verify function was called exactly twice (for the failures)
        assert func.call_count == 2

    def test_timeout_transition_to_half_open(self, circuit_breaker):
        """Test transition from OPEN to HALF_OPEN after timeout"""
        # Force OPEN state
        self._force_open(circuit_breaker)

        # Wait for timeout
        time.sleep(1.1)

        # Trigger state check
        circuit_breaker._core_breaker.allow_request()

        assert self._get_state(circuit_breaker) == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self, circuit_breaker):
        """Test success in HALF_OPEN closes the circuit"""
        # Force OPEN state
        self._force_open(circuit_breaker)
        # Modify core config directly
        circuit_breaker._core_breaker.config.timeout = 0
        time.sleep(0.01)

        func = Mock(return_value="success")

        # First success (threshold is 2)
        circuit_breaker.call(func)
        assert self._get_state(circuit_breaker) == CircuitState.HALF_OPEN
        assert circuit_breaker.state.success_count == 1

        # Second success
        circuit_breaker.call(func)
        assert self._get_state(circuit_breaker) == CircuitState.CLOSED
        assert circuit_breaker.state.success_count == 0
        assert circuit_breaker.state.failure_count == 0

    def test_half_open_failure_opens_circuit(self, circuit_breaker):
        """Test failure in HALF_OPEN opens the circuit immediately"""
        # Force OPEN state
        self._force_open(circuit_breaker)
        circuit_breaker._core_breaker.config.timeout = 0
        time.sleep(0.01)

        func = Mock(side_effect=Exception("error"))

        with pytest.raises(Exception, match="error"):
            circuit_breaker.call(func)

        assert self._get_state(circuit_breaker) == CircuitState.OPEN
        assert circuit_breaker.state.success_count == 0

    def test_half_open_concurrency_limit(self, circuit_breaker):
        """Test concurrent calls limit in HALF_OPEN state"""
        self._force_open(circuit_breaker)
        circuit_breaker._core_breaker.config.timeout = 0
        time.sleep(0.01)

        # Ensure we are in HALF_OPEN
        circuit_breaker._core_breaker.allow_request()
        assert self._get_state(circuit_breaker) == CircuitState.HALF_OPEN

        # Manually increment active calls to simulate concurrency
        # We set it to max (1)
        circuit_breaker._core_breaker._half_open_calls = circuit_breaker.config.half_open_max_calls

        func = Mock()
        # Next call should be rejected because limit is reached
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(func)

    def test_expected_exceptions(self, config):
        """Test that only expected exceptions count as failures"""
        config.expected_exceptions = (ValueError,)
        cb = CircuitBreaker("test-expected-exc", config)

        func = Mock(side_effect=TypeError("unexpected"))

        # Unexpected exception should raise but not count towards failure threshold
        with pytest.raises(TypeError):
            cb.call(func)

        assert cb.state.failure_count == 0

        func = Mock(side_effect=ValueError("expected"))

        # Expected exception counts
        with pytest.raises(ValueError):
            cb.call(func)

        assert cb.state.failure_count == 1

    def test_get_stats(self, circuit_breaker):
        """Test stats reporting"""
        stats = circuit_breaker.get_stats()
        # Name might have timestamp suffix now
        assert "test-breaker" in stats["name"]
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert "last_state_change" in stats
