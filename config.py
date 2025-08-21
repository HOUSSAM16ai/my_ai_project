# config.py - The Hyper-Configurable, Resilient Constitution (v3.0 - Enterprise Ready)

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    Base configuration class. Contains settings common to all environments.
    This class acts as the single source of truth for all configurable parameters.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-that-you-should-change'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- [THE UNIFIED SECRETS PROTOCOL] ---
    # We load all external API keys and secrets here, making them available
    # to the entire application via `current_app.config`.
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    # Future keys like SUPABASE_KEY would be added here.
    
    # --- [THE STRATEGIC AI CONFIGURATION PROTOCOL] ---
    # Centralized control over the AI Agent's behavior.
    # We use `os.environ.get` with defaults to allow easy overriding via .env
    DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL', 'openai/gpt-4o')
    AGENT_MAX_STEPS = int(os.environ.get('AGENT_MAX_STEPS', 5))
    
    # --- [THE RESILIENCE PROTOCOL] ---
    # These engine options make our database connections robust against timeouts.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True, # Checks if a connection is alive before using it.
        'pool_recycle': 280,   # Recycles connections older than 280s.
        'pool_timeout': 20,    # How long to wait for a connection from the pool.
    }

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    # In development, we use the full Supabase URL directly from the .env file.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """Testing-specific configuration for an isolated, fast environment."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # We disable pooling for the simple in-memory SQLite DB as it's not needed.
    SQLALCHEMY_ENGINE_OPTIONS = {}
    # We also don't need a real API key for most tests.
    OPENROUTER_API_KEY = 'test-key' 

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    TESTING = False
    # In production, the DATABASE_URL MUST be set explicitly in the environment.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

# A dictionary to access config classes by name string (the Application Factory pattern).
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig
)