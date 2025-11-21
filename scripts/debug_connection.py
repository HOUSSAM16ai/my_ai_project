import asyncio
import os
import sys
import urllib.parse

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def mask_url(url: str) -> str:
    """Masks the password in the connection string."""
    if not url:
        return "None"
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.password:
            masked = url.replace(parsed.password, "***")
            return masked
        return url
    except Exception:
        return "Invalid URL Format"

async def test_connection():
    print("🔍 DEBUG CONNECTION PROBE INITIATED")

    url = os.getenv("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL is not set!")
        sys.exit(1)

    # Normalize URL for display
    display_url = url
    if "postgresql" in url and "sslmode=require" in url:
        display_url = url.replace("sslmode=require", "ssl=require")

    print(f"📝 Raw DATABASE_URL Scheme: {display_url.split('://')[0]}")
    print(f"📝 Masked DATABASE_URL: {mask_url(display_url)}")

    is_sqlite = "sqlite" in url

    # 1. Asyncpg Raw Connection Test
    if not is_sqlite:
        try:
            import asyncpg
            print("\n🧪 Attempting RAW asyncpg connection...")

            # Prepare DSN
            dsn = url
            if "postgresql+asyncpg://" in dsn:
                dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")

            if "sslmode=require" in dsn:
                 dsn = dsn.replace("sslmode=require", "ssl=require")

            # Check if we need to inject statement_cache_size=0
            # For raw asyncpg, we pass it as kwarg
            print(f"   - Connecting with statement_cache_size=0...")
            conn = await asyncpg.connect(dsn, statement_cache_size=0, timeout=10)

            version = await conn.fetchval('SELECT version()')
            print(f"✅ Asyncpg Connection Successful! Version: {version}")
            await conn.close()
        except Exception as e:
            print(f"❌ Asyncpg Connection Failed: {e}")
    else:
        print("\nℹ️  Skipping RAW asyncpg check (SQLite detected).")

    # 2. SQLAlchemy Connection Test
    try:
        print("\n🧪 Attempting SQLAlchemy Engine connection...")
        # Force asyncpg driver in URL if not present
        sa_url = url
        if "postgresql://" in sa_url and "postgresql+asyncpg://" not in sa_url:
             sa_url = sa_url.replace("postgresql://", "postgresql+asyncpg://")
        elif "postgres://" in sa_url:
             sa_url = sa_url.replace("postgres://", "postgresql+asyncpg://")

        if "sslmode=require" in sa_url:
            sa_url = sa_url.replace("sslmode=require", "ssl=require")

        connect_args = {}
        if "postgresql" in sa_url and "sqlite" not in sa_url:
            connect_args.update({"statement_cache_size": 0})
            print("   - Applied statement_cache_size=0")

        engine = create_async_engine(sa_url, connect_args=connect_args)

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            value = result.scalar()
            print(f"✅ SQLAlchemy Connection Successful! Result: {value}")

        await engine.dispose()

    except Exception as e:
        print(f"❌ SQLAlchemy Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
