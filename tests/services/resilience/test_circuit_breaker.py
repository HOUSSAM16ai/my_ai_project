import pytest
import time
from unittest.mock import Mock, call
from app.services.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
)

class TestCircuitBreaker:
    @pytest.fixture
    def config(self):
        return CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout_seconds=1,
            half_open_max_calls=1
        )

    @pytest.fixture
    def circuit_breaker(self, config):
        return CircuitBreaker("test-breaker", config)

    def test_initial_state(self, circuit_breaker):
        """Test initial state is CLOSED"""
        assert circuit_breaker.state.state == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 0
        assert circuit_breaker.state.success_count == 0

    def test_success_flow(self, circuit_breaker):
        """Test successful execution keeps circuit CLOSED and resets failures"""
        func = Mock(return_value="success")

        # Simulate a failure first
        circuit_breaker._on_failure()
        assert circuit_breaker.state.failure_count == 1

        # Successful call
        result = circuit_breaker.call(func)

        assert result == "success"
        assert circuit_breaker.state.state == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 0  # Should reset on success
        func.assert_called_once()

    def test_failure_threshold_opens_circuit(self, circuit_breaker):
        """Test reaching failure threshold opens the circuit"""
        func = Mock(side_effect=Exception("error"))

        # First failure
        with pytest.raises(Exception):
            circuit_breaker.call(func)
        assert circuit_breaker.state.state == CircuitState.CLOSED
        assert circuit_breaker.state.failure_count == 1

        # Second failure (threshold reached)
        with pytest.raises(Exception):
            circuit_breaker.call(func)
        assert circuit_breaker.state.state == CircuitState.OPEN
        assert circuit_breaker.state.last_failure_time is not None

        # Next call should fail fast
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(func)

        # Verify function was called exactly twice (for the failures)
        assert func.call_count == 2

    def test_timeout_transition_to_half_open(self, circuit_breaker):
        """Test transition from OPEN to HALF_OPEN after timeout"""
        # Force OPEN state
        circuit_breaker._transition_to_open()

        # Wait for timeout
        time.sleep(1.1)

        # Should be HALF_OPEN implicitly when checked
        assert circuit_breaker._get_state() == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self, circuit_breaker):
        """Test success in HALF_OPEN closes the circuit"""
        # Force OPEN state and wait for timeout logic (simulated by helper)
        circuit_breaker._transition_to_open()
        circuit_breaker.config.timeout_seconds = 0 # Instant timeout
        time.sleep(0.01)

        func = Mock(return_value="success")

        # First success (threshold is 2)
        circuit_breaker.call(func)
        assert circuit_breaker.state.state == CircuitState.HALF_OPEN
        assert circuit_breaker.state.success_count == 1

        # Second success
        circuit_breaker.call(func)
        assert circuit_breaker.state.state == CircuitState.CLOSED
        assert circuit_breaker.state.success_count == 0
        assert circuit_breaker.state.failure_count == 0

    def test_half_open_failure_opens_circuit(self, circuit_breaker):
        """Test failure in HALF_OPEN opens the circuit immediately"""
        # Force OPEN state and wait for timeout logic
        circuit_breaker._transition_to_open()
        circuit_breaker.config.timeout_seconds = 0
        time.sleep(0.01)

        func = Mock(side_effect=Exception("error"))

        with pytest.raises(Exception):
            circuit_breaker.call(func)

        assert circuit_breaker.state.state == CircuitState.OPEN
        assert circuit_breaker.state.success_count == 0

    def test_half_open_concurrency_limit(self, circuit_breaker):
        """Test concurrent calls limit in HALF_OPEN state"""
        circuit_breaker._transition_to_open()
        circuit_breaker.config.timeout_seconds = 0
        time.sleep(0.01)

        # We need to simulate being in HALF_OPEN state correctly.
        # The call() method checks `current_state == CircuitState.HALF_OPEN`.
        # _get_state() will transition if timeout expired.

        # Ensure we are in HALF_OPEN
        assert circuit_breaker._get_state() == CircuitState.HALF_OPEN

        # Manually increment active calls to simulate concurrency
        # The logic in call() is:
        # if current_state == CircuitState.HALF_OPEN:
        #     if self.state.half_open_calls >= self.config.half_open_max_calls:
        #         raise ...

        # So we need to set half_open_calls manually
        circuit_breaker.state.half_open_calls = 1

        func = Mock()
        with pytest.raises(CircuitBreakerOpenError) as exc:
            circuit_breaker.call(func)

        assert "limit reached" in str(exc.value)

    def test_expected_exceptions(self, config):
        """Test that only expected exceptions count as failures"""
        config.expected_exceptions = (ValueError,)
        cb = CircuitBreaker("test", config)

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
        assert stats["name"] == "test-breaker"
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
        assert "last_state_change" in stats
