from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from app.services.api_chaos_monkey_service import (
    ChaosExecution,
    ChaosMonkeyMode,
    ChaosMonkeyService,
    FailureScenario,
    ResilienceLevel,
    get_chaos_monkey_service,
)


# Reset singleton before/after tests
@pytest.fixture(autouse=True)
def reset_chaos_singleton():
    # Before test
    from app.services import api_chaos_monkey_service

    api_chaos_monkey_service._chaos_monkey_instance = None
    yield
    # After test
    api_chaos_monkey_service._chaos_monkey_instance = None


def test_singleton_pattern():
    """Test that get_chaos_monkey_service returns the same instance."""
    service1 = get_chaos_monkey_service()
    service2 = get_chaos_monkey_service()
    assert service1 is service2
    assert isinstance(service1, ChaosMonkeyService)


def test_initial_state():
    """Test the initial state of the service."""
    service = get_chaos_monkey_service()
    # It seems the service initializes with some default schedules but disabled
    assert service.enabled is False
    assert service.mode == ChaosMonkeyMode.SCHEDULED
    assert len(service.schedules) > 0
    assert "db_failure" in service.schedules


def test_enable_disable():
    """Test enabling and disabling the service."""
    service = get_chaos_monkey_service()

    service.enable_chaos_monkey(mode=ChaosMonkeyMode.CONTINUOUS)
    assert service.enabled is True
    assert service.mode == ChaosMonkeyMode.CONTINUOUS

    service.disable_chaos_monkey()
    assert service.enabled is False


def test_execute_chaos_experiment_disabled_error():
    """Test that execution fails if disabled."""
    service = get_chaos_monkey_service()
    service.disable_chaos_monkey()

    with pytest.raises(RuntimeError, match="Chaos Monkey is disabled"):
        service.execute_chaos_experiment(FailureScenario.SERVICE_CRASH, ["api"])


def test_execute_chaos_experiment_success():
    """Test successful execution of a chaos experiment."""
    service = get_chaos_monkey_service()
    service.enable_chaos_monkey()

    # Mock the internal helper methods to avoid side effects and randomness
    with (
        patch.object(service, "_inject_failure") as mock_inject,
        patch.object(service, "_wait_for_recovery", return_value=True) as mock_wait,
        patch.object(service, "_get_current_error_rate", side_effect=[1.0, 1.5, 1.0]),
        patch.object(service, "_get_current_latency_p99", return_value=100.0),
    ):
        execution = service.execute_chaos_experiment(
            scenario=FailureScenario.SLOW_RESPONSE, target_services=["api"], duration_minutes=5
        )

        assert isinstance(execution, ChaosExecution)
        assert execution.scenario == FailureScenario.SLOW_RESPONSE
        assert execution.affected_services == ["api"]
        assert execution.system_recovered is True
        assert execution.passed is True  # Based on mocked metrics
        assert service.total_experiments_run == 1
        assert len(service.executions) == 1

        mock_inject.assert_called_once()
        mock_wait.assert_called_once()


def test_calculate_resilience_score_empty():
    """Test resilience score calculation with no history."""
    service = get_chaos_monkey_service()
    score = service.calculate_resilience_score()

    assert score.score == 0.0
    assert score.level == ResilienceLevel.CRITICAL
    assert score.total_tests == 0


def test_calculate_resilience_score_with_history():
    """Test resilience score calculation with history."""
    service = get_chaos_monkey_service()
    service.enable_chaos_monkey()

    # Manually populate history to avoid running full experiments
    execution1 = ChaosExecution(
        execution_id="1",
        schedule_id=None,
        scenario=FailureScenario.SERVICE_CRASH,
        started_at=datetime.now(UTC),
        passed=True,
        system_recovered=True,
        recovery_time_seconds=60.0,
    )
    execution2 = ChaosExecution(
        execution_id="2",
        schedule_id=None,
        scenario=FailureScenario.SERVICE_CRASH,
        started_at=datetime.now(UTC),
        passed=False,
        system_recovered=False,
        recovery_time_seconds=0.0,
    )

    service.executions.append(execution1)
    service.executions.append(execution2)

    score = service.calculate_resilience_score()

    assert score.total_tests == 2
    assert score.passed_tests == 1
    assert score.failed_tests == 1
    assert score.level != ResilienceLevel.CRITICAL  # Should be better than 0


def test_get_chaos_status():
    """Test getting status dict."""
    service = get_chaos_monkey_service()
    status = service.get_chaos_status()

    assert isinstance(status, dict)
    assert "enabled" in status
    assert "mode" in status
    assert "resilience_score" in status
