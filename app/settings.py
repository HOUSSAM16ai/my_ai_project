# app/settings.py
"""
Legacy settings file - kept for backward compatibility.
AI models are now configured in: app/config/ai_models.py
"""

from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "a-super-secret-key-that-you-should-change"
    FLASK_ENV: str = "development"
    DATABASE_URL: str = ""

    # Database settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {"pool_pre_ping": True}

    # AI Model - reads from central config
    @property
    def DEFAULT_AI_MODEL(self) -> str:
        from app.config.ai_models import get_ai_config

        return get_ai_config().primary_model

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
