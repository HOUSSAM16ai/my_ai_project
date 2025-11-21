# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Ensure connection args are set for Supabase/PgBouncer compatibility
connect_args = {}
if "sqlite" not in settings.DATABASE_URL:
    connect_args["statement_cache_size"] = 0
    connect_args["timeout"] = 30
    connect_args["command_timeout"] = 60

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
    future=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as db:
        yield db
