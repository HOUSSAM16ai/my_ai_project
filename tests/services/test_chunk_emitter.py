from __future__ import annotations

import pytest

from app.services.admin.streaming.emission import MS_TO_SECONDS, ChunkEmitter, Timer
from app.services.admin.streaming.formatters import EventFormatter
from app.services.admin.streaming.metrics import SessionRecorder, StreamingMetrics


class FakeFormatter(EventFormatter):
    def format_event(self, event_type: str, payload: dict[str, str | int | float | bool]) -> str:  # pragma: no cover - stub
        return f"{event_type}:{payload}"


class FakeTimer(Timer):
    def __init__(self, timestamps: list[float]) -> None:
        self.timestamps = timestamps
        self.index = 0

    def now(self) -> float:
        current = self.timestamps[self.index]
        self.index += 1
        return current


@pytest.mark.parametrize("text,timestamps", [("hello", [1.0, 1.1]), ("مرحبا", [10.0, 10.05])])
def test_chunk_emitter_records_latency_and_size(text: str, timestamps: list[float]) -> None:
    metrics = StreamingMetrics()
    emitter = ChunkEmitter(formatter=FakeFormatter(), metrics=metrics, timer=FakeTimer(timestamps))

    event = emitter.emit_delta(text)

    assert event == f"delta:{{'text': '{text}'}}"
    assert metrics.total_streams == 1
    assert metrics.total_tokens == len(text)
    assert metrics.chunk_times[-1] == pytest.approx((timestamps[1] - timestamps[0]) * MS_TO_SECONDS)


def test_chunk_emitter_formats_generic_event() -> None:
    emitter = ChunkEmitter(formatter=FakeFormatter(), metrics=StreamingMetrics(), timer=FakeTimer([0.0]))

    payload = {"trace_id": "123"}
    event = emitter.format_event("metadata", payload)

    assert event == "metadata:{'trace_id': '123'}"


def test_chunk_emitter_updates_session_recorder() -> None:
    metrics = StreamingMetrics()
    timer = FakeTimer([0.0, 0.1, 0.2])
    session = SessionRecorder(timer=timer)
    emitter = ChunkEmitter(formatter=FakeFormatter(), metrics=metrics, timer=timer)

    emitter.emit_delta("مرحبا", session=session)

    assert session.chunk_count == 1
    assert session.token_count == len("مرحبا")
    assert metrics.total_streams == 1
