"""نماذج واستجابات جاهزية وكيل الذاكرة."""

from __future__ import annotations

from pydantic import BaseModel

from microservices.memory_agent.settings import MemoryAgentSettings


class HealthResponse(BaseModel):
    """استجابة صحة قياسية لوكيل الذاكرة."""

    service: str
    status: str
    database: str | None = None


def build_health_payload(settings: MemoryAgentSettings) -> HealthResponse:
    """يبني استجابة الصحة اعتمادًا على إعدادات الوكيل."""

    return HealthResponse(
        service=settings.SERVICE_NAME,
        status="ok",
        database=settings.DATABASE_URL,
    )
