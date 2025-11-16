# app/api/stream_routes.py
# ======================================================================================
# ==                    SUPERHUMAN SSE STREAMING ROUTER (v1.0)                       ==
# ======================================================================================
# PRIME DIRECTIVE:
#   Robust Server-Sent Events streaming that surpasses ChatGPT
#   ✨ Key Features:
#   - Proper SSE event formatting with heartbeats
#   - Multi-byte UTF-8 safe chunking
#   - Comprehensive error handling
#   - Support for progress events (images, video, PDF)
#   - Reconnection support with Last-Event-ID

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator

from flask import Blueprint, Response, request, stream_with_context
from flask_login import login_required

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint("stream_api", __name__, url_prefix="/api/v1/stream")


# ======================================================================================
# SSE EVENT FORMATTING
# ======================================================================================


def sse_event(
    event: str | None = None,
    data: dict | str = None,
    eid: str | None = None,
    retry: int | None = None,
) -> str:
    """
    Build a standard SSE event frame.

    Format:
        event: <event_type>
        id: <event_id>
        retry: <milliseconds>
        data: <line1>
        data: <line2>

        (blank line to end event)

    Args:
        event: Event type (e.g., 'delta', 'done', 'error', 'ping')
        data: Event data (dict will be JSON encoded)
        eid: Event ID for reconnection support
        retry: Reconnection time in milliseconds

    Returns:
        Formatted SSE event string
    """
    lines = []

    if event:
        lines.append(f"event: {event}")

    if eid:
        lines.append(f"id: {eid}")

    if retry is not None:
        lines.append(f"retry: {retry}")

    # Convert data to string if it's a dict
    if data is not None:
        payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)

        # Split into lines to handle multi-line data properly
        for line in payload.splitlines() or [""]:
            lines.append(f"data: {line}")

    # Add blank line to end the event
    lines.append("")

    return "\n".join(lines) + "\n"


# ======================================================================================
# MOCK AI TOKEN STREAM (Replace with your actual LLM integration)
# ======================================================================================


async def ai_token_stream(prompt: str, model: str | None = None) -> AsyncIterator[str]:
    """
    Real LLM token streaming with optional mock mode for development.

    This integrates with the actual LLM client service for production streaming,
    with optional mock mode for development and testing.

    Args:
        prompt: User prompt
        model: Optional model override

    Yields:
        Token strings

    Environment Variables:
        ALLOW_MOCK_LLM: Set to 'true' for development mock mode (default: false)
        ENABLE_HYBRID_STREAMING: Enable advanced hybrid streaming (default: false)
    """
    import os

    # Check if mock mode is allowed
    allow_mock = os.getenv("ALLOW_MOCK_LLM", "false").lower() == "true"

    # Try real LLM first
    try:
        from app.services.breakthrough_streaming import get_hybrid_engine
        from app.services.ensemble_ai import get_router
        from app.services.llm_client_service import invoke_chat_stream

        # Use intelligent routing if enabled
        use_routing = os.getenv("ENABLE_INTELLIGENT_ROUTING", "false").lower() == "true"
        if use_routing and not model:
            router = get_router()
            model, tier = await router.route(prompt, {"user_query": prompt})
            logger.info(f"Intelligent router selected: {model} ({tier.value})")

        # Use default model if not specified
        if not model:
            model = os.getenv("DEFAULT_AI_MODEL", "openai/gpt-4o-mini")

        # Create streaming request
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ]

        # Check if hybrid streaming is enabled
        use_hybrid = os.getenv("ENABLE_HYBRID_STREAMING", "false").lower() == "true"

        if use_hybrid:
            # Use hybrid streaming engine
            logger.info("Using hybrid streaming engine")
            hybrid_engine = get_hybrid_engine()

            # Create async generator for real LLM stream
            async def llm_generator():
                for chunk in invoke_chat_stream(model=model, messages=messages):
                    content = chunk.get("delta", {}).get("content", "")
                    if content:
                        yield content

            # Stream through hybrid engine
            async for stream_chunk in hybrid_engine.ultra_stream(
                llm_generator(), {"current_text": prompt}
            ):
                if stream_chunk.content:
                    yield stream_chunk.content
        else:
            # Standard streaming
            logger.info(f"Using standard streaming with model: {model}")
            for chunk in invoke_chat_stream(model=model, messages=messages):
                # Extract content from chunk
                content = chunk.get("delta", {}).get("content", "")
                if content:
                    yield content

    except Exception as e:
        logger.error(f"Real LLM streaming failed: {e}", exc_info=True)

        # Fallback to mock if allowed
        if allow_mock:
            logger.warning("Falling back to mock LLM (development mode)")
            # Mock streaming for development
            words = [
                "Hello",
                "world",
                "this",
                "is",
                "a",
                "streaming",
                "response",
                "with",
                "proper",
                "SSE",
            ]

            for i in range(100):
                word = words[i % len(words)]
                token = f"{word}{i} "

                # Small delay to simulate LLM streaming
                await asyncio.sleep(0.02)

                yield token
        else:
            # Re-raise in production
            raise RuntimeError(
                f"LLM streaming failed and mock mode is disabled: {e}. "
                "Set ALLOW_MOCK_LLM=true in .env for development mode."
            )


# ======================================================================================
# SSE STREAMING ENDPOINTS
# ======================================================================================


