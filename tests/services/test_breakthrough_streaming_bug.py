import json

import pytest

from app.services.breakthrough_streaming import BreakthroughStreamingService


@pytest.mark.asyncio
async def test_breakthrough_streaming_json_injection_bug():
    """
    Verifies that the BreakthroughStreamingService correctly handles special characters
    in the text stream and does not produce invalid JSON.
    """
    service = BreakthroughStreamingService()

    # Input that contains characters that break JSON if not escaped properly
    input_text_chunks = ['He said, "Hello World!"', " and then left."]

    async def mock_generator():
        for chunk in input_text_chunks:
            yield chunk

    # Consume the stream
    stream = service.stream_with_smart_chunking(mock_generator())

    async for chunk in stream:
        # chunk format is: 'event: delta\ndata: {"text": "..."}\n\n'
        lines = chunk.strip().split("\n")
        for line in lines:
            if line.startswith("data: "):
                json_str = line[6:]
                try:
                    # This should not raise JSONDecodeError
                    data = json.loads(json_str)

                    # If empty data (completion event), skip check
                    if not data:
                        continue

                    # Verify content matches what we expect (approximately, due to chunking)
                    assert "text" in data
                except json.JSONDecodeError as e:
                    pytest.fail(f"Produced invalid JSON: {json_str}. Error: {e}")
