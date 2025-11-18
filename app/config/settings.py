# app/config/settings.py
import functools
from typing import Optional

from pydantic import Field
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
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="The Redis connection string, if used for caching or queues.",
    )

    # --- Security Settings ---
    SECRET_KEY: str = Field(
        ...,
        description="A secret key for signing sessions and tokens. Must be kept confidential.",
    )

    # --- Service Integration Settings ---
    AI_SERVICE_URL: Optional[str] = Field(
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


@functools.lru_cache()
def get_settings() -> AppSettings:
    """
    Global singleton accessor for the AppSettings instance.

    This function returns a cached instance of the AppSettings, ensuring that
    the configuration is loaded and validated only once.

    Returns:
        AppSettings: The singleton application settings object.
    """
    return AppSettings()
