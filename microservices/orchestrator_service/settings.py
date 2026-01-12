"""
إعدادات خدمة التنسيق (Orchestrator).

تمثل هذه الإعدادات مصدر الحقيقة الوحيد للخدمة، مع فصل
مسؤوليات الاتصال بالخدمات الأخرى عن منطق التنفيذ.
"""

import functools

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.settings.base import BaseServiceSettings


class OrchestratorSettings(BaseServiceSettings):
    """
    إعدادات خدمة التنسيق.

    ترث من BaseServiceSettings لتوحيد البنية التحتية،
    وتضيف إعدادات التواصل مع الوكلاء الآخرين.
    """

    # Overrides (Defaults)
    SERVICE_NAME: str = Field("orchestrator-service", description="اسم الخدمة")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الخدمة")
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./orchestrator.db",
        description="رابط قاعدة البيانات الخاصة بالخدمة",
    )

    # Service Specific
    PLANNING_AGENT_URL: str = Field(
        "http://planning-agent:8001",
        description="عنوان خدمة التخطيط",
    )
    MEMORY_AGENT_URL: str = Field(
        "http://memory-agent:8002",
        description="عنوان خدمة الذاكرة",
    )
    USER_SERVICE_URL: str = Field(
        "http://user-service:8003",
        description="عنوان خدمة المستخدمين",
    )

    model_config = SettingsConfigDict(env_prefix="ORCHESTRATOR_", env_file=".env", extra="ignore")


@functools.lru_cache(maxsize=1)
def get_settings() -> OrchestratorSettings:
    """يبني إعدادات الخدمة مع تخزينها لعمليات الطلب المتعددة."""
    return OrchestratorSettings()
