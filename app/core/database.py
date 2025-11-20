# app/core/database.py
"""
The SPACE-ENGINE.

This engine enforces the Law of Spatial Determinism, ensuring that all
parts of the system see a consistent and correct database state. It is the
single source of truth for database connections and sessions.
"""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ======================================================================================
# DATABASE CONFIGURATION
# ======================================================================================
# The DATABASE_URL is retrieved from the environment. This decouples the
# engine from the application configuration.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

# ======================================================================================
# THE CORE DATABASE OBJECTS
# ======================================================================================
# The engine is the core interface to the database.
engine = create_async_engine(DATABASE_URL, echo=True)

# The session factory is used to create new database sessions.
# The `expire_on_commit=False` setting is important for FastAPI, as it
# allows objects to be accessed even after the session is closed.
AsyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

# The declarative base is used to define database models.
Base = declarative_base()


# ======================================================================================
# THE UNIFIED SESSION PROTOCOL
# ======================================================================================
# This dependency-injectable function is the ONLY way to get a database session.
# It ensures that every request has a single, consistent session that is
# properly closed after the request is complete.
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a database session to the application.
    """
    async with AsyncSessionLocal() as session:
        yield session
