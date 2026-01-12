import pytest

from app.core.superhuman_performance_optimizer import (
    RequestTelemetry,
    SuperhumanPerformanceOptimizer,
)


def test_request_telemetry_validation() -> None:
    valid = RequestTelemetry(model_id="model-alpha", success=True, latency_ms=10.5)
    valid.ensure_valid()

    with pytest.raises(ValueError):
        RequestTelemetry(model_id="", success=True, latency_ms=1.0).ensure_valid()

    with pytest.raises(ValueError):
        RequestTelemetry(model_id="model-alpha", success=True, latency_ms=-1.0).ensure_valid()

    with pytest.raises(ValueError):
        RequestTelemetry(
            model_id="model-alpha", success=True, latency_ms=1.0, tokens=-2
        ).ensure_valid()

    with pytest.raises(ValueError):
        RequestTelemetry(
            model_id="model-alpha", success=True, latency_ms=1.0, quality_score=1.5
        ).ensure_valid()


def test_record_request_updates_metrics() -> None:
    optimizer = SuperhumanPerformanceOptimizer()
    telemetry = RequestTelemetry(
        model_id="model-alpha",
        success=True,
        latency_ms=120.0,
        tokens=50,
        quality_score=0.8,
        recorded_at=123.0,
    )

    optimizer.record_request(telemetry)

    metrics = optimizer.metrics["model-alpha"]
    assert metrics.total_requests == 1
    assert metrics.successful_requests == 1
    assert metrics.failed_requests == 0
    assert metrics.empty_responses == 0
    assert metrics.avg_tokens_per_request == 50
    assert metrics.avg_quality_score == pytest.approx(0.8)
    assert metrics.p50_latency_ms == pytest.approx(120.0)
    assert metrics.p95_latency_ms == pytest.approx(120.0)
    assert metrics.p99_latency_ms == pytest.approx(120.0)
    assert metrics.last_request_time == pytest.approx(123.0)

    assert optimizer.total_requests == 1
    assert optimizer.total_latency_ms == pytest.approx(120.0)


def test_record_request_counts_empty_responses() -> None:
    optimizer = SuperhumanPerformanceOptimizer()
    telemetry = RequestTelemetry(
        model_id="model-beta",
        success=False,
        latency_ms=45.0,
        empty_response=True,
    )

    optimizer.record_request(telemetry)

    metrics = optimizer.metrics["model-beta"]
    assert metrics.total_requests == 1
    assert metrics.failed_requests == 1
    assert metrics.empty_responses == 1
    assert metrics.avg_tokens_per_request == pytest.approx(0.0)
    assert optimizer.total_requests == 1
    assert optimizer.total_latency_ms == pytest.approx(45.0)
