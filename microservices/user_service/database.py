"""
User Service Database Module.

Uses the Shared Kernel Factory Pattern.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from microservices.user_service.settings import get_settings
from microservices.user_service.models import SQLModel
from app.core.database import create_db_engine, create_session_factory

# 1. Initialize Settings
settings = get_settings()

# 2. Create Engine using Shared Kernel Factory
engine = create_db_engine(settings)

# 3. Create Session Factory using Shared Kernel Factory
async_session_factory = create_session_factory(engine)

async def init_db() -> None:
    """Initialize database schema."""
    # Strict Production Guardrail: No auto-create in Prod
    if settings.ENVIRONMENT == "production":
         # In production, we assume migrations ran.
         # Check if we can/should check for migration status here?
         # For now, just return.
         return

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for DB Session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
