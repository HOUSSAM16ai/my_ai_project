"""
إعدادات خدمة المستخدمين.

تعزل هذه الإعدادات الخدمة عن أي اعتماد مشترك مع بقية الخدمات.
"""

import functools

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.settings.base import BaseServiceSettings


class UserServiceSettings(BaseServiceSettings):
    """إعدادات خدمة المستخدمين مع وراثة قواعد الإعدادات العامة."""

    SERVICE_NAME: str = Field("user-service", description="اسم الخدمة")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الخدمة")
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./user_service.db",
        description="رابط قاعدة بيانات خدمة المستخدمين",
    )

    model_config = SettingsConfigDict(
        env_prefix="USER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@functools.lru_cache(maxsize=1)
def get_settings() -> UserServiceSettings:
    """يبني إعدادات الخدمة مع التخزين المؤقت."""
    return UserServiceSettings()
