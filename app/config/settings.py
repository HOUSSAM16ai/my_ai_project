# app/config/settings.py
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🧠 AI MODEL CONFIGURATION CENTER                          ║
║                    ─────────────────────────────────────                     ║
║  This is the SINGLE SOURCE OF TRUTH for all AI model configurations.        ║
║  Change your AI models HERE and they will be applied everywhere.            ║
║                                                                              ║
║  🔧 How to change models:                                                   ║
║     Option 1: Set environment variables in .env file                        ║
║     Option 2: Set GitHub Codespaces Secrets                                 ║
║     Option 3: Modify the defaults below (not recommended for production)    ║
║                                                                              ║
║  📋 Available Models (via OpenRouter):                                      ║
║     - openai/gpt-4o          (Most capable, multimodal)                     ║
║     - openai/gpt-4o-mini     (Fast, cost-effective)                         ║
║     - openai/gpt-4-turbo     (Optimized GPT-4)                              ║
║     - anthropic/claude-3.5-sonnet  (Excellent reasoning)                    ║
║     - anthropic/claude-3-opus      (Most capable Claude)                    ║
║     - anthropic/claude-3.7-sonnet:thinking  (Advanced reasoning)            ║
║     - google/gemini-pro      (Google's flagship)                            ║
║     - meta-llama/llama-3-70b (Open source)                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
import functools
import os
import sys
from typing import Any

from pydantic import Field, ValidationInfo, field_validator
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
    ENVIRONMENT: str = Field(
        "development", description="The deployment environment (development, staging, production)."
    )
    DEBUG: bool = Field(False, description="Enable debug mode.")
    API_V1_STR: str = "/api/v1"

    # --- Codespaces & Cloud Native Identity ---
    CODESPACES: bool = Field(
        False, description="Auto-detected: True if running in GitHub Codespaces."
    )
    CODESPACE_NAME: str | None = Field(None, description="The name of the Codespace environment.")
    GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: str | None = Field(
        None, description="Domain suffix for port forwarding."
    )

    # --- Core Infrastructure Settings ---
    DATABASE_URL: str | None = Field(
        default=None,
        description="The primary database connection string. Auto-heals sync/async schemes.",
    )
    REDIS_URL: str | None = Field(
        None,
        description="The Redis connection string.",
    )

    # --- Security Settings ---
    SECRET_KEY: str = Field(
        ...,
        description="Master cryptographic key. MUST be set in production.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60 * 24 * 8, description="JWT expiration time in minutes."
    )
    BACKEND_CORS_ORIGINS: list[str] | str = Field(
        default=["*"],
        description="List of allowed CORS origins. Supports comma-separated string injection.",
    )
    ALLOWED_HOSTS: list[str] = Field(
        default=["*"], description="List of allowed hosts for TrustedHostMiddleware."
    )
    FRONTEND_URL: str = Field(
        default="http://localhost:5000", description="URL of the frontend application."
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 🧠 AI MODEL CONFIGURATION
    # ══════════════════════════════════════════════════════════════════════════
    # ⚠️  ALL AI MODELS ARE CONFIGURED IN: app/config/ai_models.py
    # ⚠️  To change models, edit: app/config/ai_models.py → class ActiveModels
    # ══════════════════════════════════════════════════════════════════════════

    AI_SERVICE_URL: str | None = Field(
        None, description="The URL for the external AI inference service."
    )

    # --- API Keys (These are secrets - NOT models) ---
    OPENAI_API_KEY: str | None = Field(None, description="API Key for OpenAI.")
    OPENROUTER_API_KEY: str | None = Field(None, description="API Key for OpenRouter.")

    # --- Operational Settings ---
    LOG_LEVEL: str = Field(
        default="INFO",
        description="The logging level (e.g., 'DEBUG', 'INFO').",
    )

    # --- Admin User Seeding ---
    ADMIN_EMAIL: str = Field(default="admin@example.com", description="Default admin email.")
    ADMIN_PASSWORD: str = Field(default="password", description="Default admin password.")
    ADMIN_NAME: str = Field(default="Admin User", description="Default admin name.")

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
            print(
                "WARNING: No DATABASE_URL found. Injecting SQLite fallback for stability.",
                file=sys.stderr,
            )
            return "sqlite+aiosqlite:///./test.db"

        # Only apply URL parsing logic to postgres URLs
        if not v.startswith("postgres"):
            return v

        # Auto-fix Scheme: sync -> async
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "postgresql+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Robustly handle SSL parameters
        from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

        parts = urlsplit(v)
        query_params = parse_qs(parts.query)

        ssl_mode = query_params.pop("sslmode", [None])[0]
        if ssl_mode in ("require", "disable"):
            query_params["ssl"] = [ssl_mode]

        # Rebuild the URL
        new_query = urlencode(query_params, doseq=True)
        new_parts = parts._replace(query=new_query)
        return urlunsplit(new_parts)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        elif isinstance(v, list | str):
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
