import pytest

from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.middleware.observability.analytics_adapter import AnalyticsAdapter
from app.middleware.observability.performance_profiler import PerformanceProfiler
from app.middleware.observability.telemetry_bridge import TelemetryBridge


async def _dummy_app(scope, receive, send):
    return None


class _FakeTime:
    def __init__(self, values: list[float]):
        self._values = iter(values)

    def time(self) -> float:
        return next(self._values)


def test_telemetry_bridge_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    bridge = TelemetryBridge(_dummy_app, {"exporters": ["prometheus"]})
    ctx = RequestContext(method="POST", path="/submit")
    ctx.user_id = "user-1"
    ctx.trace_id = "trace-123"
    ctx.span_id = "span-456"
    ctx.add_metadata("telemetry_bridge_start", 10.0)

    fake_time = _FakeTime([20.0])
    monkeypatch.setattr("app.middleware.observability.telemetry_bridge.time", fake_time)

    snapshot = bridge._prepare_telemetry_data(ctx, MiddlewareResult.success())

    assert snapshot.duration == pytest.approx(10.0)
    assert snapshot.to_dict()["trace_id"] == "trace-123"
    assert snapshot.to_dict()["path"] == "/submit"


def test_telemetry_bridge_exports(monkeypatch: pytest.MonkeyPatch) -> None:
    bridge = TelemetryBridge(_dummy_app, {"exporters": ["datadog"]})
    ctx = RequestContext(path="/items")
    ctx.add_metadata("telemetry_bridge_start", 5.0)

    fake_time = _FakeTime([8.0])
    monkeypatch.setattr("app.middleware.observability.telemetry_bridge.time", fake_time)

    exports: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        bridge,
        "_export_to",
        lambda exporter, payload: exports.append((exporter, payload)),
    )

    bridge.on_complete(ctx, MiddlewareResult.success())

    assert bridge.export_count == 1
    assert exports[0][0] == "datadog"
    assert exports[0][1]["duration"] == pytest.approx(3.0)


def test_analytics_event_build(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = AnalyticsAdapter(_dummy_app, {"platforms": ["mixpanel"]})
    ctx = RequestContext(path="/users", method="GET")
    fake_time = _FakeTime([42.0])
    monkeypatch.setattr("app.middleware.observability.analytics_adapter.time", fake_time)

    sent: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(
        adapter,
        "_send_to_platform",
        lambda platform, event: sent.append((platform, event)),
    )

    adapter.on_complete(ctx, MiddlewareResult.success())

    assert adapter.events_sent == 1
    assert sent[0][0] == "mixpanel"
    assert sent[0][1]["event_type"] == "page_view"
    assert sent[0][1]["status_code"] == 200


def test_analytics_skips_health(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = AnalyticsAdapter(_dummy_app, {"platforms": ["mixpanel"]})
    ctx = RequestContext(path="/health")
    fake_time = _FakeTime([100.0])
    monkeypatch.setattr("app.middleware.observability.analytics_adapter.time", fake_time)

    sent: list[dict[str, object]] = []
    monkeypatch.setattr(adapter, "_send_to_platform", lambda *_: sent.append({}))

    adapter.on_complete(ctx, MiddlewareResult.success())

    assert adapter.events_sent == 0
    assert sent == []


def test_performance_profiler_collects(monkeypatch: pytest.MonkeyPatch) -> None:
    profiler = PerformanceProfiler(_dummy_app, {"max_latencies": 5})
    fake_time = _FakeTime([1.0, 1.1, 2.0, 2.25])
    monkeypatch.setattr("app.middleware.observability.performance_profiler.time", fake_time)

    ctx_fast = RequestContext(path="/fast")
    profiler.process_request(ctx_fast)
    profiler.on_complete(ctx_fast, MiddlewareResult.success())

    ctx_slow = RequestContext(path="/slow")
    profiler.process_request(ctx_slow)
    profiler.on_complete(ctx_slow, MiddlewareResult.success())

    stats = profiler.get_statistics()

    assert stats["profiled_count"] == 2
    assert stats["p95_latency_ms"] >= stats["p50_latency_ms"]
    assert stats["tracked_endpoints"]["/fast"]["average_duration"] == pytest.approx(100.0)
    assert stats["tracked_endpoints"]["/slow"]["average_duration"] == pytest.approx(250.0)
    assert ctx_fast.get_metadata("performance_profile") == {
        "duration_ms": pytest.approx(100.0),
        "endpoint": "/fast",
    }
