"""
واجهة برمجة تطبيقات المهام (Missions API).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.domain.mission import Mission, MissionStatus, MissionEvent
from app.core.domain.user import User
from app.core.logging import get_logger
from app.security.auth_dependency import get_current_active_user, get_current_admin

logger = get_logger("missions-api")

router = APIRouter(
    prefix="/api/missions",
    tags=["Educational Missions"],
)


@router.get("", summary="قائمة مهام المستخدم")
async def list_missions(
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    skip: int = 0,
    status: MissionStatus | None = None,
):
    """
    استرجاع قائمة المهام الخاصة بالمستخدم الحالي.
    للمسؤولين: يمكن رؤية كل المهام (لاحقاً يمكن إضافة فلتر).
    """
    query = select(Mission).order_by(desc(Mission.created_at)).offset(skip).limit(limit)

    if not user.is_admin:
        query = query.where(Mission.initiator_id == user.id)

    if status:
        query = query.where(Mission.status == status)

    result = await db.execute(query)
    missions = result.scalars().all()

    return [
        {
            "id": m.id,
            "title": m.objective[:50] + ("..." if len(m.objective) > 50 else ""),
            "full_objective": m.objective,
            "status": m.status,
            "created_at": m.created_at,
            "updated_at": m.updated_at
        }
        for m in missions
    ]


@router.get("/{mission_id}", summary="تفاصيل المهمة")
async def get_mission_details(
    mission_id: int,
    user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    عرض تفاصيل المهمة وسجل أحداثها.
    """
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="المهمة غير موجودة")

    # التحقق من الصلاحية
    if not user.is_admin and mission.initiator_id != user.id:
        raise HTTPException(status_code=403, detail="ليس لديك صلاحية لعرض هذه المهمة")

    # جلب الأحداث
    events_query = (
        select(MissionEvent)
        .where(MissionEvent.mission_id == mission_id)
        .order_by(MissionEvent.created_at)
    )
    events_res = await db.execute(events_query)
    events = events_res.scalars().all()

    return {
        "mission": {
            "id": mission.id,
            "objective": mission.objective,
            "status": mission.status,
            "created_at": mission.created_at,
            "updated_at": mission.updated_at,
        },
        "timeline": [
            {
                "type": e.event_type,
                "data": e.payload_json,
                "timestamp": e.created_at
            }
            for e in events
        ]
    }
