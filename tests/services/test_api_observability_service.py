import asyncio
import threading
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request

from app.services.api_observability_service import (
    APIObservabilityService,
    get_observability_service,
    monitor_performance,
)


@pytest.fixture
def observability_service() -> Generator[APIObservabilityService, None, None]:
    """Fixture to provide a fresh APIObservabilityService instance for each test."""
    service = APIObservabilityService(sla_target_ms=20.0)
    yield service


class TestAPIObservabilityService:
    def test_initialization(self, observability_service: APIObservabilityService):
        assert observability_service.sla_target_ms == 20.0
        assert len(observability_service.metrics_buffer) == 0
        assert len(observability_service.latency_buffer) == 0
        assert len(observability_service.error_buffer) == 0
        assert len(observability_service.active_requests) == 0

    def test_generate_trace_id(self, observability_service: APIObservabilityService):
        trace_id_1 = observability_service.generate_trace_id()
        trace_id_2 = observability_service.generate_trace_id()
        assert isinstance(trace_id_1, str)
        assert len(trace_id_1) == 16
        assert trace_id_1 != trace_id_2

    def test_start_request_trace(self, observability_service: APIObservabilityService):
        trace_info = observability_service.start_request_trace("/api/test", "GET")
        assert "trace_id" in trace_info
        assert "span_id" in trace_info
        assert "timestamp" in trace_info

        trace_id = trace_info["trace_id"]
        assert trace_id in observability_service.active_requests

    def test_record_request_metrics(self, observability_service: APIObservabilityService):
        trace_info = observability_service.start_request_trace("/api/test", "GET")
        trace_id = trace_info["trace_id"]

        observability_service.record_request_metrics(
            endpoint="/api/test",
            method="GET",
            status_code=200,
            duration_ms=15.0,
            trace_id=trace_id,
        )

        assert len(observability_service.metrics_buffer) == 1
        assert len(observability_service.latency_buffer) == 1
        assert trace_id not in observability_service.active_requests

        metric = observability_service.metrics_buffer[0]
        assert metric.endpoint == "/api/test"
        assert metric.duration_ms == 15.0
        assert metric.status_code == 200

    def test_record_error_metrics(self, observability_service: APIObservabilityService):
        observability_service.record_request_metrics(
            endpoint="/api/error",
            method="POST",
            status_code=500,
            duration_ms=45.0,
            error="Internal Server Error",
        )

        assert len(observability_service.metrics_buffer) == 1
        assert len(observability_service.error_buffer) == 1

        metric = observability_service.error_buffer[0]
        assert metric.status_code == 500
        assert metric.error == "Internal Server Error"

    def test_get_performance_snapshot_empty(self, observability_service: APIObservabilityService):
        snapshot = observability_service.get_performance_snapshot()
        assert snapshot.avg_latency_ms == 0.0
        assert snapshot.requests_per_second == 0.0
        assert snapshot.error_rate == 0.0

    def test_get_performance_snapshot_metrics(self, observability_service: APIObservabilityService):
        # Add some dummy data
        latencies = [10.0, 20.0, 30.0, 100.0]
        for lat in latencies:
            observability_service.record_request_metrics(
                endpoint="/api/test", method="GET", status_code=200, duration_ms=lat
            )

        # Add an error
        observability_service.record_request_metrics(
            endpoint="/api/test", method="GET", status_code=500, duration_ms=50.0
        )
        latencies.append(50.0)

        snapshot = observability_service.get_performance_snapshot()

        assert snapshot.avg_latency_ms == sum(latencies) / len(latencies)
        assert snapshot.p50_latency_ms == 30.0  # Median of 10, 20, 30, 50, 100
        assert snapshot.error_rate == 20.0  # 1 error out of 5 requests (20%)

    def test_calculate_rps(self, observability_service: APIObservabilityService):
        # Mock time to ensure metrics are considered "recent"
        with patch("app.services.api_observability_service.datetime") as mock_datetime:
            now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = now

            # Metrics from 30 seconds ago
            # metric_time = now - timedelta(seconds=30)

            # We need to manually construct metrics because record_request_metrics uses datetime.now()
            # which we are mocking, but we want to control the timestamp of the metric specifically.
            # However, since we mock datetime.now(), record_request_metrics will use the mocked time.

            # Record 10 requests at "now" (which is mocked)
            for _ in range(10):
                observability_service.record_request_metrics(
                    endpoint="/api/rps", method="GET", status_code=200, duration_ms=10
                )

            # Now advance time by 10 seconds for the calculation
            future = now + timedelta(seconds=10)
            mock_datetime.now.return_value = future

            rps = observability_service._calculate_rps()
            # 10 requests over 10 seconds (time_span = future - first_metric_timestamp)
            # The first metric timestamp was 'now'. So span is 10s.
            assert rps == 1.0

    def test_anomaly_detection_critical(self, observability_service: APIObservabilityService):
        # Establish baseline
        for _ in range(10):
            observability_service.record_request_metrics(
                endpoint="/api/baseline", method="GET", status_code=200, duration_ms=10.0
            )

        # Trigger critical anomaly ( > 5x baseline)
        # Note: The service updates baseline BEFORE checking for anomalies.
        # Current baseline = 10.0
        # New request = 100.0
        # New baseline = 0.1 * 100 + 0.9 * 10 = 19.0
        # Critical threshold = 5 * 19.0 = 95.0
        # 100.0 > 95.0, so this should trigger an alert.
        observability_service.record_request_metrics(
            endpoint="/api/baseline", method="GET", status_code=200, duration_ms=100.0
        )

        alerts = observability_service.get_all_alerts(severity="critical")
        assert len(alerts) == 1
        assert alerts[0]["anomaly_type"] == "extreme_latency"

    def test_anomaly_detection_high(self, observability_service: APIObservabilityService):
        # Establish baseline
        for _ in range(10):
            observability_service.record_request_metrics(
                endpoint="/api/baseline", method="GET", status_code=200, duration_ms=10.0
            )

        # Trigger high anomaly ( > 3x baseline but < 5x)
        observability_service.record_request_metrics(
            endpoint="/api/baseline", method="GET", status_code=200, duration_ms=40.0
        )

        alerts = observability_service.get_all_alerts(severity="high")
        assert len(alerts) == 1
        assert alerts[0]["anomaly_type"] == "high_latency"

    def test_sla_violation(self, observability_service: APIObservabilityService):
        # SLA target is 20ms

        # First request establishes baseline (no check)
        observability_service.record_request_metrics(
            endpoint="/api/sla", method="GET", status_code=200, duration_ms=10.0
        )

        # Second request checks for SLA violation
        observability_service.record_request_metrics(
            endpoint="/api/sla", method="GET", status_code=200, duration_ms=25.0
        )

        alerts = observability_service.get_all_alerts(severity="medium")
        assert len(alerts) == 1
        assert alerts[0]["anomaly_type"] == "sla_violation"

    def test_get_endpoint_analytics(self, observability_service: APIObservabilityService):
        observability_service.record_request_metrics(
            endpoint="/api/analytics", method="GET", status_code=200, duration_ms=10.0
        )
        observability_service.record_request_metrics(
            endpoint="/api/analytics", method="GET", status_code=200, duration_ms=20.0
        )

        analytics = observability_service.get_endpoint_analytics("/api/analytics")
        assert analytics["status"] == "success"
        assert analytics["total_requests"] == 2
        assert analytics["avg_latency_ms"] == 15.0
        assert analytics["min_latency_ms"] == 10.0
        assert analytics["max_latency_ms"] == 20.0

    def test_get_endpoint_analytics_no_data(self, observability_service: APIObservabilityService):
        analytics = observability_service.get_endpoint_analytics("/api/unknown")
        assert analytics["status"] == "no_data"

    def test_get_sla_compliance(self, observability_service: APIObservabilityService):
        # 1 request compliant (10ms < 20ms)
        observability_service.record_request_metrics(
            endpoint="/api/sla", method="GET", status_code=200, duration_ms=10.0
        )
        # 1 request violation (30ms > 20ms)
        observability_service.record_request_metrics(
            endpoint="/api/sla", method="GET", status_code=200, duration_ms=30.0
        )

        compliance = observability_service.get_sla_compliance()
        assert compliance["total_requests"] == 2
        assert compliance["violations"] == 1
        assert compliance["compliance_rate_percent"] == 50.0
        assert compliance["sla_status"] == "violated"

    def test_thread_safety(self, observability_service: APIObservabilityService):
        """Test that methods are thread-safe."""

        def worker():
            for _ in range(100):
                observability_service.record_request_metrics(
                    endpoint="/api/thread", method="GET", status_code=200, duration_ms=10.0
                )

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(observability_service.metrics_buffer) == 1000
        assert observability_service.get_endpoint_analytics("/api/thread")["total_requests"] == 1000

    def test_monitor_performance_decorator_async(self):
        """Test the monitor_performance decorator with an async function."""

        # We need to patch the global observability_service used by the decorator
        with patch("app.services.api_observability_service.observability_service") as mock_service:

            @monitor_performance
            async def monitored_func(req: Request):
                await asyncio.sleep(0.01)
                return {"message": "success"}

            # Create a mock request
            mock_request = MagicMock(spec=Request)
            mock_request.url.path = "/api/decorated"
            mock_request.method = "POST"

            # Run the decorated function
            asyncio.run(monitored_func(req=mock_request))

            # Verify record_request_metrics was called
            assert mock_service.record_request_metrics.called
            call_args = mock_service.record_request_metrics.call_args[1]
            assert call_args["endpoint"] == "/api/decorated"
            assert call_args["method"] == "POST"
            assert call_args["status_code"] == 200
            assert call_args["duration_ms"] > 0

    def test_monitor_performance_decorator_exception(self):
        """Test the monitor_performance decorator when an exception occurs."""

        with patch("app.services.api_observability_service.observability_service") as mock_service:

            @monitor_performance
            async def failing_func():
                raise ValueError("Something went wrong")

            with pytest.raises(ValueError):
                asyncio.run(failing_func())

            assert mock_service.record_request_metrics.called
            call_args = mock_service.record_request_metrics.call_args[1]
            assert call_args["status_code"] == 500
            assert "Something went wrong" in call_args["error"]

    def test_get_observability_service_global(self):
        service = get_observability_service()
        assert isinstance(service, APIObservabilityService)
