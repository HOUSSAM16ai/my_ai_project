"""نماذج واستجابات جاهزية خدمة التخطيط."""

from __future__ import annotations

from pydantic import BaseModel

from microservices.planning_agent.settings import PlanningAgentSettings


class HealthResponse(BaseModel):
    """استجابة صحة قياسية لخدمة التخطيط."""

    service: str
    status: str
    database: str | None = None


def build_health_payload(settings: PlanningAgentSettings) -> HealthResponse:
    """يبني استجابة الصحة اعتمادًا على إعدادات الخدمة."""

    return HealthResponse(
        service=settings.SERVICE_NAME,
        status="ok",
        database=settings.DATABASE_URL,
    )
