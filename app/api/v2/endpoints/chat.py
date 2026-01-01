"""
Chat endpoints with streaming support.
"""

import logging
import time
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.v2.dependencies import (
    get_ai_client_dependency,
    get_chat_orchestrator,
    get_current_user_id,
)
from app.api.v2.schemas import ChatRequest, ChatResponse
from app.services.chat.orchestrator import ChatOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
    ai_client: AIClient = Depends(get_ai_client_dependency),
    user_id: int = Depends(get_current_user_id),
) -> StreamingResponse:
    """
    Stream chat response.

    Complexity: 2
    """

    async def generate() -> AsyncGenerator[str, None]:
        try:
            async for chunk in orchestrator.process(
                question=request.question,
                user_id=user_id,
                conversation_id=request.conversation_id or 0,
                ai_client=ai_client,
                history_messages=[],
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}", extra={"user_id": user_id})
            yield f"data: [ERROR] {e!s}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: ChatOrchestrator = Depends(get_chat_orchestrator),
    ai_client: AIClient = Depends(get_ai_client_dependency),
    user_id: int = Depends(get_current_user_id),
) -> ChatResponse:
    """
    Non-streaming chat endpoint.

    Complexity: 2
    """
    start_time = time.time()

    try:
        chunks = []
        async for chunk in orchestrator.process(
            question=request.question,
            user_id=user_id,
            conversation_id=request.conversation_id or 0,
            ai_client=ai_client,
            history_messages=[],
        ):
            chunks.append(chunk)

        answer = "".join(chunks)

        return ChatResponse(
            answer=answer,
            conversation_id=request.conversation_id or 0,
            metadata={
                "processing_time": time.time() - start_time,
            },
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", extra={"user_id": user_id})
        raise HTTPException(status_code=500, detail=str(e)) from e
