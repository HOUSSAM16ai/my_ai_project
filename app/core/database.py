"""
Canonical Database Factory for CogniForge.

Provides a unified Factory Pattern for creating AsyncEngines and SessionMakers.
Supports Microservices (Bounded Contexts) by allowing each service to instantiate
its own isolated DB stack based on its configuration.

Standards:
- Async First: Uses `sqlalchemy.ext.asyncio`.
- Factory Pattern: No global state for microservices; explicit `create_engine` calls.
- Connection Pooling: Configured via settings.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.settings.base import BaseServiceSettings, get_settings

logger = logging.getLogger(__name__)

__all__ = ["create_db_engine", "create_session_factory", "get_db", "engine", "async_session_factory"]

def create_db_engine(settings: BaseServiceSettings) -> AsyncEngine:
    """
    Creates an AsyncEngine based on the provided settings.
    Canonical implementation for all services.

    Handles 'sslmode' in asyncpg URLs by converting it to an SSL context,
    preventing 'unexpected keyword argument' errors.
    """
    db_url = settings.DATABASE_URL
    if not db_url:
        raise ValueError("DATABASE_URL is not set in settings.")

    engine_args = {
        "echo": settings.DEBUG,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    # Parse URL to safely handle driver-specific logic
    url_obj = make_url(db_url)

    if "sqlite" in url_obj.drivername:
        engine_args["connect_args"] = {"check_same_thread": False}
        logger.info(f"🔌 Database (SQLite): {settings.SERVICE_NAME}")

    elif "postgresql" in url_obj.drivername or "asyncpg" in url_obj.drivername:
        # GUARDRAIL: Force asyncpg driver if missing
        if url_obj.drivername == "postgresql":
            url_obj = url_obj.set(drivername="postgresql+asyncpg")
            db_url = url_obj.render_as_string(hide_password=False)

        # Initialize connect_args if not exists
        if "connect_args" not in engine_args:
            engine_args["connect_args"] = {}

        # PgBouncer Compatibility (Supabase)
        engine_args["connect_args"].update({
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0
        })

        # Handle 'sslmode' which asyncpg does not accept as a kwarg
        # We strip it from the URL and convert it to an 'ssl' context
        qs = dict(url_obj.query)
        if "sslmode" in qs:
            ssl_mode = qs.pop("sslmode")
            # Update db_url to exclude sslmode
            url_obj = url_obj.set(query=qs)

            # [CRITICAL GUARDRAIL]
            # Must use `render_as_string(hide_password=False)`!
            # 1. `str(url_obj)` masks passwords as '***', causing auth failures.
            # 2. We must PRESERVE URL encoding (e.g. '%40') for passwords.
            #    `render_as_string` handles this correctly for the driver.
            db_url = url_obj.render_as_string(hide_password=False)

            # Create SSL Context based on mode
            # 'disable' is default (no ssl arg)
            if ssl_mode in ("require", "verify-ca", "verify-full"):
                import ssl
                # Create a default context that verifies certificates
                ctx = ssl.create_default_context()

                if ssl_mode == "require":
                    # In 'require', we want SSL but don't strictly verify hostname/cert
                    # if the user just wants encryption.
                    # Note: Asyncpg's 'require' usually implies SSL but not necessarily full validation.
                    # For strict safety, 'verify-full' is best.
                    # Here we mimic common 'require' behavior: accept self-signed if needed or relax checks.
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE

                engine_args["connect_args"]["ssl"] = ctx
                logger.info(f"🔒 SSL Enabled (Mode: {ssl_mode})")

        # Production optimization
        is_dev = settings.ENVIRONMENT in ("development", "testing")
        engine_args["pool_size"] = 5 if is_dev else 40
        engine_args["max_overflow"] = 10 if is_dev else 60

        logger.info(f"🔌 Database (Postgres): {settings.SERVICE_NAME}")

    return create_async_engine(db_url, **engine_args)

def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Creates a configured sessionmaker for the given engine."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

# -----------------------------------------------------------------------------
# Global Singleton (For Legacy App/Core usage only)
# -----------------------------------------------------------------------------
# Ideally, we should remove this, but for Phase 2 backward compatibility, we keep it.
# Services should NOT use this. They should create their own in their `database.py`.

_legacy_settings = get_settings()
engine: AsyncEngine = create_db_engine(_legacy_settings)
async_session_factory = create_session_factory(engine)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting a DB session.
    Used by the Monolith/Core only. Microservices should define their own `get_db`.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
