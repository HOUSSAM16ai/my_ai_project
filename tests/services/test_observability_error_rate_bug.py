from app.services.api_observability_service import APIObservabilityService


def test_error_rate_calculation_under_load():
    """
    Verifies that the error rate is calculated correctly even when the number of errors
    exceeds the size of the error_buffer (500).

    Scenario:
    1. Send 600 requests, all resulting in 500 Internal Server Error.
    2. The metrics_buffer (size 10000) will hold all 600 requests.
    3. The error_buffer (size 500) will only hold the last 500 errors.
    4. Bug: Error rate calculated as len(error_buffer) / len(metrics_buffer) = 500 / 600 = 83.33%
    5. Expected: Error rate should be 100.0%
    """
    service = APIObservabilityService()

    # 1. Simulate 600 error requests
    total_requests = 600
    for _i in range(total_requests):
        service.record_request_metrics(
            endpoint="/api/test",
            method="GET",
            status_code=500,
            duration_ms=10.0,
            error="Test Error",
        )

    # 2. Get Snapshot
    snapshot = service.get_performance_snapshot()

    # 3. Assertions
    # Check buffer sizes to confirm the setup conditions
    assert len(service.metrics_buffer) == 600
    assert len(service.error_buffer) == 500  # Capped at 500

    # Verify Error Rate
    # With the bug, this is 500/600 * 100 = 83.33%
    # With the fix, this should be 100.0%
    assert snapshot.error_rate == 100.0, f"Error rate was {snapshot.error_rate}%, expected 100.0%"
