import json

import pytest

from app.services.admin.streaming.config import StreamingConfig
from app.services.admin.streaming.service import (
    AdaptivePacingStrategy,
    AdminChatStreamingService,
    AdminChatStreamingServiceFactory,
    SmartTokenChunker,
    SpeculativeDecoder,
    StreamingMetrics,
    get_streaming_service,
    reset_streaming_service,
    set_streaming_service_factory,
)


@pytest.fixture(autouse=True)
def reset_streaming_singleton() -> None:
    reset_streaming_service()
    set_streaming_service_factory(AdminChatStreamingServiceFactory())
    yield
    reset_streaming_service()
    set_streaming_service_factory(AdminChatStreamingServiceFactory())


# --- Unit Tests for Components ---


def test_smart_token_chunker_chunk_text():
    chunker = SmartTokenChunker()
    text = "one two three four five six"

    # Chunk size 2
    chunks = chunker.chunk_text(text, chunk_size=2)
    # With whitespace preservation:
    # "one two"
    # " three four"
    # " five six"
    assert chunks == ["one two", " three four", " five six"]

    # Chunk size 3
    chunks = chunker.chunk_text(text, chunk_size=3)
    # "one two three"
    # " four five six"
    assert chunks == ["one two three", " four five six"]


def test_smart_token_chunker_smart_chunk():
    chunker = SmartTokenChunker()
    text = "code block ```import os``` and more text"

    chunks = list(chunker.smart_chunk(text))
    # Expecting: "code block ", "```import os```", "and more text " (depending on chunk size)

    assert "```import os```" in chunks

    # Test plain text
    plain_text = "hello world"
    plain_chunks = list(chunker.smart_chunk(plain_text))
    assert len(plain_chunks) > 0
    # The chunker might return "hello world" in one chunk if size is large enough
    # or "hello " + "world" if split.
    # We check that the content is present.
    combined = "".join(plain_chunks)
    assert "hello world" in combined


def test_speculative_decoder_patterns():
    decoder = SpeculativeDecoder()

    # Common patterns
    assert "function_name(" in decoder.predict_next_tokens("def ")
    assert "os" in decoder.predict_next_tokens("import ")

    # Context based
    assert "next" in decoder.predict_next_tokens("the")
    assert "a" in decoder.predict_next_tokens("is")

    # No match
    assert decoder.predict_next_tokens("unknown_word_xyz") == []


def test_streaming_metrics():
    metrics = StreamingMetrics()
    metrics.record_chunk(10, 50.0)  # size 10, 50ms
    metrics.record_chunk(20, 100.0)  # size 20, 100ms

    stats = metrics.get_stats()
    assert stats["total_streams"] == 2
    assert stats["total_sessions"] == 0
    assert stats["total_tokens"] == 30
    assert stats["avg_latency_ms"] == 75.0
    assert stats["p50_latency_ms"] == 100.0  # sorted [50.0, 100.0], index 1 (int(2*0.5)=1)
    assert stats["avg_session_ms"] == 0.0
    assert stats["p95_session_ms"] == 0.0


def test_streaming_metrics_empty():
    metrics = StreamingMetrics()
    stats = metrics.get_stats()
    assert stats["total_streams"] == 0
    assert stats["total_sessions"] == 0
    assert stats["avg_session_ms"] == 0.0


def test_streaming_session_recording():
    metrics = StreamingMetrics()
    metrics.record_session(100.0)
    metrics.record_session(300.0)

    stats = metrics.get_stats()

    assert stats["total_sessions"] == 2
    assert stats["avg_session_ms"] == 200.0
    assert stats["p95_session_ms"] == 300.0


# --- Service Tests ---


def test_service_initialization():
    service = AdminChatStreamingService()
    assert isinstance(service.metrics, StreamingMetrics)
    assert isinstance(service.speculative_decoder, SpeculativeDecoder)
    assert isinstance(service.chunker, SmartTokenChunker)
    assert isinstance(service.pacing_strategy, AdaptivePacingStrategy)


@pytest.mark.asyncio
async def test_service_stream_response():
    service = AdminChatStreamingService()
    text = "hello world"
    metadata = {"key": "value"}

    chunks = []
    async for chunk in service.stream_response(text, metadata):
        chunks.append(chunk)

    # Verify Metadata
    assert "event: metadata" in chunks[0]
    assert '{"key": "value"}' in chunks[0]

    # Verify Delta
    delta_found = False
    for chunk in chunks:
        if "event: delta" in chunk:
            delta_found = True
            assert "text" in chunk
    assert delta_found

    # Verify Complete
    assert "event: complete" in chunks[-1]


