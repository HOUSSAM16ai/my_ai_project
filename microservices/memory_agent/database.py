import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from microservices.memory_agent.models import SQLModel
from microservices.memory_agent.settings import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

_init_lock = asyncio.Lock()
_is_initialized = False


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def _ensure_initialized() -> None:
    global _is_initialized
    if _is_initialized:
        return
    async with _init_lock:
        if _is_initialized:
            return
        await init_db()
        _is_initialized = True


async def get_session() -> AsyncSession:
    await _ensure_initialized()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
