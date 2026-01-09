"""
Unified Configuration System for CogniForge.

This module provides the canonical `AppSettings` and `get_settings()`
implementation, strictly following the Phase 2 refactoring plan.

Standards:
- Single Source of Truth: All services use this settings schema.
- Strict Types: No Any, use Pydantic V2.
- Environment Awareness: Automatic detection and validation.
- Secure Defaults: Safe by design.
"""

import functools
import json
import logging
import os
import secrets
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pydantic import Field, ValidationInfo, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Logging Setup
logger = logging.getLogger("app.core.settings")

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

_DEV_SECRET_KEY_CACHE: str | None = None

def _get_or_create_dev_secret_key() -> str:
    """Generates a stable development secret key to avoid session invalidation on restart."""
    global _DEV_SECRET_KEY_CACHE
    if _DEV_SECRET_KEY_CACHE is None:
        _DEV_SECRET_KEY_CACHE = secrets.token_urlsafe(64)
    return _DEV_SECRET_KEY_CACHE

def _ensure_database_url(value: str | None, environment: str) -> str:
    """Ensures a valid database URL exists, falling back to SQLite in Dev/Test."""
    if value:
        return value

    if environment == "production":
        raise ValueError("❌ CRITICAL: DATABASE_URL is missing in PRODUCTION!")

    if environment == "testing":
        return "sqlite+aiosqlite:///:memory:"

    logger.warning("⚠️ No DATABASE_URL found! Activating Fallback (SQLite).")
    return "sqlite+aiosqlite:///./dev.db"

def _upgrade_postgres_protocol(url: str) -> str:
    """Upgrades synchronous Postgres URLs to asyncpg."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

def _normalize_csv_or_list(value: list[str] | str | None) -> list[str]:
    """Normalizes comma-separated strings or JSON lists into a strict list[str]."""
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return []

        # Try JSON first
        if candidate.startswith("[") and candidate.endswith("]"):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass

        # Fallback to CSV
        return [item.strip() for item in candidate.split(",") if item.strip()]

    return []

# -----------------------------------------------------------------------------
# Base Settings (Shared across all services)
# -----------------------------------------------------------------------------

class BaseServiceSettings(BaseSettings):
    """
    Base configuration for all microservices.
    Enforces consistent environment, logging, and database patterns.
    """

    # Service Identity
    SERVICE_NAME: str = Field(..., description="Name of the service")
    SERVICE_VERSION: str = Field("0.1.0", description="Service version")

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production", "testing"] = Field(
        "development", description="Operational environment"
    )
    DEBUG: bool = Field(False, description="Debug mode")

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        "INFO", description="Logging level"
    )

    # Database
    DATABASE_URL: str | None = Field(None, description="Database connection URL")

    # Security
    SECRET_KEY: str = Field(
        default_factory=_get_or_create_dev_secret_key,
        min_length=32,
        description="Master secret key"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str | None, info: ValidationInfo) -> str:
        """Heals and validates the database URL."""
        env = info.data.get("ENVIRONMENT", "development")
        url = _ensure_database_url(v, env)
        return _upgrade_postgres_protocol(url)

    @model_validator(mode="after")
    def validate_security(self) -> "BaseServiceSettings":
        """Enforces security rules based on environment."""
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
            if self.SECRET_KEY == "changeme" or len(self.SECRET_KEY) < 32:
                 raise ValueError("Production SECRET_KEY is too weak")
        return self


# -----------------------------------------------------------------------------
# Main App Settings (Legacy Monolith + Gateway)
# -----------------------------------------------------------------------------

class AppSettings(BaseServiceSettings):
    """
    Configuration for the main application (Monolith/Gateway).
    Inherits from BaseServiceSettings for consistency.
    """
    SERVICE_NAME: str = "CogniForge-Core"

    PROJECT_NAME: str = Field("CogniForge", description="Project Name")

    # API
    API_V1_STR: str = "/api/v1"

    # CORS & Hosts
    BACKEND_CORS_ORIGINS: list[str] = Field(default=["*"])
    ALLOWED_HOSTS: list[str] = Field(default=["*"])

    # Infra
    REDIS_URL: str | None = None

    # Admin
    ADMIN_EMAIL: str = "admin@cogniforge.com"
    ADMIN_PASSWORD: str = "change_me_please_123!"

    @field_validator("BACKEND_CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_list(cls, v: str | list[str] | None) -> list[str]:
        return _normalize_csv_or_list(v)


@functools.lru_cache
def get_settings() -> AppSettings:
    """Singleton accessor for AppSettings."""
    return AppSettings()
