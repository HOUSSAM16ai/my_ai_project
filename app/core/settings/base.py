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
from typing import Literal

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

def _lenient_json_loads(value: str) -> object:
    """Parses environment values as JSON, allowing simple strings on failure."""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value

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
        env_json_loads=_lenient_json_loads,
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str | None, info: ValidationInfo) -> str:
        """Heals and validates the database URL."""
        env = info.data.get("ENVIRONMENT", "development")
        url = _ensure_database_url(v, env)
        # Note: _upgrade_postgres_protocol also handles Supabase Pooler compatibility
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

    @computed_field
    @property
    def is_production(self) -> bool:
        """Returns True if we are in production mode."""
        return self.ENVIRONMENT == "production"

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
    VERSION: str = Field("4.0.0-legendary", description="System Version")
    DESCRIPTION: str = Field("AI-Powered Platform", description="System Description")

    # API
    API_V1_STR: str = "/api/v1"
    API_STRICT_MODE: bool = Field(True, description="Strict API Security")

    # CORS & Hosts
    BACKEND_CORS_ORIGINS: list[str] = Field(default=["*"])
    ALLOWED_HOSTS: list[str] = Field(default=["*"])

    # Infra
    REDIS_URL: str | None = None
    DB_POOL_SIZE: int = Field(40, description="DB Pool Size")
    DB_MAX_OVERFLOW: int = Field(60, description="DB Max Overflow")

    # Admin
    ADMIN_EMAIL: str = "admin@cogniforge.com"
    ADMIN_PASSWORD: str = "change_me_please_123!"
    ADMIN_NAME: str = "Supreme Administrator"

    # Service URLs
    USER_SERVICE_URL: str | None = Field(None, description="User service base URL")

    # AI (Missing fields restored)
    OPENAI_API_KEY: str | None = Field(None, description="OpenAI API Key")
    OPENROUTER_API_KEY: str | None = Field(None, description="OpenRouter API Key")
    AI_SERVICE_URL: str | None = Field(None, description="AI Service URL")

    # Codespaces / Dev Environment (Missing fields restored)
    CODESPACES: bool = Field(False, description="Is running in Codespaces")
    CODESPACE_NAME: str | None = Field(None, description="Codespace Name")
    GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: str | None = Field(None)
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend URL")

    # Security (Tokens)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 8, description="Access Token Expiry")
    REAUTH_TOKEN_EXPIRE_MINUTES: int = Field(10, description="Re-auth Token Expiry")

    @field_validator("BACKEND_CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_list(cls, v: str | list[str] | None) -> list[str]:
        return _normalize_csv_or_list(v)

    @field_validator("CODESPACES", mode="before")
    @classmethod
    def detect_codespaces(cls, v: dict[str, str | int | bool]) -> bool:
        if v is not None:
            return bool(v)
        return os.getenv("CODESPACES") == "true"

    @field_validator("USER_SERVICE_URL", mode="before")
    @classmethod
    def default_user_service_url(cls, v: str | None, info: ValidationInfo) -> str:
        """
        ضمان عنوان خدمة المستخدمين الافتراضي وفق بيئة التشغيل.

        يعتمد على قيمة CODESPACES لتجنب مشاكل DNS في البيئات المستضافة.
        """
        if v:
            return v
        is_codespaces = info.data.get("CODESPACES")
        if is_codespaces is None:
            is_codespaces = os.getenv("CODESPACES") == "true"
        return cls._default_user_service_url(is_codespaces=bool(is_codespaces))

    @staticmethod
    def _default_user_service_url(*, is_codespaces: bool) -> str:
        """
        تحديد عنوان خدمة المستخدمين الافتراضي وفق بيئة التشغيل.

        يتم توجيه بيئات Codespaces إلى localhost لتفادي مشاكل DNS،
        بينما تستخدم البيئات الأخرى اسم خدمة الشبكة الداخلية.
        """
        if is_codespaces:
            return "http://localhost:8003"
        return "http://user-service:8003"

    @model_validator(mode="after")
    def validate_production_security(self) -> "AppSettings":
        """Strict Production Guardrails"""
        if self.ENVIRONMENT == "production":
             if self.ALLOWED_HOSTS == ["*"]:
                 raise ValueError("SECURITY RISK: ALLOWED_HOSTS cannot be '*' in production.")
             if self.BACKEND_CORS_ORIGINS == ["*"]:
                 raise ValueError("SECURITY RISK: BACKEND_CORS_ORIGINS cannot be '*' in production.")
        return self


@functools.lru_cache
def get_settings() -> AppSettings:
    """Singleton accessor for AppSettings."""
    return AppSettings()
