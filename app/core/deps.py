import logging
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import get_settings, Settings
from app.core.logger import get_logger as get_logger_instance

def get_db() -> Generator[Session, None, None]:
    """
    Database dependency provider.
    """
    settings = get_settings()
    # Use a synchronous engine for the sync dependency
    engine = create_engine(settings.DATABASE_URL.replace("+aiosqlite", ""))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_async() -> AsyncGenerator[Session, None]:
    """
    Async database dependency provider.
    """
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close()

def get_settings_dep() -> Settings:
    """
    Settings dependency provider.
    """
    return get_settings()

def get_logger(name: str = "default") -> logging.Logger:
    """
    Logger dependency provider.
    """
    return get_logger_instance(name)
