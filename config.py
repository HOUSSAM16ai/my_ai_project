# config.py - The Multi-Environment, API-Aware & Resilient Constitution (v2.2)

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration class. Contains settings common to all environments."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-that-you-should-change'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- [THE CONFIGURATION INJECTION PROTOCOL] ---
    # We declare all application-level config variables here in the base class.
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
    # Add other global keys here (e.g., AZURE_SEARCH_KEY) as the project grows.
    # --- نهاية البروتوكول ---

    # --- [THE RESILIENCE PROTOCOL] ---
    # These engine options make our database connections robust against timeouts.
    # They apply to all environments that use SQLAlchemy.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True, # Checks if a connection is alive before using it.
        'pool_recycle': 280,   # Recycles connections after 280 seconds (less than standard timeouts).
        'pool_timeout': 20,    # How long to wait for a connection from the pool.
    }
    # --- نهاية البروتوكول ---

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    # This flexible URI works for both local Docker and remote Azure connections.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://' + os.environ.get('POSTGRES_USER', 'user') + \
        ':' + os.environ.get('POSTGRES_PASSWORD', 'password') + \
        '@' + os.environ.get('POSTGRES_HOST', 'db') + \
        '/' + os.environ.get('POSTGRES_DB', 'mydb')

class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # We don't need pool options for a simple in-memory SQLite DB
    SQLALCHEMY_ENGINE_OPTIONS = {}

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    TESTING = False
    # In production, the DATABASE_URL must be set explicitly.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

# A dictionary to access config classes by name string.
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig
)