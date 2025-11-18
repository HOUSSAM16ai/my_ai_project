import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings.
    """
    DATABASE_URL: str
    API_KEY: str
    # Add other settings as needed

    class Config:
        env_file = os.environ.get("ENV_FILE", ".env")
        env_file_encoding = 'utf-8'

def get_settings() -> Settings:
    return Settings()
