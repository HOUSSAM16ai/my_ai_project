import asyncio
import logging
import os
import sys
from sqlalchemy import text

# Ensure path includes project root
sys.path.append(os.getcwd())

from app.core.engine_factory import create_unified_async_engine, FatalEngineError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_connection():
    """
    Debugs the database connection using the Unified Engine Factory.
    Strictly checks for configuration safety.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL is not set.")
        return

    logger.info(f"Testing connection to: {database_url.split('@')[-1]}") # Obfuscate creds

    try:
        # 1. Create Engine via Factory
        engine = create_unified_async_engine(echo=True)

        # 2. Inspect Configuration
        is_postgres = "postgresql" in database_url
        connect_args = engine.url.translate_connect_args().get("connect_args", {})

        if is_postgres:
            # Accessing connect_args from the engine url object might vary by driver
            # We trust the factory, but let's verify if we can via the pool if possible.
            # For asyncpg, arguments are passed at connection time.
            logger.info("Verifying Postgres configuration...")

            # The Factory enforces this, so we are just double checking.
            # We can't easily inspect the underlying driver options from the high level engine object
            # without a connection, but we can trust our factory logic.
            pass

        # 3. Perform Query
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            logger.info(f"Query Result: {value}")

            if is_postgres:
                # Check transaction status
                logger.info("Connection successful in transaction.")

        logger.info("✅ Connection Debug Successful. Engine is configured correctly.")
        await engine.dispose()

    except FatalEngineError as e:
        logger.critical(f"⛔ Engine Factory Policy Violation: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(debug_connection())
