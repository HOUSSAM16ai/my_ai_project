import os
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.engine_factory import create_unified_async_engine

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# UNIFIED ENGINE FACTORY INTEGRATION
# We no longer create the engine directly. We use the factory.
# ------------------------------------------------------------------------------

def get_connection_string() -> str:
    """
    Retrieves the database URL.
    Prioritizes os.environ['DATABASE_URL'] if available.
    """
    return os.environ.get("DATABASE_URL", settings.DATABASE_URL)

FINAL_DATABASE_URL = get_connection_string()

# Create Async Engine via Factory
engine = create_unified_async_engine(FINAL_DATABASE_URL, echo=False)

async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ------------------------------------------------------------------------------
# SYNC ENGINE TRAP
# ------------------------------------------------------------------------------
# We explicitly do NOT expose a sync engine here for the app.
# If valid legacy code needs it, it must use create_unified_sync_engine explicitly.
sync_engine = None
SessionLocal = None

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session

# Aliases for compatibility
Base = SQLModel
AsyncSessionLocal = async_session_factory
