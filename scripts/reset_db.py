import asyncio
import logging
import os
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.settings.base import get_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    settings = get_settings()
    db_url = settings.DATABASE_URL

    # Configure connection args for transaction pooler if needed
    connect_args = {}
    if "postgresql" in db_url or "asyncpg" in db_url:
        connect_args = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0
        }

    logger.info("Connecting to database...")
    engine = create_async_engine(db_url, echo=False, connect_args=connect_args)

    async with engine.begin() as conn:
        logger.info("Truncating content tables...")
        # Truncate tables. using CASCADE to handle foreign keys if any.
        # Tables: content_items, content_solutions, content_search
        await conn.execute(text("TRUNCATE TABLE content_items, content_solutions, content_search CASCADE;"))
        logger.info("Tables truncated successfully.")

    await engine.dispose()
    logger.info("Database reset complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
