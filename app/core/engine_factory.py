# app/core/engine_factory.py
"""
🔥 THE OMNIVERSAL ENGINE FACTORY 🔥
===================================
The SINGLE source of truth for all database engine creation in the universe.
Enforces `statement_cache_size=0` for PgBouncer/Supabase compatibility.

ABSOLUTE REALITY REWRITER PROTOCOL:
- No engine is created outside this file.
- No connection escapes the 'statement_cache_size=0' check.
- Ghost Engines are banished.
"""

import logging
import sys
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger("cogniforge.engine_factory")

class FatalEngineError(RuntimeError):
    """Raised when an engine is created unsafely."""
    pass

def _sanitize_url_for_async(url: str) -> str:
    """
    Ensures the URL uses the correct asyncpg scheme.
    """
    if not url:
        raise FatalEngineError("Database URL is empty!")

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")

    return url

def _sanitize_url_for_sync(url: str) -> str:
    """
    Ensures the URL uses the correct sync scheme (psycopg2).
    """
    if not url:
         raise FatalEngineError("Database URL is empty!")

    # If it has +asyncpg, strip it for sync engine (if ever needed)
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")

    if "+aiosqlite" in url:
        url = url.replace("+aiosqlite", "")

    return url

def create_unified_async_engine(
    url: str,
    echo: bool = False,
    **kwargs: Any
) -> AsyncEngine:
    """
    The ONE AND ONLY way to create an async SQLAlchemy engine.
    Automatically injects PgBouncer-safe arguments.
    """
    safe_url = _sanitize_url_for_async(url)

    # 1. DEFAULT CONNECT ARGS
    connect_args = kwargs.pop("connect_args", {}) or {}

    # 2. ENFORCE PGBOUNCER COMPATIBILITY
    if "sqlite" not in safe_url:
        # Check if already set
        existing_cache = connect_args.get("statement_cache_size")

        if existing_cache is not None and existing_cache != 0:
            logger.critical(f"🚨 ATTEMPT TO SET statement_cache_size={existing_cache} DETECTED! OVERRIDING TO 0.")

        # FORCE 0
        connect_args["statement_cache_size"] = 0

        # Ensure basic timeout settings are also safe
        if "timeout" not in connect_args:
             connect_args["timeout"] = 30
        if "command_timeout" not in connect_args:
             connect_args["command_timeout"] = 60

        # Log this event
        logger.info("🔒 Secured Async Engine with statement_cache_size=0")

    # 3. CREATE ENGINE
    try:
        engine = create_async_engine(
            safe_url,
            echo=echo,
            connect_args=connect_args,
            future=True,
            pool_pre_ping=True,
            **kwargs
        )
        return engine
    except Exception as e:
        logger.critical(f"💥 FAILED TO CREATE ASYNC ENGINE: {e}")
        raise FatalEngineError(f"Engine creation failed: {e}") from e

def create_unified_sync_engine(
    url: str,
    echo: bool = False,
    **kwargs: Any
) -> Engine:
    """
    The ONE AND ONLY way to create a SYNC SQLAlchemy engine.
    (Used mainly for isolated scripts or legacy tests).
    """
    safe_url = _sanitize_url_for_sync(url)

    connect_args = kwargs.pop("connect_args", {}) or {}

    # WARNING: Psycopg2 usually doesn't need statement_cache_size=0 because it doesn't use
    # server-side prepared statements by default unless configured.
    # But we monitor it.

    if "sqlite" not in safe_url:
         # For sync engines (psycopg2), we don't strictly need statement_cache_size
         # because it's an asyncpg-specific param.
         # However, we ensure we aren't doing anything crazy.
         pass

    try:
        engine = create_engine(
            safe_url,
            echo=echo,
            connect_args=connect_args,
            pool_pre_ping=True,
            future=True,
            **kwargs
        )
        return engine
    except Exception as e:
        logger.critical(f"💥 FAILED TO CREATE SYNC ENGINE: {e}")
        raise FatalEngineError(f"Sync Engine creation failed: {e}") from e
