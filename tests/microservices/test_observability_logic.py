"""اختبارات منطق خدمة المراقبة لضمان وضوح القواعد التحليلية."""

from datetime import UTC, datetime

from microservices.observability_service.logic import (
    build_baseline,
    build_capacity_plan,
    derive_root_causes,
    detect_anomaly,
    serialize_capacity_plan,
)
from microservices.observability_service.models import (
    AnomalyDetection,
    AnomalySeverity,
    AnomalyType,
    LoadForecast,
    MetricType,
    TelemetryData,
)


def test_build_baseline_returns_expected_statistics() -> None:
    """يتأكد من أن خط الأساس يعكس الإحصاءات المتوقعة للقيم."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

    baseline = build_baseline(values)

    assert baseline["mean"] == 5.5
    assert baseline["median"] == 5.5
    assert baseline["p95"] == 10.0
    assert baseline["p99"] == 10.0


def test_detect_anomaly_flags_error_rate_increase() -> None:
    """يتأكد من أن زيادة معدل الأخطاء تُعرّف كشذوذ عالي الخطورة."""
    thresholds = {
        MetricType.ERROR_RATE: {"threshold": 0.05},
        MetricType.LATENCY: {"zscore": 3.0},
        MetricType.REQUEST_RATE: {"zscore": 2.5},
    }
    baseline = {"mean": 0.02, "median": 0.02, "stdev": 0.0, "p95": 0.05, "p99": 0.05}
    data = TelemetryData(
        metric_id="metric-1",
        service_name="billing",
        metric_type=MetricType.ERROR_RATE,
        value=0.12,
        timestamp=datetime.now(UTC),
    )

    anomaly = detect_anomaly(data, baseline, thresholds)

    assert anomaly is not None
    assert anomaly.anomaly_type == AnomalyType.ERROR_RATE_INCREASE
    assert anomaly.severity == AnomalySeverity.HIGH


def test_detect_anomaly_uses_zscore_for_latency() -> None:
    """يتأكد من أن انحراف الكمون العالي ينتج شذوذًا مناسبًا."""
    thresholds = {
        MetricType.ERROR_RATE: {"threshold": 0.05},
        MetricType.LATENCY: {"zscore": 3.0},
        MetricType.REQUEST_RATE: {"zscore": 2.5},
    }
    baseline = {"mean": 10.0, "median": 10.0, "stdev": 1.0, "p95": 12.0, "p99": 13.0}
    data = TelemetryData(
        metric_id="metric-2",
        service_name="search",
        metric_type=MetricType.LATENCY,
        value=20.0,
        timestamp=datetime.now(UTC),
    )

    anomaly = detect_anomaly(data, baseline, thresholds)

    assert anomaly is not None
    assert anomaly.anomaly_type == AnomalyType.LATENCY_SPIKE
    assert anomaly.severity in {AnomalySeverity.HIGH, AnomalySeverity.CRITICAL}


def test_derive_root_causes_compiles_multiple_signals() -> None:
    """يتأكد من أن التحليل يجمع الأسباب المتعددة عند توفرها."""
    anomaly = AnomalyDetection(
        anomaly_id="a-1",
        service_name="checkout",
        anomaly_type=AnomalyType.LATENCY_SPIKE,
        severity=AnomalySeverity.HIGH,
        detected_at=datetime.now(UTC),
        metric_value=200.0,
        expected_value=100.0,
        confidence=0.9,
        description="Latency spike",
    )
    service_metrics = [
        TelemetryData(
            metric_id="cpu",
            service_name="checkout",
            metric_type=MetricType.CPU_USAGE,
            value=85.0,
            timestamp=datetime.now(UTC),
        ),
        TelemetryData(
            metric_id="mem",
            service_name="checkout",
            metric_type=MetricType.MEMORY_USAGE,
            value=95.0,
            timestamp=datetime.now(UTC),
        ),
        TelemetryData(
            metric_id="err",
            service_name="checkout",
            metric_type=MetricType.ERROR_RATE,
            value=0.2,
            timestamp=datetime.now(UTC),
        ),
    ]

    causes = derive_root_causes(anomaly, service_metrics)

    assert "High CPU usage detected" in causes
    assert "Memory exhaustion detected" in causes
    assert "Correlated with increased error rate" in causes


def test_serialize_capacity_plan_exposes_required_fields() -> None:
    """يتأكد من أن خطة السعة تتحول إلى حمولة قابلة للإرسال."""
    forecast = LoadForecast(
        forecast_id="f-1",
        service_name="search",
        forecast_timestamp=datetime.now(UTC),
        predicted_load=200.0,
        confidence_interval=(180.0, 220.0),
        model_accuracy=0.9,
        generated_at=datetime.now(UTC),
    )

    plan = build_capacity_plan(
        service_name="search",
        forecast=forecast,
        current_capacity=100.0,
        safety_factor=1.5,
        horizon_hours=24,
    )

    payload = serialize_capacity_plan(plan)

    assert payload is not None
    assert payload["service_name"] == "search"
    assert payload["recommended_capacity"] == 300.0
