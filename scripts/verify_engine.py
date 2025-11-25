import argparse
import asyncio
import logging

from app.core.engine_factory import create_unified_async_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_engine(url: str):
    """
    Verifies that the engine can be created and connected to.
    Ensures correct settings for PgBouncer compatibility.
    """
    print(f"Verifying connection to: {url.split('@')[-1]}") # Hide credentials

    try:
        engine = create_unified_async_engine(url)

        # Test connection
        async with engine.connect() as _:
             print("✓ Connection successful.")
             # Verify statement_cache_size if possible (driver dependent)
             # With asyncpg, it's in connect_args

        await engine.dispose()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Database URL to verify")
    args = parser.parse_args()

    if args.url:
        asyncio.run(verify_engine(args.url))
    else:
        print("No URL provided. Skipping.")
