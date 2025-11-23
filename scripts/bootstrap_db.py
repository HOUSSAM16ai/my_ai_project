import asyncio
import logging
import os
import sys
import urllib.parse
from typing import Optional

# Ensure project root is in sys.path
sys.path.append(os.getcwd())

from sqlalchemy import text
from sqlalchemy.engine.url import make_url, URL

from app.core.engine_factory import create_unified_async_engine, FatalEngineError

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
        raise ValueError("DATABASE_URL is empty")

    # 1. Basic Scheme Fixes
    if url_str.startswith("postgres://"):
        url_str = url_str.replace("postgres://", "postgresql://", 1)

    try:
        u = make_url(url_str)
    except Exception as e:
        raise ValueError(f"Invalid DATABASE_URL format: {e}")

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
    # render_as_string(hide_password=False)
    return u.render_as_string(hide_password=False)


# Alias for backward compatibility if needed, or internal use
sanitize_url = sanitize_database_url


async def verify_connection(url: str) -> bool:
    """
    Verifies the connection using the Unified Engine Factory.
    This ensures the URL is actually usable by our application logic.
    """
    try:
        engine = create_unified_async_engine(database_url=url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception as e:
        logger.error(f"Connection verification failed: {e}")
        return False


async def main():
    try:
        # 1. Get Raw URL
        raw_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

        # 2. Sanitize
        clean_url = sanitize_database_url(raw_url)
        logger.info(f"Sanitized URL scheme: {make_url(clean_url).drivername}")

        # 3. Verify
        # Skip verification if explicitly requested (e.g. for unit testing URL generation only)
        if os.environ.get("SKIP_DB_VERIFY") != "1":
            logger.info("Verifying connection...")
            if not await verify_connection(clean_url):
                logger.error("Could not connect to database.")
                sys.exit(1)
            logger.info("✅ Verification successful.")
        else:
            logger.info("⚠️ Skipping connection verification (SKIP_DB_VERIFY=1)")

        # 4. OUTPUT (STDOUT ONLY)
        # The ONLY thing printed to stdout.
        print(clean_url, end="")

    except Exception as e:
        logger.error(f"Bootstrap Critical Failure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
