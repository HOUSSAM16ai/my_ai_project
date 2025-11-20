# app/api/routers/admin.py
"""
Admin-facing API endpoints for the CogniForge platform.
This has been migrated to use the new Reality Kernel engines.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.ai_gateway import AIClient, get_ai_client
from app.core.database import AsyncSession, get_db


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    question: str
    conversation_id: str | None = None


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.post("/api/chat/stream", summary="Admin Chat Streaming Endpoint")
async def chat_stream(
    chat_request: ChatRequest,
    ai_client: AIClient = Depends(get_ai_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Handles POST requests to initiate a chat stream.
    This now uses the ENERGY-ENGINE (AIClient) and SPACE-ENGINE (AsyncSession)
    for all its operations.
    """
    question = chat_request.question
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")

    async def response_generator():
        try:
            async for chunk in ai_client.stream_chat([{"role": "user", "content": question}]):
                yield f"data: {json.dumps(chunk)}\\n\\n"
        except Exception as e:
            error_payload = {
                "type": "error",
                "payload": {"error": f"Failed to connect to AI service: {e}"},
            }
            yield f"data: {json.dumps(error_payload)}\\n\\n"

    return StreamingResponse(response_generator(), media_type="text/event-stream")
