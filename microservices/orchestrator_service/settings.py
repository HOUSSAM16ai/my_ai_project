"""
إعدادات خدمة التنسيق (Orchestrator).

تمثل هذه الإعدادات مصدر الحقيقة الوحيد للخدمة، مع فصل
مسؤوليات الاتصال بالخدمات الأخرى عن منطق التنفيذ.
"""

import functools
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OrchestratorSettings(BaseSettings):
    """
    إعدادات خدمة التنسيق بصورة مستقلة وبسيطة.
    """

    SERVICE_NAME: str = Field("orchestrator-service", description="اسم الخدمة")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الخدمة")

    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = Field(
        "development", description="بيئة التشغيل"
    )
    DEBUG: bool = Field(False, description="تفعيل وضع التصحيح")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="مستوى السجلات"
    )

    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./orchestrator.db",
        description="رابط قاعدة البيانات الخاصة بالخدمة",
    )

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
