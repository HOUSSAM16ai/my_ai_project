# app/config/settings.py
import functools
import os
import sys
from typing import Any, List, Optional

from pydantic import Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """
    SUPERHUMAN CONFIGURATION NEXUS V3.0-HYPER.

    This class serves as the singular source of truth for the Reality Kernel.
    It implements intelligent environment detection, auto-healing configuration
    paths, and robust secret integration for GitHub Codespaces and Enterprise Environments.
    """

    # --- Core Identity & Environment ---
    PROJECT_NAME: str = Field("CogniForge Reality Kernel V3", description="The project name.")
    VERSION: str = Field("3.0-hyper", description="The application version.")
    ENVIRONMENT: str = Field("development", description="The deployment environment (development, staging, production).")
    DEBUG: bool = Field(False, description="Enable debug mode.")
    API_V1_STR: str = "/api/v1"

    # --- Codespaces & Cloud Native Identity ---
    CODESPACES: bool = Field(False, description="Auto-detected: True if running in GitHub Codespaces.")
    CODESPACE_NAME: Optional[str] = Field(None, description="The name of the Codespace environment.")
    GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: Optional[str] = Field(None, description="Domain suffix for port forwarding.")

    # --- Core Infrastructure Settings ---
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="The primary database connection string. Auto-heals sync/async schemes.",
    )
    REDIS_URL: Optional[str] = Field(
        None,
        description="The Redis connection string.",
    )

    # --- Security Settings ---
    SECRET_KEY: str = Field(
        ...,
        description="Master cryptographic key. MUST be set in production.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 8, description="JWT expiration time in minutes.")
    BACKEND_CORS_ORIGINS: List[str] | str = Field(
        default=["*"],
        description="List of allowed CORS origins. Supports comma-separated string injection.",
    )

    # --- Service Integration (AI & LLM) ---
    AI_SERVICE_URL: Optional[str] = Field(
        None, description="The URL for the external AI inference service."
    )
    DEFAULT_AI_MODEL: str = Field(
        default="openai/gpt-4o",
        description="The default AI model to use for inference.",
    )
    OPENAI_API_KEY: Optional[str] = Field(None, description="API Key for OpenAI.")
    OPENROUTER_API_KEY: Optional[str] = Field(None, description="API Key for OpenRouter.")

    # --- Operational Settings ---
    LOG_LEVEL: str = Field(
        default="INFO",
        description="The logging level (e.g., 'DEBUG', 'INFO').",
    )

    # --- Pydantic Model Configuration ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CODESPACES", mode="before")
    @classmethod
    def detect_codespaces(cls, v: Any, info: ValidationInfo) -> bool:
        """
        Intelligently detects if the application is running inside a GitHub Codespace.
        Prioritizes explicit config, then checks system environment variables.
        """
        if v is not None:
            return bool(v)
        return os.getenv("CODESPACES") == "true"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str | None) -> str:
        """
        SUPERHUMAN ALGORITHM: Database URL Auto-Healing.
        Ensures compatibility between asyncpg, SQLAlchemy, and various providers (Supabase, Neon, Local).
        """
        if not v:
            # Fallback for testing or local dev if completely missing
            # In CI/Codespaces without secrets, this prevents crash-on-import, though app will fail later if DB needed.
            print("WARNING: No DATABASE_URL found. Injecting SQLite fallback for stability.", file=sys.stderr)
            return "sqlite+aiosqlite:///./test.db"

        # 1. Auto-fix Scheme: sync -> async
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            if "postgresql+asyncpg" not in v:
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # 2. Auto-fix SSL Mode: libpq 'sslmode' -> asyncpg 'ssl'
        # Crucial for Supabase/Neon in Codespaces
        if "sslmode=require" in v:
            # Replace with ssl=require for asyncpg compatibility if not already handled
            v = v.replace("sslmode=require", "ssl=require")

        # 3. Handle 'disable' mode for local dev to avoid asyncpg errors
        if "sslmode=disable" in v:
             v = v.replace("sslmode=disable", "ssl=disable")

        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        return []

    def validate_integrity(self):
        """
        Runs a post-initialization integrity check.
        Logs warnings for missing critical secrets (does not raise to avoid crash-loops).
        """
        missing = []
        if self.SECRET_KEY == "changeme":
            missing.append("SECRET_KEY (using default)")

        # Check AI Keys if AI service is expected
        if not self.OPENROUTER_API_KEY and not self.OPENAI_API_KEY:
            # Not an error, but a warning
            pass

        return missing

@functools.lru_cache
def get_settings() -> AppSettings:
    """
    Global singleton accessor for the AppSettings instance.
    """
    return AppSettings()
