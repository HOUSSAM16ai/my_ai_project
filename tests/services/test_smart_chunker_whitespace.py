
import pytest
from app.services.admin_chat_streaming_service import SmartTokenChunker

def test_chunk_text_preserves_newlines():
    """Test that chunk_text preserves newlines which are critical for Markdown formatting."""
    text = "Line 1\nLine 2\nLine 3"
    chunker = SmartTokenChunker()

    # Use a large chunk size to get everything in one go, or at least see how it handles the internal structure
    chunks = chunker.chunk_text(text, chunk_size=10)

    # The current implementation joins with " ", so it becomes "Line 1 Line 2 Line 3"
    joined = "".join(chunks)
    assert "Line 1\nLine 2\nLine 3" in joined

def test_chunk_text_preserves_indentation():
    """Test that chunk_text preserves indentation (multiple spaces)."""
    text = "def func():\n    return True"
    chunker = SmartTokenChunker()

    chunks = chunker.chunk_text(text, chunk_size=10)
    joined = "".join(chunks)

    assert "    return True" in joined
