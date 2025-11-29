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
from app.core.di import get_logger
from app.models import AdminConversation, AdminMessage, MessageRole

logger = get_logger(__name__)

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
def get_session_factory():
    """Dependency to get the global session factory."""
    return async_session_factory


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
    session_factory=Depends(get_session_factory),
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
            """
            Safely persists the assistant's message to the database.
            Uses a fresh session to ensure robustness against request cancellation.
            """
            assistant_content = "".join(full_response)
            if not assistant_content:
                assistant_content = "Error: No response received from AI service."

            try:
                # Use a FRESH session because the original 'db' dependency
                # might be closed if the request was cancelled.
                async with session_factory() as session:
                    assistant_msg = AdminMessage(
                        conversation_id=conversation.id,
                        role=MessageRole.ASSISTANT,
                        content=assistant_content,
                    )
                    session.add(assistant_msg)
                    await session.commit()
            except Exception as db_e:
                logger.error(f"Failed to save assistant message: {db_e}")

        # Context manager for guaranteed persistence
        class StreamingPersistenceContext:
            def __init__(self):
                self.is_persisted = False

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if not self.is_persisted:
                    # Log cancellation if applicable
                    if exc_type is asyncio.CancelledError:
                        logger.warning(
                            "Client disconnected during chat stream. Persisting partial response.",
                            extra={"conversation_id": conversation.id},
                        )

                    # Ensure persistence
                    await asyncio.shield(safe_persist())
                    self.is_persisted = True

        try:
            async with StreamingPersistenceContext():
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

        except Exception as e:
            error_payload = {
                "type": "error",
                "payload": {"error": f"Failed to connect to AI service: {e}"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            # Context manager handles persistence even here if it bubbled up,
            # but since we yield error data, we might exit cleanly from the try block
            # or raise. If we yield, we are still inside the generator.
            # Actually, if Exception is caught here, we yield data.
            # The context manager's __aexit__ will run after this block finishes (generator close).

    return StreamingResponse(response_generator(), media_type="text/event-stream")


@router.get("/api/chat/latest", summary="Get Latest Conversation")
async def get_latest_chat(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Retrieves the latest conversation for the current user.
    """
    stmt = (
        select(AdminConversation)
        .where(AdminConversation.user_id == user_id)
        .order_by(AdminConversation.created_at.desc(), AdminConversation.id.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        return {"conversation_id": None, "messages": []}

    stmt = (
        select(AdminMessage)
        .where(AdminMessage.conversation_id == conversation.id)
        .order_by(AdminMessage.created_at, AdminMessage.id)
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return {
        "conversation_id": conversation.id,
        "title": conversation.title,
        "messages": [
            {
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ],
    }
