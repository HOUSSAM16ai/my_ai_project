"""
إعدادات وكيل التخطيط (Planning Agent).

تضمن هذه الإعدادات عمل الوكيل بشكل مستقل وقابل للتكوين.
"""

import functools

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.settings.base import BaseServiceSettings


class PlanningAgentSettings(BaseServiceSettings):
    """
    إعدادات وكيل التخطيط.

    ترث من BaseServiceSettings لضمان التوافق مع المعايير الموحدة.
    """

    # Overrides (Defaults)
    SERVICE_NAME: str = Field("planning-agent", description="اسم الوكيل")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الوكيل")
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./planning_agent.db",
        description="رابط قاعدة البيانات الخاصة بالوكيل",
    )

    model_config = SettingsConfigDict(
        env_prefix="PLANNING_",
        env_file=".env",
        extra="ignore"
    )


@functools.lru_cache(maxsize=1)
def get_settings() -> PlanningAgentSettings:
    """يبني إعدادات الوكيل مع تخزينها للاستخدام المتكرر."""
    return PlanningAgentSettings()
