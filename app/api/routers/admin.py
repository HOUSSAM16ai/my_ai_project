# app/api/routers/admin.py
"""
Admin-facing API endpoints for the CogniForge platform.
Refactored to use 'AdminChatBoundaryService' for Separation of Concerns.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, model_validator

from app.core.ai_gateway import AIClient, get_ai_client
from app.core.database import AsyncSession, async_session_factory, get_db
from app.core.di import get_logger
from app.models import MessageRole
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
    return StreamingResponse(
        service.stream_chat_response_safe(
            user_id, conversation, question, history, ai_client, session_factory
        ),
        media_type="text/event-stream",
    )


@router.get("/api/chat/latest", summary="Get Latest Conversation")
async def get_latest_chat(
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
):
    """
    Retrieves the latest conversation for the current user.
    Pure Router implementation: Delegates entirely to Boundary Service.
    """
    conversation_data = await service.get_latest_conversation_details(user_id)
    if not conversation_data:
        return {"conversation_id": None, "messages": []}
    return conversation_data


@router.get("/api/conversations", summary="List Conversations")
async def list_conversations(
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
):
    """
    Retrieves a list of conversations for the current user.
    Pure Router implementation: Delegates entirely to Boundary Service.
    """
    return await service.list_user_conversations(user_id)


@router.get("/api/conversations/{conversation_id}", summary="Get Conversation Details")
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
):
    """
    Retrieves messages for a specific conversation.
    Pure Router implementation: Delegates entirely to Boundary Service.
    """
    return await service.get_conversation_details(user_id, conversation_id)