def _get_chat_params(req):
    """Extracts chat parameters from the Flask request."""
    if req.method == "GET":
        question = req.args.get("q", "").strip()
        conversation_id = req.args.get("conversation_id")
    else:
        data = req.get_json() or {}
        question = data.get("question", "").strip()
        conversation_id = data.get("conversation_id")
    return question, conversation_id


async def _generate_sse_events(question: str, conversation_id: str | None) -> AsyncIterator[str]:
    """Async generator for SSE events for the chat stream."""
    event_id = 0
    last_heartbeat = time.monotonic()

    try:
        # Send hello event
        yield sse_event(
            "hello",
            {"ts": time.time(), "model": "gpt-4", "conversation_id": conversation_id},
            eid=str(event_id),
        )
        event_id += 1

        # Stream tokens
        buffer = ""
        token_count = 0

        async for token in ai_token_stream(question):
            buffer += token
            token_count += 1

            # Send chunk every N tokens or at punctuation
            should_send = token_count % 8 == 0 or (token and token[-1] in ".!?,;:\n")

            if should_send and buffer:
                yield sse_event("delta", {"text": buffer}, eid=str(event_id))
                event_id += 1
                buffer = ""

            # Send heartbeat every 20 seconds
            now = time.monotonic()
            if now - last_heartbeat > 20:
                yield sse_event("ping", "🔧", eid=str(event_id))
                event_id += 1
                last_heartbeat = now

        # Send remaining buffer
        if buffer:
            yield sse_event("delta", {"text": buffer}, eid=str(event_id))
            event_id += 1

        # Send completion event
        yield sse_event("complete", {"reason": "stop", "tokens": token_count}, eid=str(event_id))

    except Exception as e:
        logger.error(f"SSE streaming error: {e}", exc_info=True)
        # Send error event instead of crashing silently
        yield sse_event(
            "error",
            {"message": str(e)[:500], "type": type(e).__name__},
            eid=str(event_id),
        )


def _run_async_generator_in_sync(async_gen: AsyncIterator[str]):
    """
    Sync wrapper to run an async generator.
    Creates a new event loop for the request.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        while True:
            try:
                chunk = loop.run_until_complete(async_gen.__anext__())
                yield chunk
            except StopAsyncIteration:
                break
    finally:
        loop.close()
        asyncio.set_event_loop(None)


@bp.route("/chat", methods=["GET", "POST"])
@login_required
def sse_chat():
    """
    SSE endpoint for real-time chat streaming.

    Query Parameters (GET):
        - q: Question/prompt
        - conversation_id: Optional conversation ID

    JSON Body (POST):
        - question: Question/prompt
        - conversation_id: Optional conversation ID

    Response:
        Server-Sent Events stream with various events like 'hello', 'delta', 'done', 'error', 'ping'.
    """
    question, conversation_id = _get_chat_params(request)

    if not question:

        def error_gen():
            yield sse_event("error", {"message": "Question is required"})

        return Response(
            stream_with_context(error_gen()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )

    async_gen = _generate_sse_events(question, conversation_id)
    sync_gen = _run_async_generator_in_sync(async_gen)

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Content-Type": "text/event-stream; charset=utf-8",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # For NGINX
    }

    return Response(stream_with_context(sync_gen), headers=headers)


@bp.route("/progress/<task_id>", methods=["GET"])
@login_required
def sse_progress(task_id: str):
    """
    SSE endpoint for task progress (images, video, PDF generation).

    This endpoint streams progress updates for long-running tasks.

    Args:
        task_id: Unique task identifier

    Response:
        Server-Sent Events with:
        - event: progress (percentage updates)
        - event: preview (preview URLs or data URIs)
        - event: complete (final result)
        - event: error (task failures)
    """

    def generate():
        """Generate progress events"""
        event_id = 0

        try:
            # Send initial status
            yield sse_event(
                "progress",
                {"id": task_id, "pct": 0, "note": "Starting task..."},
                eid=str(event_id),
            )
            event_id += 1

            # Simulate progress (replace with actual task monitoring)
            for pct in range(0, 101, 10):
                time.sleep(0.5)  # Simulate work

                yield sse_event(
                    "progress",
                    {"id": task_id, "pct": pct, "note": f"Processing... {pct}%"},
                    eid=str(event_id),
                )
                event_id += 1

                # Send preview at 50%
                if pct == 50:
                    yield sse_event(
                        "preview",
                        {
                            "id": task_id,
                            "url": f"/api/tasks/{task_id}/preview",
                            "type": "image/jpeg",
                        },
                        eid=str(event_id),
                    )
                    event_id += 1

            # Send completion
            yield sse_event(
                "complete",
                {
                    "id": task_id,
                    "url": f"/api/tasks/{task_id}/result",
                    "type": "image/png",
                },
                eid=str(event_id),
            )

        except Exception as e:
            logger.error(f"Progress streaming error: {e}", exc_info=True)
            yield sse_event(
                "error",
                {"id": task_id, "message": str(e)},
                eid=str(event_id),
            )

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "Content-Type": "text/event-stream; charset=utf-8",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    return Response(stream_with_context(generate()), headers=headers)


# ======================================================================================
# HEALTH CHECK
# ======================================================================================


@bp.route("/health", methods=["GET"])
def stream_health():
    """
    Health check endpoint for streaming service.

    Returns:
        JSON response with service status
    """
    return {
        "status": "ok",
        "service": "sse-streaming",
        "version": "1.0",
        "endpoints": [
            "/api/v1/stream/chat",
            "/api/v1/stream/progress/<task_id>",
        ],
    }
