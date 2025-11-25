# app/api/routers/admin.py
"""
Admin-facing API endpoints for the CogniForge platform.
This has been migrated to use the new Reality Kernel engines.
"""

import asyncio
import json

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.config.settings import get_settings
from app.core.ai_gateway import AIClient, get_ai_client
from app.core.database import AsyncSession, async_session_factory, get_db
from app.models import AdminConversation, AdminMessage, MessageRole

# --- Configuration ---
ALGORITHM = "HS256"


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    question: str
    conversation_id: str | None = None


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


# --- Security ---
def get_current_user_id(request: Request) -> int:
    """
    Retrieves the current user ID from the Authorization header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # For now, we require auth.
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return int(user_id)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Invalid user ID in token") from e


@router.post("/api/chat/stream", summary="Admin Chat Streaming Endpoint")
async def chat_stream(
    chat_request: ChatRequest,
    ai_client: AIClient = Depends(get_ai_client),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Handles POST requests to initiate a chat stream.
    This now uses the ENERGY-ENGINE (AIClient) and SPACE-ENGINE (AsyncSession)
    for all its operations.
    """
    question = chat_request.question
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")

    # 1. Handle Conversation Persistence
    conversation = None
    if chat_request.conversation_id:
        # Try to find existing conversation
        try:
            conv_id_int = int(chat_request.conversation_id)
            stmt = select(AdminConversation).where(
                AdminConversation.id == conv_id_int, AdminConversation.user_id == user_id
            )
            result = await db.execute(stmt)
            conversation = result.scalar_one_or_none()
        except ValueError:
            pass  # Invalid ID format, treat as new

    if not conversation:
        conversation = AdminConversation(title=question[:50], user_id=user_id)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

    # 2. Save User Message
    user_message = AdminMessage(
        conversation_id=conversation.id, role=MessageRole.USER, content=question
    )
    db.add(user_message)
    await db.commit()

    # 3. Prepare Context
    stmt = (
        select(AdminMessage)
        .where(AdminMessage.conversation_id == conversation.id)
        .order_by(AdminMessage.created_at.desc(), AdminMessage.id.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    history_messages = list(result.scalars().all())
    history_messages.reverse()

    messages = []
    for msg in history_messages:
        role = msg.role
        messages.append({"role": role.value, "content": msg.content})

    if not messages or messages[-1]["content"] != question:
        messages.append({"role": "user", "content": question})

    # --- SUPERHUMAN STREAMING & QUANTUM PERSISTENCE SHIELD ---
    # streaming_service = get_streaming_service() # Reserved for V4 integration

    async def response_generator():
        # Send init event
        init_payload = {
            "conversation_id": conversation.id,
            "title": conversation.title,
        }
        yield f"event: conversation_init\ndata: {json.dumps(init_payload)}\n\n"

        full_response = []

        # QUANTUM SHIELD: Atomic persistence function
        async def safe_persist():
            assistant_content = "".join(full_response)
            if not assistant_content:
                assistant_content = "Error: No response received from AI service."

            try:
                # Use a FRESH session because the original 'db' dependency
                # might be closed if the request was cancelled.
                async with async_session_factory() as session:
                    assistant_msg = AdminMessage(
                        conversation_id=conversation.id,
                        role=MessageRole.ASSISTANT,
                        content=assistant_content,
                    )
                    session.add(assistant_msg)
                    await session.commit()
            except Exception as db_e:
                # Log error but ensure we don't crash the loop (though this is end of life anyway)
                print(f"Failed to save assistant message: {db_e}")

        try:
            # Use the AI client directly but format output to match what StreamingService might expect if we used it fully.
            # For now, we keep the iteration logic here but could use service.stream_response if we adapted it.
            # The key request was to fix the weakness (persistence), so we focus on that.

            # However, to use the "Superhuman" service for chunking (if we wanted), we would pipe it.
            # Given the time constraint and "one weakness" directive, fixing persistence is the priority.

            async for chunk in ai_client.stream_chat(messages):
                content_part = ""
                if isinstance(chunk, dict):
                    choices = chunk.get("choices", [])
                    if choices and len(choices) > 0:
                        delta = choices[0].get("delta", {})
                        content_part = delta.get("content", "")
                    else:
                        content_part = chunk.get("content", "")

                if content_part:
                    full_response.append(content_part)

                yield f"data: {json.dumps(chunk)}\n\n"

        except GeneratorExit:
            # Client disconnected!
            # Activate Quantum Shield to save what we have.
            # We use asyncio.shield to protect the save operation from the cancellation.
            await asyncio.shield(safe_persist())
            raise # Re-raise to let the server handle the close properly

        except Exception as e:
            error_payload = {
                "type": "error",
                "payload": {"error": f"Failed to connect to AI service: {e}"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            # Also persist on error
            await asyncio.shield(safe_persist())

        else:
            # Normal completion
            await asyncio.shield(safe_persist())

    return StreamingResponse(response_generator(), media_type="text/event-stream")
