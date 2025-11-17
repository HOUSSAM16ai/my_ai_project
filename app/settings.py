
# app/settings.py
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "a-super-secret-key-that-you-should-change"
    DEFAULT_AI_MODEL: str = "openai/gpt-4o"
    FLASK_ENV: str = "development"
    DATABASE_URL: str = ""

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {"pool_pre_ping": True}

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
