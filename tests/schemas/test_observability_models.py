from __future__ import annotations

from datetime import datetime

from app.schemas.observability import (
    AiOpsResponse,
    AlertModel,
    AlertsResponse,
    MetricsData,
    MetricsResponse,
    PerformanceSnapshotModel,
    SnapshotResponse,
)


def test_metrics_response_accepts_plain_dict_for_aiops():
    snapshot = PerformanceSnapshotModel(
        timestamp=datetime(2024, 5, 1),
        avg_latency_ms=10.0,
        p50_latency_ms=8.0,
        p95_latency_ms=12.0,
        p99_latency_ms=14.0,
        p999_latency_ms=16.0,
        requests_per_second=30.0,
        error_rate=0.01,
        active_requests=3,
        request_count=100,
        error_count=1,
    )

    metrics = MetricsResponse(
        timestamp=datetime(2024, 5, 1),
        metrics=MetricsData(
            api_performance=snapshot,
            aiops_health={"anomalies_detected": 0, "system_health_score": 99.5},
        ),
    )

    assert metrics.metrics.aiops_health["system_health_score"] == 99.5


def test_aiops_and_alerts_legacy_wrappers_preserve_payloads():
    alerts = AlertsResponse(alerts=[{"id": "a1", "severity": "high", "message": "down"}])
    aiops = AiOpsResponse(data={"ok": True, "score": 90})

    assert alerts.alerts[0]["severity"] == "high"
    assert aiops.data["score"] == 90


def test_alert_model_allows_serializable_details():
    alert = AlertModel(
        id="alert-1",
        severity="critical",
        message="database unreachable",
        timestamp=datetime(2024, 2, 1),
        details={"attempts": 3, "hosts": ["db-1", "db-2"], "metadata": {"region": "eu"}},
    )

    assert alert.details == {"attempts": 3, "hosts": ["db-1", "db-2"], "metadata": {"region": "eu"}}


def test_snapshot_response_accepts_model_and_dict():
    model_payload = PerformanceSnapshotModel(
        timestamp=datetime(2024, 6, 1),
        avg_latency_ms=11.0,
        p50_latency_ms=9.0,
        p95_latency_ms=13.0,
        p99_latency_ms=15.0,
        p999_latency_ms=17.0,
        requests_per_second=31.0,
        error_rate=0.02,
        active_requests=4,
        request_count=101,
        error_count=2,
    )

    response_from_model = SnapshotResponse(snapshot=model_payload)
    response_from_dict = SnapshotResponse(
        snapshot={
            "timestamp": datetime(2024, 6, 1),
            "avg_latency_ms": 11.0,
            "p50_latency_ms": 9.0,
            "p95_latency_ms": 13.0,
            "p99_latency_ms": 15.0,
            "p999_latency_ms": 17.0,
            "requests_per_second": 31.0,
            "error_rate": 0.02,
            "active_requests": 4,
            "request_count": 101,
            "error_count": 2,
        }
    )

    assert response_from_model.snapshot.requests_per_second == 31.0
    assert response_from_dict.snapshot["avg_latency_ms"] == 11.0
