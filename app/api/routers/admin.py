# app/api/routers/admin.py
"""
واجهة برمجة تطبيقات المسؤول (Admin API).
---------------------------------------------------------
توفر هذه الوحدة نقاط النهاية (Endpoints) الخاصة بالمسؤولين،
وتعتمد بشكل كامل على خدمة `AdminChatBoundaryService` لفصل المسؤوليات.
تتبع نمط "Presentation Layer" فقط، ولا تحتوي على أي منطق عمل.

المعايير:
- توثيق شامل باللغة العربية.
- صرامة في تحديد الأنواع (Strict Typing).
- اعتماد كامل على حقن التبعيات (Dependency Injection).
"""

from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.schemas import ChatRequest
from app.core.ai_gateway import AIClient, get_ai_client
from app.core.database import async_session_factory, get_db
from app.core.di import get_logger
from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService

logger = get_logger(__name__)


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


def get_session_factory() -> Callable[[], AsyncSession]:
    """
    تبعية لاسترجاع مصنع الجلسات العالمي.
    ضروري للعمليات الخلفية التي تتطلب جلسات مستقلة.
    """
    return async_session_factory


def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminChatBoundaryService:
    """تبعية للحصول على خدمة حدود محادثة المسؤول."""
    return AdminChatBoundaryService(db)


def get_current_user_id(
    request: Request, service: AdminChatBoundaryService = Depends(get_admin_service)
) -> int:
    """
    استرجاع معرف المستخدم الحالي باستخدام منطق سياسات الخدمة.
    """
    auth_header = request.headers.get("Authorization")
    return service.validate_auth_header(auth_header)


@router.post("/api/chat/stream", summary="بث محادثة المسؤول (Admin Chat Stream)")
async def chat_stream(
    chat_request: ChatRequest,
    ai_client: AIClient = Depends(get_ai_client),
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
    session_factory: Callable[[], AsyncSession] = Depends(get_session_factory),
) -> StreamingResponse:
    """
    نقطة نهاية لبدء بث محادثة مع الذكاء الاصطناعي (Overmind).

    التدفق:
    1. استقبال السؤال.
    2. تفويض المعالجة لخدمة الحدود (Boundary Service).
    3. إرجاع استجابة تدفقية (StreamingResponse) بتنسيق SSE.

    Args:
        chat_request: نموذج طلب المحادثة.
        ai_client: عميل الذكاء الاصطناعي المحقون.
        user_id: معرف المستخدم الحالي.
        service: خدمة الحدود.
        session_factory: مصنع الجلسات للعمليات الخلفية.

    Returns:
        StreamingResponse: تدفق أحداث الخادم (SSE).
    """
    question = chat_request.question
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")

    # تنسيق تدفق المحادثة بالكامل عبر خدمة الحدود
    stream_generator = service.orchestrate_chat_stream(
        user_id,
        question,
        chat_request.conversation_id,
        ai_client,
        session_factory,
    )

    return StreamingResponse(
        stream_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # تعطيل التخزين المؤقت في Nginx
        },
    )


@router.get("/api/chat/latest", summary="استرجاع آخر محادثة (Get Latest Conversation)")
async def get_latest_chat(
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
) -> dict[str, Any]:
    """
    استرجاع تفاصيل آخر محادثة للمستخدم الحالي.
    مفيد لاستعادة الحالة عند إعادة تحميل الصفحة.
    """
    conversation_data = await service.get_latest_conversation_details(user_id)
    if not conversation_data:
        return {"conversation_id": None, "messages": []}
    return conversation_data


@router.get("/api/conversations", summary="سرد المحادثات (List Conversations)")
async def list_conversations(
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
) -> list[dict[str, Any]]:
    """
    استرجاع قائمة بجميع محادثات المستخدم.
    """
    return await service.list_user_conversations(user_id)


@router.get(
    "/api/conversations/{conversation_id}", summary="تفاصيل المحادثة (Conversation Details)"
)
async def get_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id),
    service: AdminChatBoundaryService = Depends(get_admin_service),
) -> dict[str, Any]:
    """
    استرجاع الرسائل والتفاصيل لمحادثة محددة.
    """
    return await service.get_conversation_details(user_id, conversation_id)
