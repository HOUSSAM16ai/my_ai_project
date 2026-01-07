"""
إعدادات وكيل التخطيط (Planning Agent).

تعكس هذه الإعدادات استقلالية الوكيل وارتباطه بقاعدة بياناته الخاصة.
"""

import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlanningAgentSettings(BaseSettings):
    """
    إعدادات وكيل التخطيط.

    يتم استخدام رابط قاعدة البيانات الخاصة بالوكيل لضمان
    العزل الكامل عن بقية الخدمات.
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
    """يبني إعدادات الوكيل مع تخزينها داخلياً."""

    return PlanningAgentSettings()
