import pytest

from app.services.admin_chat_streaming_service import (AdminChatStreamingService, SmartTokenChunker,
                                                       SpeculativeDecoder, StreamingMetrics,
                                                       get_streaming_service)

# --- Unit Tests for Components ---


def test_smart_token_chunker_chunk_text():
    chunker = SmartTokenChunker()
    text = "one two three four five six"

    # Chunk size 2
    chunks = chunker.chunk_text(text, chunk_size=2)
    assert chunks == ["one two", "three four", "five six"]

    # Chunk size 3
    chunks = chunker.chunk_text(text, chunk_size=3)
    assert chunks == ["one two three", "four five six"]


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
    assert "hello " in plain_chunks[0] or "hello world " in plain_chunks[0]


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
    assert stats["total_tokens"] == 30
    assert stats["avg_latency_ms"] == 75.0
    assert stats["p50_latency_ms"] == 100.0  # sorted [50.0, 100.0], index 1 (int(2*0.5)=1)


def test_streaming_metrics_empty():
    metrics = StreamingMetrics()
    stats = metrics.get_stats()
    assert stats["total_streams"] == 0


# --- Service Tests ---


def test_service_initialization():
    service = AdminChatStreamingService()
    assert isinstance(service.metrics, StreamingMetrics)
    assert isinstance(service.speculative_decoder, SpeculativeDecoder)
    assert isinstance(service.chunker, SmartTokenChunker)


def test_service_stream_response():
    service = AdminChatStreamingService()
    text = "hello world"
    metadata = {"key": "value"}

    chunks = list(service.stream_response(text, metadata))

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


def test_singleton():
    s1 = get_streaming_service()
    s2 = get_streaming_service()
    assert s1 is s2
