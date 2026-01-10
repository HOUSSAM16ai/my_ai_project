"""نماذج واستجابات جاهزية خدمة المراقبة."""

from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """استجابة صحة قياسية لخدمة المراقبة."""

    service: str
    status: str
    database: str | None = None


def build_health_payload(service_name: str, database: str | None = None) -> HealthResponse:
    """يبني استجابة الصحة لخدمة المراقبة."""

    return HealthResponse(service=service_name, status="ok", database=database)
