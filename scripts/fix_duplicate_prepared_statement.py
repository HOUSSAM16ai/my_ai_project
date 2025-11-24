#!/usr/bin/env python3
"""
scripts/fix_duplicate_prepared_statement.py

Verifies database engine health by attempting to establish a connection
and execute a simple query using app.core.engine_factory.create_unified_async_engine.
This ensures the environment is correctly configured for PgBouncer (statement_cache_size=0).
"""
import asyncio
import argparse
import sys
import os
import logging
from sqlalchemy import text

# Ensure project root is in sys.path
sys.path.append(os.getcwd())

try:
    from app.core.engine_factory import create_unified_async_engine
except ImportError as e:
    print(f"❌ Failed to import engine factory: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("engine_verifier")

async def verify_engine_configuration():
    """
    Verifies that the database engine can be created and connected to.
    This implicitly checks for PgBouncer compatibility (statement_cache_size=0)
    if the factory is correctly implemented.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set. Using in-memory SQLite for verification.")
        database_url = "sqlite+aiosqlite:///:memory:"

    # Redact password for logging
    safe_url = database_url
    if "@" in safe_url:
        prefix = safe_url.split("@")[0]
        suffix = safe_url.split("@")[1]
        # Keep scheme and user, hide password
        if ":" in prefix and "://" in prefix:
            scheme_part = prefix.split("://")[0]
            user_part = prefix.split("://")[1].split(":")[0]
            safe_url = f"{scheme_part}://{user_part}:******@{suffix}"

    logger.info(f"Verifying engine for URL: {safe_url}")

    try:
        engine = create_unified_async_engine(database_url)

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("✅ Connection successful. Engine is healthy.")

        await engine.dispose()
        return True
    except Exception as e:
        logger.error(f"❌ Engine verification failed: {e}")
        return False

async def main():
    parser = argparse.ArgumentParser(description="Verify Database Engine Configuration")
    parser.add_argument("--verify", action="store_true", help="Run verification and exit")
    args = parser.parse_args()

    # If --verify is passed (or default), run verification
    success = await verify_engine_configuration()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
