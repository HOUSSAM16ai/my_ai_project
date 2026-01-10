"""نماذج واستجابات جاهزية خدمة التنسيق."""

from __future__ import annotations

from pydantic import BaseModel

from microservices.orchestrator_service.settings import OrchestratorSettings


class HealthResponse(BaseModel):
    """استجابة صحة قياسية لخدمة التنسيق."""

    service: str
    status: str
    database: str | None = None


def build_health_payload(settings: OrchestratorSettings) -> HealthResponse:
    """يبني استجابة الصحة اعتمادًا على إعدادات الخدمة."""

    return HealthResponse(
        service=settings.SERVICE_NAME,
        status="ok",
        database=settings.DATABASE_URL,
    )
