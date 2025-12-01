#!/usr/bin/env python3
import asyncio
import os
from sqlalchemy import text, inspect
from app.core.engine_factory import create_unified_async_engine
from app.models import AdminMessage, MessageRole

async def heal_message_roles():
    """
    Checks for messages with uppercase 'USER' roles and updates them to 'user'.
    This is a one-time data fix script.
    """
    print("Initiating Database Healing Protocol for Enum Case Mismatch...")
    engine = create_unified_async_engine()

    async with engine.begin() as conn:
        # Check if table exists (simple check)
        # In async engine, we can run sync inspection
        def check_table(connection):
            insp = inspect(connection)
            return insp.has_table("admin_messages")

        has_table = await conn.run_sync(check_table)
        if not has_table:
            print("Table admin_messages does not exist. Skipping.")
            return

        # Count affected rows
        # Postgres is case sensitive for string comparison
        result = await conn.execute(text("SELECT count(*) FROM admin_messages WHERE role = 'USER'"))
        count = result.scalar()
        print(f"Found {count} messages with legacy 'USER' role.")

        if count > 0:
            print(f"Healing {count} records...")
            await conn.execute(text("UPDATE admin_messages SET role = 'user' WHERE role = 'USER'"))
            # Also handle other potential mismatches if needed, but USER is the reported one.
            # We could do lower(role) but safe to be explicit.
            print("Healing complete. All records normalized.")
        else:
            print("No corrupted records found. System is healthy.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Ensure DATABASE_URL is set
    if "DATABASE_URL" not in os.environ:
        print("DATABASE_URL not set. Skipping.")
        exit(1)

    asyncio.run(heal_message_roles())
