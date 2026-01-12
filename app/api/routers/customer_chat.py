"""
واجهة برمجة تطبيقات محادثة العملاء القياسيين.

توفر نقاط النهاية الخاصة بالمستخدمين القياسيين للوصول إلى محادثة تعليمية
مع فرض سياسات الأمان والملكية.
"""

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.customer_chat import CustomerConversationDetails, CustomerConversationSummary
from app.core.ai_gateway import AIClient, get_ai_client
from app.core.config import get_settings
from app.core.database import async_session_factory, get_db
from app.core.di import get_logger
from app.core.domain.user import User
from app.deps.auth import CurrentUser, require_permissions
from app.services.boundaries.customer_chat_boundary_service import CustomerChatBoundaryService
from app.services.chat.contracts import ChatDispatchRequest
from app.services.chat.dispatcher import ChatRoleDispatcher, build_chat_dispatcher
from app.services.chat.orchestrator import ChatOrchestrator
from app.services.rbac import QA_SUBMIT
from app.services.auth.token_decoder import decode_user_id

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


@router.websocket("/ws")
async def chat_stream_ws(
    websocket: WebSocket,
    ai_client: AIClient = Depends(get_ai_client),
    dispatcher: ChatRoleDispatcher = Depends(get_chat_dispatcher),
    session_factory: Callable[[], AsyncSession] = Depends(get_session_factory),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    قناة WebSocket لبث محادثة تعليمية للمستخدم القياسي.
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        user_id = decode_user_id(token, get_settings().SECRET_KEY)
    except HTTPException:
        await websocket.close(code=4401)
        return

    actor = await db.get(User, user_id)
    if actor is None or not actor.is_active:
        await websocket.close(code=4401)
        return

    await websocket.accept()

    if actor.is_admin:
        await websocket.send_json(
            {
                "type": "error",
                "payload": {
                    "details": "Admin accounts must use the admin chat endpoint.",
                    "status_code": 403,
                },
            }
        )
        await websocket.close(code=4403)
        return

    try:
        while True:
            payload = await websocket.receive_json()
            question = str(payload.get("question", "")).strip()
            if not question:
                await websocket.send_json(
                    {"type": "error", "payload": {"details": "Question is required."}}
                )
                continue

            client_ip = websocket.client.host if websocket.client else None
            user_agent = websocket.headers.get("user-agent")

            dispatch_request = ChatDispatchRequest(
                question=question,
                conversation_id=payload.get("conversation_id"),
                ai_client=ai_client,
                session_factory=session_factory,
                ip=client_ip,
                user_agent=user_agent,
            )

            try:
                dispatch_result = await ChatOrchestrator.dispatch(
                    user=actor,
                    request=dispatch_request,
                    dispatcher=dispatcher,
                )
            except HTTPException as exc:
                await websocket.send_json(
                    {
                        "type": "error",
                        "payload": {"details": exc.detail, "status_code": exc.status_code},
                    }
                )
                continue

            await websocket.send_json(
                {"type": "status", "payload": {"status_code": dispatch_result.status_code}}
            )

            async for event in dispatch_result.stream:
                await websocket.send_json(event)

    except WebSocketDisconnect:
        logger.info("Customer WebSocket disconnected")


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
