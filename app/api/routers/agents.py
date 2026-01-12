# app/api/routers/agents.py
"""
واجهة وكلاء التخطيط (Agents Planning Router).
---------------------------------------------
توفر هذه الوحدة نقاط النهاية الخاصة بتوليد خطط الوكلاء
ومشاركتها مع العملاء عبر عقد API واضح.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.di import get_logger
from app.deps.auth import CurrentUser, get_current_user
from app.services.overmind.domain.api_schemas import AgentsPlanRequest, AgentsPlanResponse
from app.services.overmind.plan_registry import AgentPlanRegistry
from app.services.overmind.plan_service import AgentPlanService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/agents",
    tags=["Agents"],
)


def get_plan_registry(request: Request) -> AgentPlanRegistry:
    """
    الحصول على سجل الخطط من حالة التطبيق.
    """
    registry = getattr(request.app.state, "agent_plan_registry", None)
    if registry is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent plan registry is not initialized",
        )
    return registry


def get_plan_service(request: Request) -> AgentPlanService:
    """
    الحصول على خدمة التخطيط من حالة التطبيق.
    """
    service = getattr(request.app.state, "agent_plan_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent plan service is not initialized",
        )
    return service


@router.post(
    "/plan",
    response_model=AgentsPlanResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid plan request"},
        401: {"description": "Unauthorized"},
        500: {"description": "Agent plan service is not initialized"},
    },
)
async def create_agent_plan(
    payload: AgentsPlanRequest,
    current: CurrentUser = Depends(get_current_user),
    registry: AgentPlanRegistry = Depends(get_plan_registry),
    plan_service: AgentPlanService = Depends(get_plan_service),
) -> AgentsPlanResponse:
    """
    إنشاء خطة جديدة من مجلس الوكلاء.
    """
    plan_record = await plan_service.create_plan(payload)
    registry.store(plan_record)
    logger.info(
        "Agent plan stored", extra={"user_id": current.user.id, "plan_id": plan_record.data.plan_id}
    )
    return AgentsPlanResponse(status="success", data=plan_record.data)


@router.get(
    "/plan/{plan_id}",
    response_model=AgentsPlanResponse,
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Plan not found"},
        500: {"description": "Agent plan registry is not initialized"},
    },
)
async def get_agent_plan(
    plan_id: str,
    current: CurrentUser = Depends(get_current_user),
    registry: AgentPlanRegistry = Depends(get_plan_registry),
) -> AgentsPlanResponse:
    """
    استرجاع خطة محفوظة عبر معرفها.
    """
    plan_record = registry.get(plan_id)
    if plan_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    logger.info(
        "Agent plan retrieved",
        extra={"user_id": current.user.id, "plan_id": plan_record.data.plan_id},
    )
    return AgentsPlanResponse(status="success", data=plan_record.data)
