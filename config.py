# config.py - The Central Constitution of the System v2.0

import os
from dotenv import load_dotenv

# The Constitution is loaded ONCE at the very top.
load_dotenv()

class Config:
    """Base configuration settings. Shared by all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-that-must-be-changed'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- THE SUPERCHARGED FIX: The API Key is now an official part of the constitution ---
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')


class DevelopmentConfig(Config):
    """Configuration for the local development environment."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.environ.get('POSTGRES_USER')}:"
        f"{os.environ.get('POSTGRES_PASSWORD')}@"
        f"{os.environ.get('POSTGRES_HOST', 'db')}/"
        f"{os.environ.get('POSTGRES_DB')}"
    )

class TestingConfig(Config):
    """Configuration for automated tests."""
    TESTING = True
    # Use an in-memory SQLite database for lightning-fast, isolated tests.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:" 
    WTF_CSRF_ENABLED = False # Disable CSRF forms for simpler testing