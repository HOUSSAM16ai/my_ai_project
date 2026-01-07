"""
واجهة برمجة تطبيقات محادثة العملاء القياسيين.

توفر نقاط النهاية الخاصة بالمستخدمين القياسيين للوصول إلى محادثة تعليمية
مع فرض سياسات الأمان والملكية.
"""
from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.customer_chat import (
    CustomerChatRequest,
    CustomerConversationDetails,
    CustomerConversationSummary,
)
from app.core.ai_gateway import AIClient, get_ai_client
from app.core.domain.models import User
from app.core.database import async_session_factory, get_db
from app.core.di import get_logger
from app.deps.auth import CurrentUser, require_permissions
from app.services.boundaries.customer_chat_boundary_service import CustomerChatBoundaryService
from app.services.chat.contracts import ChatDispatchRequest
from app.services.chat.dispatcher import ChatRoleDispatcher, build_chat_dispatcher
from app.services.chat.orchestrator import ChatOrchestrator
from app.services.rbac import QA_SUBMIT

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/chat",
    tags=["Customer Chat"],
)


def get_session_factory() -> Callable[[], AsyncSession]:
    """تبعية لاسترجاع مصنع الجلسات."""
    return async_session_factory


def get_chat_actor(
    current: CurrentUser = Depends(require_permissions(QA_SUBMIT)),
) -> CurrentUser:
    """تبعية تضمن امتلاك صلاحية الأسئلة التعليمية."""
    return current


def get_current_user_id(current: CurrentUser = Depends(get_chat_actor)) -> int:
    """إرجاع معرف المستخدم الحالي بعد تحقق الصلاحيات."""
    return current.user.id


async def get_actor_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    جلب كائن المستخدم الفعلي بعد التحقق من الحالة.
    """
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive")
    await db.refresh(user)
    db.expunge(user)
    return user


def get_customer_service(db: AsyncSession = Depends(get_db)) -> CustomerChatBoundaryService:
    """تبعية للحصول على خدمة حدود محادثة العملاء."""
    return CustomerChatBoundaryService(db)

def get_chat_dispatcher(db: AsyncSession = Depends(get_db)) -> ChatRoleDispatcher:
    """تبعية للحصول على موزّع الدردشة حسب الدور."""
    return build_chat_dispatcher(db)


@router.post("/stream", summary="بث محادثة تعليمية")
async def chat_stream(
    request: Request,
    chat_request: CustomerChatRequest,
    ai_client: AIClient = Depends(get_ai_client),
    actor: User = Depends(get_actor_user),
    dispatcher: ChatRoleDispatcher = Depends(get_chat_dispatcher),
    session_factory: Callable[[], AsyncSession] = Depends(get_session_factory),
) -> StreamingResponse:
    """
    بث محادثة العميل القياسي مع الذكاء الاصطناعي.
    """
    if actor.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin accounts must use the admin chat endpoint.",
        )
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    dispatch_request = ChatDispatchRequest(
        question=chat_request.question,
        conversation_id=chat_request.conversation_id,
        ai_client=ai_client,
        session_factory=session_factory,
        ip=client_ip,
        user_agent=user_agent,
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
            "Content-Encoding": "identity",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/latest",
    summary="استرجاع آخر محادثة",
    response_model=CustomerConversationDetails | None,
)
async def get_latest_chat(
    actor: User = Depends(get_actor_user),
    service: CustomerChatBoundaryService = Depends(get_customer_service),
) -> CustomerConversationDetails | None:
    conversation_data = await service.get_latest_conversation_details(actor)
    if not conversation_data:
        return None
    return CustomerConversationDetails.model_validate(conversation_data)


@router.get(
    "/conversations",
    summary="سرد المحادثات",
    response_model=list[CustomerConversationSummary],
)
async def list_conversations(
    actor: User = Depends(get_actor_user),
    service: CustomerChatBoundaryService = Depends(get_customer_service),
) -> list[CustomerConversationSummary]:
    results = await service.list_user_conversations(actor)
    return [CustomerConversationSummary.model_validate(r) for r in results]


@router.get(
    "/conversations/{conversation_id}",
    summary="تفاصيل محادثة",
    response_model=CustomerConversationDetails,
)
async def get_conversation(
    conversation_id: int,
    actor: User = Depends(get_actor_user),
    service: CustomerChatBoundaryService = Depends(get_customer_service),
) -> CustomerConversationDetails:
    data = await service.get_conversation_details(actor, conversation_id)
    return CustomerConversationDetails.model_validate(data)
