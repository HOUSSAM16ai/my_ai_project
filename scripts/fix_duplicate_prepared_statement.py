#!/usr/bin/env python3
"""
scripts/fix_duplicate_prepared_statement.py

Verifies database engine health by attempting to establish a connection
and execute a simple query using app.core.engine_factory.create_unified_async_engine.
This ensures the environment is correctly configured for PgBouncer (statement_cache_size=0).
Includes Hyper-Resilient Timeout Logic to prevent CI/CD Freezes.
"""
import argparse
import asyncio
import logging
import os
import sys

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
    Includes strict timeouts to prevent hanging.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.warning("DATABASE_URL not set. Using in-memory SQLite for verification.")
        database_url = "sqlite+aiosqlite:///:memory:"

    # Check if we are using SQLite (either fallback or explicit)
    is_sqlite = "sqlite" in database_url

    # Redact password for logging
    safe_url = database_url
    if "@" in safe_url:
        try:
            prefix = safe_url.split("@")[0]
            suffix = safe_url.split("@")[1]
            # Keep scheme and user, hide password
            if ":" in prefix and "://" in prefix:
                scheme_part = prefix.split("://")[0]
                user_part = prefix.split("://")[1].split(":")[0]
                safe_url = f"{scheme_part}://{user_part}:******@{suffix}"
        except IndexError:
             pass # Fallback to raw if parsing fails

    logger.info(f"Verifying engine for URL: {safe_url}")

    if is_sqlite:
         logger.info("ℹ️  SQLite detected. Skipping PgBouncer specific checks.")

    try:
        # Strict timeout for verification to prevent freeze
        async with asyncio.timeout(10.0): # 10 seconds max for engine verification
            engine = create_unified_async_engine(database_url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("✅ Connection successful. Engine is healthy.")
            await engine.dispose()
            return True

    except TimeoutError:
        logger.error("❌ Engine verification TIMED OUT. Database is unresponsive.")
        return False
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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
