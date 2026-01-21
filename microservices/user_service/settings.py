"""
إعدادات خدمة المستخدمين.

تعزل هذه الإعدادات الخدمة عن أي اعتماد مشترك مع بقية الخدمات.
"""

import functools
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UserServiceSettings(BaseSettings):
    """
    إعدادات خدمة المستخدمين بصورة مستقلة وبسيطة.
    """

    SERVICE_NAME: str = Field("user-service", description="اسم الخدمة")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الخدمة")

    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = Field(
        "development", description="بيئة التشغيل"
    )
    DEBUG: bool = Field(False, description="تفعيل وضع التصحيح")
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="مستوى السجلات"
    )

    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./user_service.db",
        description="رابط قاعدة بيانات خدمة المستخدمين",
    )

    model_config = SettingsConfigDict(env_prefix="USER_", env_file=".env", extra="ignore")


@functools.lru_cache(maxsize=1)
def get_settings() -> UserServiceSettings:
    """يبني إعدادات الخدمة مع التخزين المؤقت."""
    return UserServiceSettings()
