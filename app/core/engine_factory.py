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
import copy
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

    # Create a deep copy of kwargs to avoid side effects
    final_kwargs = copy.deepcopy(kwargs)

    # 1. EXTRACT OR INIT CONNECT ARGS
    connect_args = final_kwargs.pop("connect_args", {}) or {}

    # 2. ENFORCE PGBOUNCER COMPATIBILITY
    if "sqlite" not in safe_url:
        # Critical check
        if connect_args.get("statement_cache_size") is not None:
            val = connect_args["statement_cache_size"]
            if val != 0:
                logger.critical(f"🚨 OVERRIDING UNSAFE statement_cache_size={val} TO 0")

        # FORCE 0
        connect_args["statement_cache_size"] = 0

        # Ensure timeouts
        if "timeout" not in connect_args:
             connect_args["timeout"] = 30
        if "command_timeout" not in connect_args:
             connect_args["command_timeout"] = 60

        logger.debug(f"🔒 Async Engine Configured: {safe_url.split('://')[0]} | cache_size=0")
    else:
        # SQLite cleanup
        final_kwargs.pop("pool_size", None)
        final_kwargs.pop("max_overflow", None)

    # 3. POOLING CONFIG
    if "sqlite" not in safe_url:
        if "pool_pre_ping" not in final_kwargs:
            final_kwargs["pool_pre_ping"] = True

    # 4. CREATE ENGINE
    try:
        engine = create_async_engine(
            safe_url,
            echo=echo,
            connect_args=connect_args,
            future=True,
            **final_kwargs
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
    """
    safe_url = _sanitize_url_for_sync(url)
    final_kwargs = copy.deepcopy(kwargs)

    connect_args = final_kwargs.pop("connect_args", {}) or {}

    if "sqlite" in safe_url:
         final_kwargs.pop("pool_size", None)
         final_kwargs.pop("max_overflow", None)

    try:
        engine = create_engine(
            safe_url,
            echo=echo,
            connect_args=connect_args,
            pool_pre_ping=True,
            future=True,
            **final_kwargs
        )
        return engine
    except Exception as e:
        logger.critical(f"💥 FAILED TO CREATE SYNC ENGINE: {e}")
        raise FatalEngineError(f"Sync Engine creation failed: {e}") from e
