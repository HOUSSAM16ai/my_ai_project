"""نماذج واستجابات جاهزية خدمة المستخدمين."""

from __future__ import annotations

from pydantic import BaseModel

from microservices.user_service.settings import UserServiceSettings


class HealthResponse(BaseModel):
    """استجابة صحة قياسية لخدمة المستخدمين."""

    service: str
    status: str
    environment: str | None = None


def build_health_payload(settings: UserServiceSettings) -> HealthResponse:
    """يبني استجابة الصحة اعتمادًا على إعدادات الخدمة."""

    return HealthResponse(
        service=settings.SERVICE_NAME,
        status="ok",
        environment=settings.ENVIRONMENT,
    )
