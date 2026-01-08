"""
سجل خطط الوكلاء (Agent Plan Registry).
---------------------------------------
يوفر هذا الملف مستودعاً قابلاً للتوسع لتخزين خطط الوكلاء
واسترجاعها عبر معرفات واضحة. يعتمد على نمط "مستودع البيانات"
مع دعم التخزين المركزي لتسهيل التوسع الأفقي.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.models import AgentPlanSnapshot
from app.core.database import async_session_factory
from app.services.overmind.domain.api_schemas import AgentPlanData


@dataclass(frozen=True)
class AgentPlanRecord:
    """
    تمثيل داخلي لخطة الوكلاء.

    يحتوي على البيانات الأساسية اللازمة لعرض الخطة للعملاء.
    """

    data: AgentPlanData


class PlanRegistry(Protocol):
    """
    واجهة سجل خطط الوكلاء لضمان فصل التخزين عن الاستخدام.
    """

    async def store(self, plan: AgentPlanRecord) -> None:
        """حفظ خطة جديدة في المستودع."""

    async def get(self, plan_id: str) -> AgentPlanRecord | None:
        """استرجاع خطة محفوظة عبر معرفها."""


class InMemoryPlanRegistry:
    """
    مستودع خطط الوكلاء في الذاكرة (للاستخدام المحلي أو الاختبار).

    يُستخدم لتسجيل الخطط المؤقتة واسترجاعها بسرعة عبر معرف الخطة.
    """

    def __init__(self) -> None:
        self._plans: dict[str, AgentPlanRecord] = {}

    async def store(self, plan: AgentPlanRecord) -> None:
        """
        حفظ خطة جديدة داخل السجل.

        Args:
            plan: الخطة المراد تخزينها.
        """
        self._plans[plan.data.plan_id] = plan

    async def get(self, plan_id: str) -> AgentPlanRecord | None:
        """
        استرجاع خطة من السجل.

        Args:
            plan_id: معرف الخطة.

        Returns:
            AgentPlanRecord | None: الخطة إذا وجدت أو None إذا لم توجد.
        """
        return self._plans.get(plan_id)


class DatabasePlanRegistry:
    """
    مستودع خطط الوكلاء المدعوم بقاعدة البيانات لتسهيل التوسع الأفقي.
    """

    def __init__(self, session_factory: Callable[[], AsyncSession] = async_session_factory) -> None:
        self._session_factory = session_factory

    async def store(self, plan: AgentPlanRecord) -> None:
        """
        حفظ خطة جديدة داخل قاعدة البيانات.
        """
        payload = plan.data.model_dump()
        async with self._session_factory() as session:
            await self._upsert_plan(session, plan.data.plan_id, payload)

    async def get(self, plan_id: str) -> AgentPlanRecord | None:
        """
        استرجاع خطة مخزنة من قاعدة البيانات.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentPlanSnapshot).where(AgentPlanSnapshot.plan_id == plan_id)
            )
            snapshot = result.scalar_one_or_none()
            if snapshot is None or snapshot.payload_json is None:
                return None

            plan_data = AgentPlanData.model_validate(snapshot.payload_json)
            return AgentPlanRecord(data=plan_data)

    async def _upsert_plan(
        self,
        session: AsyncSession,
        plan_id: str,
        payload: dict[str, object],
    ) -> None:
        result = await session.execute(
            select(AgentPlanSnapshot).where(AgentPlanSnapshot.plan_id == plan_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.payload_json = payload
        else:
            session.add(AgentPlanSnapshot(plan_id=plan_id, payload_json=payload))
        await session.commit()
