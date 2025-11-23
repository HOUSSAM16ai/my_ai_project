# app/api/routers/admin.py
"""
Admin-facing API endpoints for the CogniForge platform.
This has been migrated to use the new Reality Kernel engines.
"""

import json
import jwt
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.core.ai_gateway import AIClient, get_ai_client
from app.core.database import AsyncSession, async_session_factory, get_db
from app.models import AdminConversation, AdminMessage, MessageRole, User

# --- JWT Configuration ---
# Reusing the config from ai_service.py as a temporary measure until IDENTITY-ENGINE is fully unified
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key")
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
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return int(user_id)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID in token")


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
    # Retrieve conversation history (limit to last 20 messages for context window)
    # To get the LAST 20 messages ordered by time ascending, we sort by time DESC, limit, then reverse.
    stmt = (
        select(AdminMessage)
        .where(AdminMessage.conversation_id == conversation.id)
        .order_by(AdminMessage.created_at.desc(), AdminMessage.id.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    # Convert to list to support reversal
    history_messages = list(result.scalars().all())

    # Reverse to get chronological order (ASC)
    # The DB query returned them DESC (newest first)
    history_messages.reverse()

    # Format messages for AI Client
    messages = []
    for msg in history_messages:
        role = msg.role
        # Enum values are already lowercase "user", "assistant"
        messages.append({"role": role.value, "content": msg.content})

    # Ensure the current question is included.
    # Since we just saved 'user_message', it might be in 'history_messages' if the limit wasn't reached
    # or if it was recent enough.
    if not messages or messages[-1]["content"] != question:
        messages.append({"role": "user", "content": question})

    async def response_generator():
        # Send the conversation ID immediately so the client can update its state
        init_payload = {
            "conversation_id": conversation.id,
            "title": conversation.title,
        }
        yield f"event: conversation_init\ndata: {json.dumps(init_payload)}\n\n"

        full_response = []
        try:
            # Stream the response from AI
            async for chunk in ai_client.stream_chat(messages):
                # Expecting chunk to be a dict, potentially with 'content' or similar structure
                # Adjust based on actual AIClient output structure.
                # Assuming chunk is a dict representing partial response or full object.

                # We assume chunk has a structure that json.dumps handles.
                # If we need to extract content for persistence, we need to know the structure.
                # Looking at mock in conftest: yield {"role": "assistant", "content": "Mocked response"}
                # Looking at OpenRouterAIClient: yield chunk (json from API)

                # We'll try to extract content if possible, or just dump it.
                # For persistence, we need the text content.

                content_part = ""
                if isinstance(chunk, dict):
                    # Try standard OpenAI/OpenRouter format
                    choices = chunk.get("choices", [])
                    if choices and len(choices) > 0:
                        delta = choices[0].get("delta", {})
                        content_part = delta.get("content", "")
                    else:
                        # Fallback or direct content
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

        finally:
            # 3. Save Assistant Message (after stream completes or disconnects)
            # This 'finally' block ensures we save what we have generated so far,
            # even if the client disconnects (GeneratorExit) or an error occurs.
            # CRITICAL FIX: We must use a NEW session, as the request-scoped 'db' session
            # might already be closed by FastAPI if the client disconnected.
            assistant_content = "".join(full_response)
            if assistant_content:
                try:
                    async with async_session_factory() as session:
                        assistant_msg = AdminMessage(
                            conversation_id=conversation.id,
                            role=MessageRole.ASSISTANT,
                            content=assistant_content,
                        )
                        session.add(assistant_msg)
                        await session.commit()
                except Exception as db_e:
                    # Log error but don't crash the generator close
                    print(f"Failed to save assistant message: {db_e}")

    return StreamingResponse(response_generator(), media_type="text/event-stream")
