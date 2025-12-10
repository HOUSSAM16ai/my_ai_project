"""
Test for Context Service Integration.
Verifies that the codebase indexer runs and generates a summary.
"""
from app.services.chat.context_service import get_context_service

def test_context_service_generation():
    service = get_context_service()

    # Run the generation
    summary = service._refresh_index()

    # Updated assertions for "Deep Indexer V2 Enterprise" format
    assert "### Project Stats" in summary
    assert "FILES_SCANNED=" in summary
    assert "### Top Files (by LOC)" in summary
    assert "### Architecture Layers" in summary

    # Check if system prompt gets it
    prompt = service.get_context_system_prompt()
    assert "Overmind CLI Mindgate" in prompt
    assert summary in prompt
