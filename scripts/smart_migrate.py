import asyncio
import logging
import os
import sys
import time

# Ensure we can import app modules
sys.path.append(os.getcwd())

from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import inspect, text

from app.core.engine_factory import create_unified_async_engine

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("smart_migrate")

# Load environment variables
load_dotenv()


def get_database_url():
    return os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")


async def check_db_state_with_retry(max_retries=5, timeout=10):
    """
    Checks the state of the database with robust retry logic and timeouts.
    Returns: (has_alembic_table: bool, has_user_table: bool)
    """
    database_url = get_database_url()
    last_error = None

    for attempt in range(max_retries):
        try:
            # Use Unified Factory
            engine = create_unified_async_engine(database_url)

            # Use asyncio.wait_for to enforce strict timeout
            async with asyncio.timeout(timeout):
                async with engine.connect() as conn:
                    def _inspect(connection):
                        inspector = inspect(connection)
                        tables = inspector.get_table_names()
                        return "alembic_version" in tables, "users" in tables

                    return await conn.run_sync(_inspect)

        except (TimeoutError, asyncio.TimeoutError):
            logger.warning(f"⏳ Attempt {attempt + 1}/{max_retries}: Connection timed out after {timeout}s.")
            last_error = "Connection timed out"
        except Exception as e:
            logger.warning(f"⚠️ Attempt {attempt + 1}/{max_retries}: Connection failed: {e}")
            last_error = e
        finally:
            # Ensure engine disposal if created
            if 'engine' in locals():
                await engine.dispose()

        # Exponential backoff
        if attempt < max_retries - 1:
            sleep_time = 2 ** attempt
            logger.info(f"Using Superhuman Backoff Algorithm... Sleeping {sleep_time}s")
            await asyncio.sleep(sleep_time)

    raise Exception(f"Failed to connect to database after {max_retries} attempts. Last error: {last_error}")


def run_smart_migration():
    """
    Executes the appropriate Alembic command based on DB state.
    """
    # Point to the correct alembic.ini location
    alembic_cfg_path = "migrations/alembic.ini"
    if not os.path.exists(alembic_cfg_path):
        # Fallback if it's in root
        alembic_cfg_path = "alembic.ini"

    if not os.path.exists(alembic_cfg_path):
        logger.error(f"❌ alembic.ini not found at {alembic_cfg_path}")
        sys.exit(1)

    alembic_cfg = Config(alembic_cfg_path)

    logger.info("🔍 Checking database state (Unified + Superhuman Retry)...")

    try:
        has_alembic, has_users = asyncio.run(check_db_state_with_retry())
    except Exception as e:
        logger.error(f"❌ Database State Check Failed: {e}")
        logger.error("This usually means the database is not ready or is locked.")
        sys.exit(1)

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
