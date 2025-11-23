# app/config/settings.py
import functools

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """
    Enterprise-grade, framework-independent application settings.

    This class defines the configuration for the application, loaded from
    environment variables and a .env file. It uses Pydantic for validation
    and type hinting, providing a single, reliable source of truth for
    configuration values.
    """

    # --- Core Infrastructure Settings ---
    DATABASE_URL: str = Field(
        ...,
        description="The primary database connection string (e.g., 'postgresql://user:pass@host:port/db').",
    )
    REDIS_URL: str | None = Field(
        default=None,
        description="The Redis connection string, if used for caching or queues.",
    )

    # --- Security Settings ---
    SECRET_KEY: str = Field(
        ...,
        description="A secret key for signing sessions and tokens. Must be kept confidential.",
    )

    # --- Service Integration Settings ---
    AI_SERVICE_URL: str | None = Field(
        default=None, description="The URL for the external AI inference service."
    )
    DEFAULT_AI_MODEL: str = Field(
        default="openai/gpt-4o",
        description="The default AI model to use for inference.",
    )

    # --- Operational Settings ---
    LOG_LEVEL: str = Field(
        default="INFO",
        description="The logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR').",
    )

    # --- Pydantic Model Configuration ---
    # This instructs Pydantic to load settings from a .env file located
    # in the project's root directory.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow extra fields to be present in the environment without causing validation errors.
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str | None) -> str:
        if not v:
            # Fallback for testing or local dev if completely missing
            return "sqlite+aiosqlite:///./test.db"

        # 1. Auto-fix Scheme: sync -> async
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # 2. Auto-fix SSL Mode: libpq 'sslmode' -> asyncpg 'ssl'
        # Common issue with Supabase/Neon connection strings in asyncpg
        if "sslmode=require" in v:
            # asyncpg usually expects just explicit ssl context or param,
            # but many drivers/SQLAlchemy handle query params.
            # However, 'sslmode' is specific to libpq.
            # For asyncpg, we often need to replace it or rely on SQLAlchemy to pass it.
            # Safe bet: Replace sslmode=require with ssl=require which some layers understand,
            # OR leave it if SQLAlchemy's make_url handles it.
            # But asyncpg specifically doesn't like 'sslmode'.
            v = v.replace("sslmode=require", "ssl=require")

        return v


@functools.lru_cache
def get_settings() -> AppSettings:
    """
    Global singleton accessor for the AppSettings instance.

    This function returns a cached instance of the AppSettings, ensuring that
    the configuration is loaded and validated only once.

    Returns:
        AppSettings: The singleton application settings object.
    """
    return AppSettings()
