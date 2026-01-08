"""
إعدادات وكيل التخطيط (Planning Agent).

تضمن هذه الإعدادات عمل الوكيل بشكل مستقل وقابل للتكوين.
"""

import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlanningAgentSettings(BaseSettings):
    """
    إعدادات وكيل التخطيط.

    تستخدم لتحديد معلمات التشغيل والاتصال بقاعدة البيانات.
    """

    SERVICE_NAME: str = Field("planning-agent", description="اسم الوكيل")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الوكيل")
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./planning_agent.db",
        description="رابط قاعدة البيانات الخاصة بالوكيل",
    )

    model_config = SettingsConfigDict(env_prefix="PLANNING_")


@functools.lru_cache(maxsize=1)
def get_settings() -> PlanningAgentSettings:
    """يبني إعدادات الوكيل مع تخزينها للاستخدام المتكرر."""

    return PlanningAgentSettings()
