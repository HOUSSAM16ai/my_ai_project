# config.py - The Multi-Environment Constitution

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-super-secret-key-that-you-should-change'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Add other base configurations here

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # We prioritize DATABASE_URL for cloud, but fall back to Docker variables for simplicity
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://' + os.environ.get('POSTGRES_USER', 'user') + \
        ':' + os.environ.get('POSTGRES_PASSWORD', 'password') + \
        '@' + os.environ.get('POSTGRES_HOST', 'db') + \
        '/' + os.environ.get('POSTGRES_DB', 'mydb')

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Use an in-memory DB for fast tests
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') # In production, DATABASE_URL is mandatory

# This dictionary maps the string names to the actual config classes
config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig
)