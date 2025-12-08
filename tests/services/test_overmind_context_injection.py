from unittest.mock import MagicMock, patch

import pytest

from app.overmind.planning.deep_indexer_v2.models import FileMetric, GlobalMetrics, IndexResult
from app.services.chat.context_service import get_context_service


def test_codebase_context_summary():
    """
    Verifies that the CodebaseContextService correctly generates a summary
    containing the requested metrics (LOC, Hotspots).
    """
    service = get_context_service()

    # Mock build_index to return a controlled result (IndexResult object)
    mock_index = IndexResult(
        files_scanned=10,
        global_metrics=GlobalMetrics(
            total_loc=12345,
            total_functions=50,
            avg_function_complexity=5.5,
            std_function_complexity=1.0,
            max_function_complexity=20,
            max_function_complexity_ref="ref"
        ),
        file_metrics=[
            FileMetric(
                path="app/main.py",
                file_hash="abc",
                loc=100,
                function_count=2,
                class_count=0,
                avg_function_complexity=1.0,
                max_function_complexity=1,
                tags=[],
                layer="core",
                entrypoint=False
            ),
            FileMetric(
                path="app/huge.py",
                file_hash="def",
                loc=5000,
                function_count=20,
                class_count=0,
                avg_function_complexity=10.0,
                max_function_complexity=20,
                tags=[],
                layer="core",
                entrypoint=False
            ),
        ],
        complexity_hotspots_top50=[],
        duplicate_function_bodies={},
        dependencies={},
        layers={},
        service_candidates=[],
        modules=[],
        functions=[],
        function_call_frequency_top50=[],
        index_version="v2",
        entrypoints=[],
        call_graph_edges_sample=[],
        cache_used=False,
        cached_files=0,
        changed_files=0,
        skipped_large_files=[],
        generated_at="now",
        config={},
        version_details={}
    )

    with patch("app.services.chat.context_service.build_index", return_value=mock_index):
        service.force_refresh()
        prompt = service.get_context_system_prompt()

        # Check basic Overmind Persona
        assert "Overmind CLI Mindgate" in prompt
        assert "Cognitive Map" in prompt

        # Check Metrics
        assert "LOC=12345" in prompt
        assert "funcs=50" in prompt

        # Check Top Files
        assert "app/huge.py" in prompt
        assert "loc=5000" in prompt


@pytest.mark.asyncio
async def test_admin_chat_injection():
    """
    Verifies that AdminChatStreamer injects the prompt.
    """
    from app.models import AdminConversation
    from app.services.admin.chat_streamer import AdminChatStreamer

    mock_persistence = MagicMock()
    streamer = AdminChatStreamer(mock_persistence)

    # Mock inputs
    conversation = AdminConversation(id=1, title="Test", user_id=1)
    history = []  # Empty history
    ai_client = MagicMock()

    # Mock stream_chat to return empty iterator
    async def mock_stream(*args, **kwargs):
        yield "response"

    ai_client.stream_chat = mock_stream

    session_factory = MagicMock()

    # Mock the context service injection
    with patch(
        "app.services.chat.context_service.CodebaseContextService.get_context_system_prompt",
        return_value="SYSTEM_PROMPT_INJECTED",
    ):
        # We need to mock orchestrator too to avoid complex dependencies
        with patch("app.services.admin.chat_streamer.get_chat_orchestrator") as mock_get_orch:
            mock_orch = MagicMock()
            mock_orch.detect_intent.return_value.intent = "chat"  # Standard chat
            mock_get_orch.return_value = mock_orch

            # Run the streamer
            async for _chunk in streamer.stream_response(
                1, conversation, "Hello", history, ai_client, session_factory
            ):
                pass

            # Verify history was modified
            assert len(history) >= 2  # System + User
            assert history[0]["role"] == "system"
            assert history[0]["content"] == "SYSTEM_PROMPT_INJECTED"
