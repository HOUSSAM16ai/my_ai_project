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

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.admin import (
    ChatRequest,
    ConversationDetailsResponse,
    ConversationSummaryResponse,
)
from app.core.ai_gateway import AIClient, get_ai_client
from app.core.database import async_session_factory, get_db
from app.core.di import get_logger
from app.core.domain.user import User
from app.deps.auth import CurrentUser, require_roles
from app.services.boundaries.admin_chat_boundary_service import AdminChatBoundaryService
from app.services.chat.contracts import ChatDispatchRequest
from app.services.chat.dispatcher import ChatRoleDispatcher, build_chat_dispatcher
from app.services.chat.orchestrator import ChatOrchestrator
from app.services.rbac import ADMIN_ROLE

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


def get_chat_actor(
    current: CurrentUser = Depends(require_roles(ADMIN_ROLE)),
) -> CurrentUser:
    """تبعية تُلزم صفة الإداري قبل استخدام قنوات الدردشة الإدارية."""

    return current


def get_current_user_id(current: CurrentUser = Depends(get_chat_actor)) -> int:
    """
    إرجاع معرف المستخدم الحالي بعد التحقق من صلاحيات الأسئلة التعليمية.

    يعتمد هذا التابع على تبعية `get_chat_actor` لضمان أن المستدعي يملك
    التصاريح اللازمة قبل متابعة أي عمليات بث أو استعلامات خاصة بالمحادثات
    الإدارية.

    Args:
        current: كائن المستخدم الحالي المزود بالأدوار والصلاحيات.

    Returns:
        int: معرف المستخدم الموثق.
    """

    return current.user.id


async def get_actor_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    الحصول على كائن المستخدم الفعلي بالاعتماد على معرفه.

    يوفر هذا التابع طبقة تجريد تُمكِّن من تجاوز التحقق في الاختبارات عبر
    إعادة تعريف `get_current_user_id`، مع الحفاظ على مسار التحقق الأساسي في
    بيئة الإنتاج.

    Args:
        user_id: معرف المستخدم المستخرج من التبعيات السابقة.
        db: جلسة قاعدة البيانات المستخدمة للاستعلام.

    Returns:
        User: كائن المستخدم الفعّال.

    Raises:
        HTTPException: إذا كان المستخدم غير موجود أو غير مفعّل.
    """

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive")

    # فصل الكائن عن الجلسة لضمان توفر بياناته أثناء البث الطويل دون الاصطدام بإغلاق الجلسة.
    await db.refresh(user)
    db.expunge(user)

    return user

def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminChatBoundaryService:
    """تبعية للحصول على خدمة حدود محادثة المسؤول."""
    return AdminChatBoundaryService(db)

def get_chat_dispatcher(db: AsyncSession = Depends(get_db)) -> ChatRoleDispatcher:
    """تبعية للحصول على موزّع الدردشة حسب الدور."""
    return build_chat_dispatcher(db)

@router.post("/api/chat/stream", summary="بث محادثة المسؤول (Admin Chat Stream)")
async def chat_stream(
    chat_request: ChatRequest,
    ai_client: AIClient = Depends(get_ai_client),
    actor: User = Depends(get_actor_user),
    dispatcher: ChatRoleDispatcher = Depends(get_chat_dispatcher),
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
    # تنسيق تدفق المحادثة بالكامل عبر خدمة الحدود
    dispatch_request = ChatDispatchRequest(
        question=chat_request.question,
        conversation_id=chat_request.conversation_id,
        ai_client=ai_client,
        session_factory=session_factory,
    )
    dispatch_result = await ChatOrchestrator.dispatch(
        user=actor,
        request=dispatch_request,
        dispatcher=dispatcher,
    )

    return StreamingResponse(
        dispatch_result.stream,
        media_type="text/event-stream",
        status_code=dispatch_result.status_code,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Encoding": "identity",  # منع الضغط (GZip) لضمان الوصول الفوري
            "X-Accel-Buffering": "no",  # تعطيل التخزين المؤقت في Nginx
        },
    )

@router.get(
    "/api/chat/latest",
    summary="استرجاع آخر محادثة (Get Latest Conversation)",
    response_model=ConversationDetailsResponse | None,
)
async def get_latest_chat(
    actor: User = Depends(get_actor_user),
    service: AdminChatBoundaryService = Depends(get_admin_service),
) -> ConversationDetailsResponse | None:
    """
    استرجاع تفاصيل آخر محادثة للمستخدم الحالي.
    مفيد لاستعادة الحالة عند إعادة تحميل الصفحة.
    """
    conversation_data = await service.get_latest_conversation_details(actor)
    if not conversation_data:
        return None
    return ConversationDetailsResponse.model_validate(conversation_data)

@router.get(
    "/api/conversations",
    summary="سرد المحادثات (List Conversations)",
    response_model=list[ConversationSummaryResponse],
)
async def list_conversations(
    actor: User = Depends(get_actor_user),
    service: AdminChatBoundaryService = Depends(get_admin_service),
) -> list[ConversationSummaryResponse]:
    """
    استرجاع قائمة بجميع محادثات المستخدم.

    الخدمة تعيد البيانات متوافقة مع Schema مباشرة.
    """
    results = await service.list_user_conversations(actor)
    return [ConversationSummaryResponse.model_validate(r) for r in results]

@router.get(
    "/api/conversations/{conversation_id}",
    summary="تفاصيل المحادثة (Conversation Details)",
    response_model=ConversationDetailsResponse,
)
async def get_conversation(
    conversation_id: int,
    actor: User = Depends(get_actor_user),
    service: AdminChatBoundaryService = Depends(get_admin_service),
) -> ConversationDetailsResponse:
    """
    استرجاع الرسائل والتفاصيل لمحادثة محددة.
    """
    data = await service.get_conversation_details(actor, conversation_id)
    return ConversationDetailsResponse.model_validate(data)
