"""
إعدادات خدمة المستخدمين (User Service).

تهدف هذه الإعدادات إلى عزل بيانات المستخدمين في خدمة مستقلة.
"""

import functools

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UserServiceSettings(BaseSettings):
    """
    إعدادات خدمة المستخدمين.

    يتم تحديد قاعدة بيانات مستقلة لضمان العزل بين الخدمات.
    """

    SERVICE_NAME: str = Field("user-service", description="اسم الخدمة")
    SERVICE_VERSION: str = Field("1.0.0", description="إصدار الخدمة")
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./user_service.db",
        description="رابط قاعدة البيانات الخاصة بالخدمة",
    )

    model_config = SettingsConfigDict(env_prefix="USER_")


@functools.lru_cache(maxsize=1)
def get_settings() -> UserServiceSettings:
    """يبني إعدادات الخدمة مع تخزينها للاستخدام المتكرر."""

    return UserServiceSettings()
