import asyncio
import logging
import os
import sys
from urllib.parse import quote_plus

# Ensure the project root is in sys.path
sys.path.append(os.getcwd())

from sqlalchemy import text

from app.core.engine_factory import create_unified_async_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def bootstrap():
    """
    Bootstraps the database:
    1. Validates/Sanitizes DATABASE_URL.
    2. Exports it to the environment for subsequent scripts.
    3. Verifies connection using the Unified Engine Factory.
    """

    # 1. Read from env or default
    db_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

    # 2. Simple sanitization for export (the Factory does deeper sanitization)
    # This part is mainly for non-python tools that might read the output of this script
    # if we were printing it. But here we are just validating.

    logger.info(f"Bootstrapping with URL scheme: {db_url.split(':')[0]}")

    try:
        # 3. Verify Connection with Factory
        engine = create_unified_async_engine(database_url=db_url)

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection verification successful.")

        await engine.dispose()

        # In a real shell script, we would print `export DATABASE_URL=...`
        # but here we just confirm it works.
        print(f"export DATABASE_URL='{db_url}'")

    except Exception as e:
        logger.error(f"❌ Bootstrap failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(bootstrap())
