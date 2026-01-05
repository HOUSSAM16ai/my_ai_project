from app.telemetry.events import EventPayload, EventTracker, EventType
from app.telemetry.metrics import MetricRecord, MetricsManager
from app.telemetry.structured_logging import LogRecord, LoggingManager


def test_metric_record_tracks_histogram_and_traces() -> None:
    manager = MetricsManager()
    record = MetricRecord(
        name="latency_ms",
        value=120.5,
        labels={"path": "/health", "method": "GET"},
        trace_id="trace-1",
        span_id="span-1",
    )

    manager.record_metric(record)

    assert manager.stats["metrics_recorded"] == 1
    assert list(manager.histograms["latency_ms"])[0] == 120.5
    assert manager.trace_metrics["trace-1"][0].exemplar_span_id == "span-1"


def test_log_record_keeps_exception_and_trace_links() -> None:
    manager = LoggingManager()
    error = RuntimeError("boom")
    manager.log(
        LogRecord(
            level="ERROR",
            message="failed",
            context={"service": "demo"},
            exception=error,
            trace_id="trace-2",
            span_id="span-2",
        )
    )

    stored = manager.logs_buffer[-1]
    assert stored.context == {"service": "demo"}
    assert stored.trace_id == "trace-2"
    assert stored.exception == {"type": "RuntimeError", "message": "boom"}


def test_event_tracker_enriches_and_deduplicates() -> None:
    tracker = EventTracker(batch_size=2)
    payload = EventPayload(event_type=EventType.USER, name="login", user_id="u1")

    first_id = tracker.track(payload)
    duplicate_id = tracker.track(payload)

    assert first_id == duplicate_id
    assert tracker.stats["duplicates_filtered"] == 1
    # second unique event triggers batch processing (clearing event_batch)
    tracker.track(EventPayload(event_type=EventType.USER, name="logout", user_id="u1"))
    assert tracker.event_batch == []
    assert tracker.events[-1].context["server"] == "cogniforge"
