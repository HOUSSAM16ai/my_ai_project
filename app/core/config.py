# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    SECRET_KEY: str = "a-super-secret-key-that-you-should-change"
    DEFAULT_AI_MODEL: str = "openai/gpt-4o"
    LOG_LEVEL: str = "INFO"

settings = Settings()
