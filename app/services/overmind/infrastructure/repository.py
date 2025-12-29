"""
مستودع بيانات العقل المدبر (Overmind Repository).
--------------------------------------------------
مسؤول عن جميع عمليات التخاطب مع قاعدة البيانات (SQLAlchemy queries).
يفصل منطق الوصول للبيانات عن منطق الأعمال.

المبادئ:
- Separation of Concerns: استعلامات SQL فقط هنا.
- Eager Loading: تحميل العلاقات بشكل صريح لتجنب MissingGreenlet.
- Atomic Operations: استخدام الـ Session الحالية بدقة.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import (
    Mission,
    MissionEvent,
    MissionEventType,
    MissionPlan,
    MissionStatus,
    PlanStatus,
    Task,
    TaskStatus,
)


class MissionRepository:
    """
    مستودع للتعامل مع كيانات Mission و Task و Related Models.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_mission(self, objective: str, initiator_id: int) -> Mission:
        """إنشاء مهمة جديدة."""
        mission = Mission(
            objective=objective,
            initiator_id=initiator_id,
            status=MissionStatus.PENDING,
        )
        self.session.add(mission)
        await self.session.flush()
        # نترك الـ commit للخدمة (Service) أو نستخدم flush فقط إذا كنا ضمن معاملة أكبر
        return mission

    async def get_mission_by_id(self, mission_id: int) -> Mission | None:
        """
        استرجاع مهمة بالمعرف مع تحميل كافة العلاقات المطلوبة.
        """
        stmt = (
            select(Mission)
            .options(
                # استخدام selectinload للعلاقات One-to-Many لتجنب مشاكل الأداء في joinedload
                selectinload(Mission.tasks),
                selectinload(Mission.mission_plans),
                selectinload(Mission.events),
            )
            .where(Mission.id == mission_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_mission_status(self, mission_id: int, status: MissionStatus) -> Mission | None:
        """تحديث حالة المهمة."""
        stmt = select(Mission).where(Mission.id == mission_id)
        result = await self.session.execute(stmt)
        mission = result.scalar_one_or_none()
        if mission:
            mission.status = status
            self.session.add(mission)
            # flush لتحديث الحالة في الذاكرة/SQL
            await self.session.flush()
        return mission

    async def create_event(
        self, mission_id: int, event_type: MissionEventType, payload: dict[str, Any]
    ) -> MissionEvent:
        """تسجيل حدث جديد."""
        event = MissionEvent(
            mission_id=mission_id,
            event_type=event_type,
            payload_json=payload,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_latest_plan_version(self, mission_id: int) -> int:
        """الحصول على رقم آخر إصدار للخطة."""
        stmt = select(func.max(MissionPlan.version)).where(MissionPlan.mission_id == mission_id)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def create_mission_plan(self, plan: MissionPlan) -> MissionPlan:
        """حفظ خطة مهمة جديدة."""
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def set_active_plan(self, mission_id: int, plan_id: int) -> None:
        """تعيين الخطة النشطة للمهمة."""
        stmt = select(Mission).where(Mission.id == mission_id)
        result = await self.session.execute(stmt)
        mission = result.scalar_one()
        mission.active_plan_id = plan_id
        self.session.add(mission)
        await self.session.flush()

    async def create_task(self, task: Task) -> Task:
        """إنشاء مهمة فرعية (Task)."""
        self.session.add(task)
        await self.session.flush()
        return task

    async def get_task_by_id(self, task_id: int) -> Task | None:
        """استرجاع مهمة فرعية."""
        stmt = select(Task).where(Task.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tasks_for_mission(self, mission_id: int) -> list[Task]:
        """استرجاع جميع المهام لمهمة رئيسية."""
        stmt = select(Task).where(Task.mission_id == mission_id).order_by(Task.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_mission_events(self, mission_id: int) -> list[MissionEvent]:
        """استرجاع أحداث المهمة."""
        stmt = (
            select(MissionEvent)
            .where(MissionEvent.mission_id == mission_id)
            .order_by(MissionEvent.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
