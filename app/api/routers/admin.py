# app/api/routers/admin.py
"""
Admin-facing API endpoints for the CogniForge platform.
Refactored to use 'AdminChatBoundaryService' for Separation of Concerns.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, model_validator
from sqlalchemy import select

from app.core.ai_gateway import AIClient, get_ai_client
from app.core.database import AsyncSession, async_session_factory, get_db
from app.core.di import get_logger
from app.models import AdminConversation, AdminMessage, MessageRole
from app.services.admin_chat_boundary_service import AdminChatBoundaryService

logger = get_logger(__name__)


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""

    question: str
    conversation_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "message" in data and "question" not in data:
                data["question"] = data["message"]
            if "conversation_id" in data and data["conversation_id"] is not None:
                data["conversation_id"] = str(data["conversation_id"])
        return data


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


def get_session_factory():
    """Dependency to get the global session factory."""
    return async_session_factory


def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminChatBoundaryService:
    """Dependency to get the Admin Chat Boundary Service."""
    return AdminChatBoundaryService(db)


def get_current_user_id(
    request: Request, service: AdminChatBoundaryService = Depends(get_admin_service)
) -> int:
    """
    Retrieves the current user ID using the Service's Policy Boundary logic.
    """
    auth_header = request.headers.get("Authorization")
    return service.validate_auth_header(auth_header)


@router.post("/api/chat/stream", summary="Admin Chat Streaming Endpoint")
async def chat_stream(
    chat_request: ChatRequest,
    ai_client: AIClient = Depends(get_ai_client),
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
    session_factory=Depends(get_session_factory),
):
    """
    Handles POST requests to initiate a chat stream.
    Now uses AdminChatBoundaryService for orchestration.
    """
    question = chat_request.question
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")

    # 1. Get or Create Conversation (Data Boundary)
    conversation = await service.get_or_create_conversation(
        user_id, question, chat_request.conversation_id
    )

    # 2. Save User Message (Data Boundary)
    await service.save_message(conversation.id, MessageRole.USER, question)

    # 3. Prepare Context (Data Boundary)
    history = await service.get_chat_history(conversation.id)

    # 4. Stream Response (Service Boundary)
    # Pass session_factory for the internal safe persistence context

    import json

    async def safe_stream_generator():
        try:
            async for chunk in service.stream_chat_response(
                user_id, conversation, question, history, ai_client, session_factory
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Stream interrupted: {e}", exc_info=True)
            error_payload = {
                "type": "error",
                "payload": {"details": f"Service Error: {e}"},
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        safe_stream_generator(),
        media_type="text/event-stream",
    )


@router.get("/api/chat/latest", summary="Get Latest Conversation")
async def get_latest_chat(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Retrieves the latest conversation for the current user.
    Refactoring Note: Kept simple read logic here or could move to service.
    For 80/20 rule, we focus on the complex chat_stream first, but let's clean this up too slightly.
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
                "created_at": msg.created_at.isoformat() if msg.created_at else "",
            }
            for msg in messages
        ],
    }


@router.get("/api/conversations", summary="List Conversations")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    Retrieves a list of conversations for the current user.
    """
    stmt = (
        select(AdminConversation)
        .where(AdminConversation.user_id == user_id)
        .order_by(AdminConversation.created_at.desc(), AdminConversation.id.desc())
    )
    result = await db.execute(stmt)
    conversations = result.scalars().all()

    results = []
    for conv in conversations:
        c_at = conv.created_at.isoformat() if conv.created_at else ""
        u_at = c_at
        if hasattr(conv, "updated_at") and conv.updated_at:
            u_at = conv.updated_at.isoformat()

        results.append({"id": conv.id, "title": conv.title, "created_at": c_at, "updated_at": u_at})
    return results


@router.get("/api/conversations/{conversation_id}", summary="Get Conversation Details")
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
):
    """
    Retrieves messages for a specific conversation.
    """
    # Verify ownership via Service Boundary (handles Admin override)
    conversation = await service.verify_conversation_access(user_id, conversation_id)

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
                "created_at": msg.created_at.isoformat() if msg.created_at else "",
            }
            for msg in messages
        ],
    }