@pytest.mark.asyncio
async def test_service_async_stream_response():
    service = AdminChatStreamingService()

    async def mock_gen():
        yield "hello "
        yield "world "
        yield "async"

    chunks = []
    async for chunk in service.async_stream_response(mock_gen(), {"meta": "data"}):
        chunks.append(chunk)

    assert "event: metadata" in chunks[0]
    assert "event: complete" in chunks[-1]

    # Check content
    content = "".join(chunks)
    assert "hello" in content
    assert "world" in content


@pytest.mark.asyncio
async def test_stream_response_emits_complete_when_empty_text():
    service = AdminChatStreamingService()

    chunks = [chunk async for chunk in service.stream_response("", {"trace": "id"})]

    assert len(chunks) == 2
    assert chunks[0].startswith("event: metadata")
    completion = json.loads(chunks[-1].split("data: ")[1])

    assert completion["chunks_sent"] == 0
    assert completion["total_time_ms"] >= 0
    stats = service.get_metrics()
    assert stats["total_sessions"] >= 1


@pytest.mark.asyncio
async def test_async_stream_response_emits_complete_without_tokens():
    service = AdminChatStreamingService()

    async def empty_gen():
        if False:  # pragma: no cover - يضمن طبيعة المولّد
            yield ""  # pragma: no cover

    chunks = [chunk async for chunk in service.async_stream_response(empty_gen())]

    assert len(chunks) == 1
    assert chunks[0].startswith("event: complete")
    completion = json.loads(chunks[0].split("data: ")[1])
    assert completion["chunks_sent"] == 0


def test_singleton():
    s1 = get_streaming_service()
    s2 = get_streaming_service()
    assert s1 is s2


def test_singleton_factory_override_resets_instance():
    baseline = get_streaming_service()

    class CustomFactory(AdminChatStreamingServiceFactory):
        def __init__(self) -> None:
            super().__init__(config=StreamingConfig(optimal_chunk_size=2))

        def create(self) -> AdminChatStreamingService:
            return AdminChatStreamingService(config=self.config)

    set_streaming_service_factory(CustomFactory())
    custom = get_streaming_service()

    assert custom is not baseline
    assert custom.config.optimal_chunk_size == 2


def test_custom_pacing_strategy_is_used():
    calls: list[float] = []

    class FakePacing:
        def delay_ms(self, metrics: StreamingMetrics, config: StreamingConfig) -> float:
            calls.append(metrics.total_streams + config.min_chunk_delay_ms)
            return 0

    service = AdminChatStreamingService(pacing_strategy=FakePacing())
    service.metrics.record_chunk(5, 10.0)

    delay = service.pacing_strategy.delay_ms(service.metrics, service.config)

    assert delay == 0
    assert calls


class SteppedTimer:
    def __init__(self, step: float = 0.1) -> None:
        self.current = 0.0
        self.step = step

    def now(self) -> float:
        value = self.current
        self.current += self.step
        return value


@pytest.mark.asyncio
async def test_service_records_session_metrics():
    timer = SteppedTimer()

    async def fast_sleep(_: float) -> None:
        return None

    service = AdminChatStreamingService(timer=timer, sleep=fast_sleep)

    chunks = []
    async for chunk in service.stream_response("hello world"):
        chunks.append(chunk)

    stats = service.get_metrics()
    assert stats["total_sessions"] == 1
    assert stats["avg_session_ms"] == pytest.approx(300.0)
    assert any("event: complete" in chunk for chunk in chunks)


class ManualTimer:
    def __init__(self) -> None:
        self.current = 0.0

    def now(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


@pytest.mark.asyncio
async def test_session_chunk_counts_are_isolated_per_stream():
    timer = ManualTimer()

    async def advance_sleep(delay_seconds: float) -> None:
        timer.advance(delay_seconds)

    class ZeroPacing:
        def delay_ms(self, metrics: StreamingMetrics, config: StreamingConfig) -> float:  # pragma: no cover - stub
            return 0

    config = StreamingConfig(optimal_chunk_size=1, min_chunk_delay_ms=0, max_chunk_delay_ms=0)
    service = AdminChatStreamingService(
        config=config,
        timer=timer,
        sleep=advance_sleep,
        pacing_strategy=ZeroPacing(),
    )

    first_chunks = [chunk async for chunk in service.stream_response("one two")]
    first_complete = json.loads(first_chunks[-1].split("data: ")[1])

    second_chunks = [chunk async for chunk in service.stream_response("three four five")]
    second_complete = json.loads(second_chunks[-1].split("data: ")[1])

    assert first_complete["chunks_sent"] == 2
    assert second_complete["chunks_sent"] == 3
    assert first_complete["chunks_sent"] != second_complete["chunks_sent"]
    assert service.metrics.total_streams == 5
