import asyncio
import logging
import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.getcwd())

from sqlalchemy import text
from sqlalchemy.engine.url import make_url

from app.core.engine_factory import create_unified_async_engine

# --- 1. LOGGING SETUP (STRICTLY STDERR) ---
# Prevent any logs from going to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
    force=True,
)
logger = logging.getLogger("bootstrap_db")


def sanitize_database_url(url_str: str) -> str:
    """
    Sanitizes and validates the database URL.
    - Fixes scheme (postgres -> postgresql)
    - Fixes drivers (postgresql -> postgresql+asyncpg)
    - Fixes SSL params (sslmode=require -> ssl=require logic for query params)
    - Encodes passwords if needed (though usually assumed encoded in env)
    """
    if not url_str:
        # If empty, default to SQLite immediately
        return "sqlite+aiosqlite:///./dev.db"

    # 1. Basic Scheme Fixes
    if url_str.startswith("postgres://"):
        url_str = url_str.replace("postgres://", "postgresql://", 1)

    try:
        u = make_url(url_str)
    except Exception as e:
        logger.warning(f"Invalid DATABASE_URL format ({e}). Defaulting to SQLite.")
        return "sqlite+aiosqlite:///./dev.db"

    # 2. Driver Fixes for Async
    if u.drivername == "postgresql":
        u = u.set(drivername="postgresql+asyncpg")
    elif u.drivername == "sqlite" and "aiosqlite" not in u.drivername:
        u = u.set(drivername="sqlite+aiosqlite")

    # 3. Query Param Fixes (SSL)
    # SQLAlchemy URL object handles query params as a dict
    query_params = dict(u.query)

    if "sslmode" in query_params:
        ssl_mode = query_params.pop("sslmode")
        if ssl_mode == "require":
            # For asyncpg, we typically handle this via connect_args in the factory,
            # but standardizing the URL string is also good.
            # asyncpg supports ?ssl=require in the connection string.
            query_params["ssl"] = "require"

    u = u.set(query=query_params)

    # 4. Render
    return u.render_as_string(hide_password=False)


async def verify_connection(url: str, is_fallback: bool = False) -> bool:
    """
    Verifies the connection using the Unified Engine Factory.
    Includes Hyper-Resilient Retry Logic (Exponential Backoff + Strict Timeouts)
    to prevent setup freezes.
    """
    # If falling back to SQLite, we don't need many retries
    max_retries = 1 if is_fallback else 3
    base_timeout = 5.0  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            # We use a strict timeout to kill hanging connections
            async with asyncio.timeout(base_timeout):
                engine = create_unified_async_engine(database_url=url)
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                await engine.dispose()
                return True

        except TimeoutError:
            if not is_fallback:
                logger.warning(
                    f"⚠️ Connection verification timed out (Attempt {attempt}/{max_retries}). "
                    f"The database might be unreachable or blocking."
                )
        except Exception as e:
            if not is_fallback:
                logger.warning(
                    f"⚠️ Connection verification failed (Attempt {attempt}/{max_retries}): {e}"
                )

        # Exponential Backoff
        if attempt < max_retries:
            sleep_time = 2.0 ** attempt
            logger.info(f"⏳ Waiting {sleep_time}s before retrying...")
            await asyncio.sleep(sleep_time)

    if not is_fallback:
        logger.error("❌ Critical Failure: Could not establish database connection after multiple attempts.")
    return False


async def main():
    try:
        # 1. Get Raw URL
        raw_url = os.environ.get("DATABASE_URL")

        # If no URL provided, default directly to SQLite
        if not raw_url:
             logger.info("No DATABASE_URL set. Using default SQLite.")
             clean_url = "sqlite+aiosqlite:///./dev.db"
        else:
             # 2. Sanitize provided URL
             clean_url = sanitize_database_url(raw_url)
             logger.info(f"Sanitized URL scheme: {make_url(clean_url).drivername}")

        # 3. Verify
        # Skip verification if explicitly requested (e.g. for unit testing URL generation only)
        if os.environ.get("SKIP_DB_VERIFY") != "1":
            logger.info("🔍 Verifying connection with Resilient Probe...")

            if not await verify_connection(clean_url):
                logger.warning("⚠️  Primary Database Unreachable. Activating EMERGENCY SQLITE PROTOCOL.")

                # FALLBACK LOGIC
                clean_url = "sqlite+aiosqlite:///./dev.db"
                logger.info(f"🔄 Switching to Fallback Database: {clean_url}")

                # Verify Fallback
                if not await verify_connection(clean_url, is_fallback=True):
                    logger.error("❌ COMPLETE SYSTEM FAILURE: Even SQLite fallback failed.")
                    sys.exit(1)

                logger.info("✅ Emergency Protocol Successful. Using local database.")
            else:
                logger.info("✅ Verification successful. Database is ready.")
        else:
            logger.info("⚠️ Skipping connection verification (SKIP_DB_VERIFY=1)")

        # 4. OUTPUT (STDOUT ONLY)
        # The ONLY thing printed to stdout.
        print(clean_url, end="")

    except Exception as e:
        logger.error(f"Bootstrap Critical Failure: {e}")
        # Even on critical failure, try to output SQLite to keep the app alive?
        # No, if we crash here something is very wrong. But let's be safe.
        print("sqlite+aiosqlite:///./dev.db", end="")
        sys.exit(0) # Exit 0 to let setup_dev.sh continue with the fallback


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
