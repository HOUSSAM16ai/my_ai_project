import argparse
import asyncio

from app.core.engine_factory import create_unified_async_engine


async def debug_connection(database_url):
    print(f"Debugging connection to: {database_url.split('@')[-1]}")

    try:
        # 1. Create Engine
        engine = create_unified_async_engine(database_url)

        # 2. Inspect Configuration
        is_postgres = "postgresql" in database_url

        if is_postgres:
             print("Mode: PostgreSQL (Async)")
        else:
             print("Mode: SQLite/Other")

        # 3. Attempt Connection
        print("Attempting connection...")
        async with engine.connect() as conn:
            print("✓ Connection successful!")

            # 4. Run simple query
            # Use text() for raw sql
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            print("✓ Query 'SELECT 1' successful!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", nargs="?", help="Database URL")
    args = parser.parse_args()

    url = args.url or "sqlite+aiosqlite:///:memory:"
    asyncio.run(debug_connection(url))
