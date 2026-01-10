"""اختبارات نماذج طلبات خدمة المراقبة."""

from microservices.observability_service.main import TelemetryRequest
from microservices.observability_service.models import MetricType


def test_telemetry_request_labels_are_isolated() -> None:
    first = TelemetryRequest(
        metric_id="m1",
        service_name="svc",
        metric_type=MetricType.LATENCY,
        value=1.0,
    )
    second = TelemetryRequest(
        metric_id="m2",
        service_name="svc",
        metric_type=MetricType.LATENCY,
        value=2.0,
    )

    first.labels["region"] = "eu"

    assert second.labels == {}
    assert first.labels == {"region": "eu"}
