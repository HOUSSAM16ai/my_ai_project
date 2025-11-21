import asyncio
import logging
import os
import sys

# Ensure we can import app modules
sys.path.append(os.getcwd())

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_migrate")


async def check_db_state():
    """
    Checks the state of the database to determine the migration strategy.
    Returns: (has_alembic_table: bool, has_user_table: bool)
    """
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:

        def _inspect(connection):
            inspector = inspect(connection)
            tables = inspector.get_table_names()
            return "alembic_version" in tables, "users" in tables

        return await conn.run_sync(_inspect)


def run_smart_migration():
    """
    Executes the appropriate Alembic command based on DB state.
    """
    # Point to the correct alembic.ini location
    alembic_cfg_path = "migrations/alembic.ini"
    if not os.path.exists(alembic_cfg_path):
        # Fallback if it's in root
        alembic_cfg_path = "alembic.ini"

    alembic_cfg = Config(alembic_cfg_path)

    logger.info("🔍 Checking database state...")

    # We need to run the async check in a loop loop
    has_alembic, has_users = asyncio.run(check_db_state())

    if has_alembic:
        logger.info("✅ 'alembic_version' table found. Continuing with standard migration...")
        command.upgrade(alembic_cfg, "head")
    elif has_users:
        logger.warning("⚠️  Existing tables found ('users') but NO 'alembic_version'.")
        logger.warning("🛑  Preventing re-creation errors. Stamping DB as 'head'...")
        command.stamp(alembic_cfg, "head")
        logger.info("✅  Database stamped. You are now synced with the codebase.")
    else:
        logger.info("✨  Fresh database detected. Running full migration...")
        command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    try:
        run_smart_migration()
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
