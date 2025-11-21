# app/core/config.py

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CogniForge Reality Kernel V3"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    SECRET_KEY: str = "changeme_in_production_super_secret_key_123456"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"

    # LLM
    OPENAI_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None

    # Cors
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str | None) -> str:
        if not v:
            return "sqlite+aiosqlite:///./test.db"

        # 1. Auto-fix Scheme: sync -> async
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # 2. Auto-fix SSL Mode for asyncpg compatibility
        # asyncpg often rejects 'sslmode', preferring 'ssl' param or context.
        if "sslmode=require" in v:
            v = v.replace("sslmode=require", "ssl=require")

        return v


settings = Settings()
