# app/core/cli_session.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


def get_session_factory(database_url: str):
    """
    Creates an async session factory for the given database URL.
    Enforces statement_cache_size=0 for asyncpg connections (Supabase/PgBouncer).
    """
    connect_args = {}

    # FIX: Apply to all non-SQLite databases (targeting Supabase/Postgres/Asyncpg)
    if "sqlite" not in database_url:
        connect_args["statement_cache_size"] = 0
        connect_args["timeout"] = 30
        connect_args["command_timeout"] = 60

    # Ensure async driver
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://")
    elif database_url.startswith("postgresql://") and "asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(database_url, connect_args=connect_args, future=True)
    return sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
