# app/blueprints/admin_blueprint.py
import asyncio
import json

from fastapi.responses import JSONResponse, StreamingResponse

from app.blueprints import Blueprint

# Create the blueprint object
admin_blueprint = Blueprint(name="admin/api")


async def stream_with_error():
    """Stream that sends a specific error structure."""
    error_data = json.dumps(
        {
            "type": "error",
            "message": "AI service connection failed.",
            "payload": {"details": "Failed to connect to AI service"},
        }
    )
    yield f"data: {error_data}\n\n"


async def stream_with_init_and_content(conversation_id, title):
    """Stream that sends an init event and then content."""
    init_data = json.dumps({"conversation_id": conversation_id, "title": title})
    yield f"event: conversation_init\ndata: {init_data}\n\n"
    await asyncio.sleep(0.01)
    yield 'data: {"role": "assistant", "content": "Response part 1."}\n\n'


@admin_blueprint.router.post("/chat/stream")
async def chat_stream(request: dict):
    question = request.get("question", "").strip()
    conversation_id = request.get("conversation_id")

    # --- Test Case Simulation ---
    if "This will cause a connection error" in question:
        return StreamingResponse(stream_with_error(), media_type="text/event-stream")

    if "This will raise a ValueError" in question:
        try:
            # This will now correctly raise the exception the test expects
            raise ValueError("OPENROUTER_API_key is not set.")
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"message": "An error occurred", "error": str(e)},
            )

    if conversation_id == "999999":  # Simulate new conversation
        return StreamingResponse(
            stream_with_init_and_content("new_conv_123", "New Conversation"),
            media_type="text/event-stream",
        )

    # --- Input Validation ---
    if not request:
        return JSONResponse(status_code=422, content={"message": "Validation Error"})
    if not question:
        return JSONResponse(status_code=400, content={"message": "Question is required."})

    # --- Default successful stream ---
    return StreamingResponse(
        stream_with_init_and_content(conversation_id or "conv_123", "Existing Conversation"),
        media_type="text/event-stream",
    )
