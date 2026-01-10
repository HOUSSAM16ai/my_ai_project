import asyncio
import os
import sys

# Set env before any other imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import contextlib

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Import the module under test
from app.core import db_schema


async def main():
    print("Testing schema validation with SQLite...")

    # Create a fresh engine for testing
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # CRITICAL: Patch the engine in the db_schema module where it was imported
    db_schema.engine = test_engine

    try:
        # 1. Validate Schema (should create tables)
        # Using a timeout to prevent hanging
        async with asyncio.timeout(30):
            await db_schema.validate_schema_on_startup()

        print("Schema validation successful.")

        # 2. Verify tables exist
        async with test_engine.connect() as conn:
            result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables created: {tables}")

            required_tables = ["users", "missions", "tasks", "mission_plans", "audit_log"]
            for t in required_tables:
                if t not in tables:
                    print(f"ERROR: Table {t} missing!")
                    sys.exit(1)

            # 3. Verify Columns (check SQLite type conversion)
            # Check users.is_active is INTEGER (Boolean in SQLite) or BOOLEAN
            result = await conn.execute(text("PRAGMA table_info(users)"))
            columns = {row[1]: row[2] for row in result.fetchall()}
            print(f"Users columns: {columns}")

            if columns["is_active"] not in ["BOOLEAN", "INTEGER", "BOOL"]:
                 print(f"WARNING: is_active type is {columns['is_active']}")

    except TimeoutError:
        print("TIMEOUT: Operation took too long.")
        sys.exit(1)
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await test_engine.dispose()

if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
