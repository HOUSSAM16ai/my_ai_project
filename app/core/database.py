from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings

# Async Engine (Primary for FastAPI)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync Engine (For Background Threads/Legacy Compatibility)
# Convert async sqlite url to sync for fallback
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+aiosqlite", "")
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in SYNC_DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
