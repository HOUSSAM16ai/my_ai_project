"""إعدادات قاعدة البيانات المحلية لخدمة البحث."""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@lru_cache(maxsize=1)
def _get_engine():
    """يبني محرك قاعدة البيانات اعتماداً على DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is required for research agent database access.")
    return create_async_engine(database_url, pool_pre_ping=True)


def async_session_factory() -> async_sessionmaker[AsyncSession]:
    """ينشئ مصنع جلسات غير متزامن لخدمة البحث."""
    engine = _get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
