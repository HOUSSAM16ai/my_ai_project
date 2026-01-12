"""
User Service Configuration.

Inherits from canonical BaseServiceSettings.
"""

import functools

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from app.core.settings.base import BaseServiceSettings


class UserServiceSettings(BaseServiceSettings):
    """
    Configuration for User Service.
    Isolated database.
    """

    SERVICE_NAME: str = "user-service"
    SERVICE_VERSION: str = "1.0.0"

    # Default to a local SQLite DB for dev/testing if not provided
    DATABASE_URL: str | None = Field(
        default="sqlite+aiosqlite:///./user_service.db", description="User Service Database URL"
    )

    model_config = SettingsConfigDict(env_prefix="USER_", env_file=".env", extra="ignore")


@functools.lru_cache(maxsize=1)
def get_settings() -> UserServiceSettings:
    return UserServiceSettings()
