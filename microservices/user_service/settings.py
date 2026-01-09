"""
إعدادات خدمة المستخدمين (User Service).

تهدف هذه الإعدادات إلى عزل بيانات المستخدمين في خدمة مستقلة.
"""

import functools

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.settings.base import BaseServiceSettings


class UserServiceSettings(BaseServiceSettings):
    """
    إعدادات خدمة المستخدمين.

    يتم تحديد قاعدة بيانات مستقلة لضمان العزل بين الخدمات.
    """
    SERVICE_NAME: str = Field("user-service", description="اسم الخدمة")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الخدمة")

    # We override this to provide a default for dev, but in PROD it should be env var.
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./user_service.db",
        description="رابط قاعدة البيانات الخاصة بالخدمة",
    )

    # Re-declare env_file to ensure it's not lost when overriding env_prefix
    model_config = SettingsConfigDict(
        env_prefix="USER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@functools.lru_cache(maxsize=1)
def get_settings() -> UserServiceSettings:
    """يبني إعدادات الخدمة مع تخزينها للاستخدام المتكرر."""

    return UserServiceSettings()
