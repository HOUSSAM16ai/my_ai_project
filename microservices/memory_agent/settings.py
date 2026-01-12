"""
إعدادات وكيل الذاكرة (Memory Agent).

تضمن هذه الإعدادات استقلالية التخزين وعدم مشاركة قاعدة بيانات مركزية.
"""

import functools

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.settings.base import BaseServiceSettings


class MemoryAgentSettings(BaseServiceSettings):
    """
    إعدادات وكيل الذاكرة.

    ترث من BaseServiceSettings لضمان التوافق مع المعايير الموحدة.
    """

    # Overrides (Defaults)
    SERVICE_NAME: str = Field("memory-agent", description="اسم الوكيل")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الوكيل")
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./memory_agent.db",
        description="رابط قاعدة البيانات الخاصة بالوكيل",
    )

    model_config = SettingsConfigDict(env_prefix="MEMORY_", env_file=".env", extra="ignore")


@functools.lru_cache(maxsize=1)
def get_settings() -> MemoryAgentSettings:
    """يبني إعدادات الوكيل مع تخزينها للاستخدام المتكرر."""
    return MemoryAgentSettings()
