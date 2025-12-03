import pytest
from app.services.api_observability_service import APIObservabilityService

@pytest.fixture
def observability_service():
    return APIObservabilityService(sla_target_ms=20.0)

def test_anomaly_detection_false_negative_due_to_baseline_pollution(observability_service):
    """
    Verifies that updating the baseline BEFORE checking for anomalies causes false negatives.

    Scenario:
    1. Baseline established at 100ms.
    2. An incoming request has 525ms latency.
    3. Threshold is 5x baseline.

    Expected Behavior (Correct Logic):
    - Baseline = 100ms
    - Threshold = 500ms
    - 525ms > 500ms -> Anomaly Detected!

    Current Buggy Behavior:
    - New Baseline = 0.1 * 525 + 0.9 * 100 = 52.5 + 90 = 142.5ms
    - New Threshold = 5 * 142.5 = 712.5ms
    - 525ms < 712.5ms -> Anomaly MISSED!
    """

    # 1. Establish stable baseline at 100ms
    # We do this by feeding 100ms many times
    # Initial: empty
    # 1: B=100
    # ...
    for _ in range(50):
        observability_service.record_request_metrics(
            endpoint="/api/bug", method="GET", status_code=200, duration_ms=100.0
        )

    # Verify baseline is approx 100
    current_baseline = observability_service.baseline_latency["/api/bug"]
    assert abs(current_baseline - 100.0) < 1.0, f"Baseline should be ~100, got {current_baseline}"

    # 2. Send a request that SHOULD be an anomaly (525ms > 5x 100ms)
    # But due to the bug, it won't be detected.
    observability_service.record_request_metrics(
        endpoint="/api/bug", method="GET", status_code=200, duration_ms=525.0
    )

    # 3. Check for alerts
    alerts = observability_service.get_all_alerts(severity="critical")

    # This assertion CONFIRMS the bug exists.
    # If the bug was fixed, this would be != 0 (it would detect the anomaly).
    # Since we expect the bug to be present, we assert len(alerts) == 0.
    # After fixing, we will update this test to assert len(alerts) == 1.

    # Wait, the instruction is to "write a new test case that specifically fails before your fix and passes after it".
    # So I should write the assertion expecting the CORRECT behavior (alert detected).
    # If the bug exists, this test will FAIL.

    assert len(alerts) == 1, "Anomaly should be detected! If 0, the baseline pollution bug masked it."
    assert alerts[0]["anomaly_type"] == "extreme_latency"
