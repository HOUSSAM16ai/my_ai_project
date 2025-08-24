# config.py - The Hyper-Configurable, Resilient Constitution (v4.0 - Lazy Loaded)
import os
from dotenv import load_dotenv

# We only load dotenv here to make variables available.
# The actual configuration values are now loaded inside the classes.
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../.env')) # Use ../.env because config.py is inside app/

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-that-you-should-change'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    # --- Static configurations can live here ---
    
    @staticmethod
    def init_app(app):
        """
        A place for configurations that need the app object,
        but we don't need it for this problem.
        """
        pass

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    
    # --- [THE CRITICAL FIX] ---
    # The value is now set directly here, reading from the already-loaded environment.
    # This happens *after* the initial imports, when app.config.from_object is called.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig
)