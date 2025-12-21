import pytest
from unittest.mock import MagicMock
from app.services.saga_orchestrator import (
    SagaOrchestrator, SagaStatus, StepStatus, SagaType, get_saga_orchestrator
)

@pytest.fixture
def orchestrator():
    return SagaOrchestrator()

def test_saga_creation(orchestrator):
    steps = [
        {"name": "Step 1", "action": lambda: True, "compensation": lambda: True}
    ]
    saga_id = orchestrator.create_saga("test_saga", steps)
    assert saga_id is not None

    status = orchestrator.get_saga_status(saga_id)
    assert status["status"] == "pending"
    assert len(status["steps"]) == 1

def test_successful_saga(orchestrator):
    action1 = MagicMock(return_value="res1")
    comp1 = MagicMock()
    action2 = MagicMock(return_value="res2")
    comp2 = MagicMock()

    steps = [
        {"name": "s1", "action": action1, "compensation": comp1},
        {"name": "s2", "action": action2, "compensation": comp2, "max_retries": 0}
    ]
    saga_id = orchestrator.create_saga("success_saga", steps)

    result = orchestrator.execute_saga(saga_id)
    assert result is True

    status = orchestrator.get_saga_status(saga_id)
    assert status["status"] == "completed"

    action1.assert_called_once()
    action2.assert_called_once()
    comp1.assert_not_called()
    comp2.assert_not_called()

def test_failed_saga_compensation(orchestrator):
    action1 = MagicMock(return_value="res1")
    comp1 = MagicMock()
    action2 = MagicMock(side_effect=Exception("Boom"))
    comp2 = MagicMock()

    steps = [
        {"name": "s1", "action": action1, "compensation": comp1},
        {"name": "s2", "action": action2, "compensation": comp2, "max_retries": 0}
    ]
    saga_id = orchestrator.create_saga("fail_saga", steps)

    result = orchestrator.execute_saga(saga_id)
    assert result is False

    status = orchestrator.get_saga_status(saga_id)
    assert status["status"] == "compensated" # Not FAILED, but COMPENSATED (or failed handled)
    # The code sets status=FAILED inside catch, then calls _compensate_saga which sets status=COMPENSATED.

    action1.assert_called_once()
    action2.assert_called_once()
    comp1.assert_called_once() # Should compensate step 1
    comp2.assert_not_called() # Step 2 failed, so no compensation needed (assuming atomic fail)

def test_retry_logic(orchestrator):
    # Fail twice, then succeed
    action = MagicMock(side_effect=[Exception("Fail1"), Exception("Fail2"), "Success"])

    steps = [
        {"name": "retry_step", "action": action, "compensation": lambda: None, "max_retries": 3}
    ]
    saga_id = orchestrator.create_saga("retry_saga", steps)

    result = orchestrator.execute_saga(saga_id)
    assert result is True

    status = orchestrator.get_saga_status(saga_id)
    assert status["steps"][0]["retry_count"] == 2
    assert action.call_count == 3

def test_max_retries_exceeded(orchestrator):
    action = MagicMock(side_effect=Exception("Fail"))
    steps = [
        {"name": "fail_step", "action": action, "compensation": lambda: None, "max_retries": 1}
    ]
    saga_id = orchestrator.create_saga("fail_retry_saga", steps)

    result = orchestrator.execute_saga(saga_id)
    assert result is False

    status = orchestrator.get_saga_status(saga_id)
    assert status["steps"][0]["retry_count"] == 2 # Initial + 1 retry? Or 0 + 2 attempts. Code increments retry_count.
    # Code: while retry_count <= max_retries: ... retry_count += 1

def test_concurrent_execution_prevention(orchestrator):
    steps = [{"name": "s1", "action": lambda: True, "compensation": lambda: True}]
    saga_id = orchestrator.create_saga("concurrent", steps)

    # Mock lock or running set to simulate running
    orchestrator._running_sagas.add(saga_id)

    result = orchestrator.execute_saga(saga_id)
    assert result is False

def test_not_found(orchestrator):
    assert orchestrator.execute_saga("missing") is False
    assert orchestrator.get_saga_status("missing") is None

def test_metrics_and_events(orchestrator):
    steps = [{"name": "s1", "action": lambda: True, "compensation": lambda: True}]
    saga_id = orchestrator.create_saga("metrics", steps)
    orchestrator.execute_saga(saga_id)

    metrics = orchestrator.get_metrics()
    assert metrics["total_sagas"] == 1
    assert metrics["completed"] == 1

    events = orchestrator.get_saga_events(saga_id)
    assert len(events) > 0
    assert events[0]["event_type"] == "saga_created"

def test_singleton():
    s1 = get_saga_orchestrator()
    s2 = get_saga_orchestrator()
    assert s1 is s2
