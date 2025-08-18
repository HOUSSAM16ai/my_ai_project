# config.py - The Multi-Environment Constitution (v2.0 - Test-Aware)

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # TESTING = False # Good practice to set defaults in the base class

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://' + os.environ.get('POSTGRES_USER', 'user') + \
        ':' + os.environ.get('POSTGRES_PASSWORD', 'password') + \
        '@' + os.environ.get('POSTGRES_HOST', 'db') + \
        '/' + os.environ.get('POSTGRES_DB', 'mydb')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    # --- [THE ULTIMATE FIX] ---
    # We provide a database URI for the testing environment.
    # Using SQLite in-memory is the fastest and cleanest way to run tests.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    # --- نهاية الإصلاح الخارق ---
    WTF_CSRF_ENABLED = False # Disable CSRF forms for simpler testing
    
class ProductionConfig(Config):
    """Production configuration."""
    # Production config should be carefully set
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') # Mandatory in production

config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig
)