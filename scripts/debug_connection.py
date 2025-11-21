import asyncio
import os
import sys
import urllib.parse
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

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

    print(f"📝 Raw DATABASE_URL Scheme: {url.split('://')[0]}")
    print(f"📝 Masked DATABASE_URL: {mask_url(url)}")

    # 1. Asyncpg Raw Connection Test
    try:
        import asyncpg
        print("\n🧪 Attempting RAW asyncpg connection...")
        # Parse params from URL
        parsed = urllib.parse.urlparse(url)

        if '+' in parsed.scheme:
            scheme = parsed.scheme.split('+')[1] # asyncpg
        else:
            scheme = parsed.scheme

        if scheme != 'asyncpg' and scheme != 'postgresql':
             print(f"⚠️ Scheme seems to be {scheme}, expecting asyncpg compatible")

        # We will try to connect using the DSN directly if asyncpg allows,
        # but asyncpg.connect(dsn) is standard.
        # Note: asyncpg expects postgresql:// not postgresql+asyncpg://

        asyncpg_url = url.replace("postgresql+asyncpg://", "postgresql://")

        conn = await asyncpg.connect(asyncpg_url)
        version = await conn.fetchval('SELECT version()')
        print(f"✅ Asyncpg Connection Successful! Version: {version}")
        await conn.close()
    except Exception as e:
        print(f"❌ Asyncpg Connection Failed: {e}")

    # 2. SQLAlchemy Connection Test
    try:
        print("\n🧪 Attempting SQLAlchemy Engine connection...")
        # Force asyncpg driver in URL if not present
        sa_url = url
        if "postgresql://" in sa_url and "postgresql+asyncpg://" not in sa_url:
             sa_url = sa_url.replace("postgresql://", "postgresql+asyncpg://")

        connect_args = {}
        if "postgresql" in sa_url:
            connect_args = {"statement_cache_size": 0}

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
