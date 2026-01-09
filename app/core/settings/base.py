import logging
import os
import secrets
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """
    Base settings class for all microservices.
    Provides common configuration for environment, logging, and database.
    """

    # Service Identity
    SERVICE_NAME: str = Field(..., description="Name of the service")
    SERVICE_VERSION: str = Field("0.1.0", description="Service version")

    # Environment Control
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = Field(
        "development", description="Operational environment"
    )
    DEBUG: bool = Field(False, description="Debug mode")

    # Database
    DATABASE_URL: str = Field(..., description="Database connection URL")

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="Logging level"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def ensure_async_db_url(cls, v: str | None) -> str:
        """Ensures the database URL is async compatible."""
        if not v:
            # In testing/dev, we might fallback, but explicit is better.
            # Allowing None for now if subclass handles it, but typically required.
            return v

        if v.startswith("sqlite://"):
             return v.replace("sqlite://", "sqlite+aiosqlite://")

        if v.startswith("postgresql://") and "asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://")

        return v
