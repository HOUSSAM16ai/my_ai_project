# app/core/kernel_v2/config_v2.py
"""
The Unified Configuration System (ConfigV2) for Reality Kernel v2.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigV2(BaseSettings):
    """
    Defines the application's configuration settings.
    Settings are loaded from environment variables and a .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./default.db"
    SECRET_KEY: str = "a_default_secret_key"
    # Add other settings as needed...


# Use lru_cache as a simple singleton pattern to ensure settings are loaded only once
@lru_cache
def get_settings() -> ConfigV2:
    """
    Loads and returns the application settings.
    The lru_cache decorator ensures this function is only executed once.
    """
    print("Loading configuration settings...")
    return ConfigV2()
