# app/db/engine_v2.py
"""
The new asynchronous SQLAlchemy engine for Reality Kernel v2.
"""
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.kernel_v2.config_v2 import get_settings

# Get the database URL from the central configuration
settings = get_settings()
DATABASE_URL = settings.DATABASE_URL

# Create the async engine.
# `echo=True` is useful for debugging in development.
async_engine = create_async_engine(DATABASE_URL, echo=False)

def get_async_engine():
    """Returns the singleton async engine instance."""
    return async_engine
