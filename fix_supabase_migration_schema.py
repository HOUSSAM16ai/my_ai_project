#!/usr/bin/env python3
"""
🚀 FIX SUPABASE MIGRATION SCHEMA - The Ultimate Solution (Async)
================================================================
This script creates the Supabase migration schema and table that the
Supabase Dashboard expects, while maintaining compatibility with Alembic.
Adapted to work with PgBouncer transaction mode (using Unified Factory).
"""

import asyncio
import os
import sys
import traceback

from dotenv import load_dotenv
from sqlalchemy import text

# FIX: Ensure app modules are importable
sys.path.append(os.getcwd())

from app.core.engine_factory import create_unified_async_engine  # noqa: E402

# Load environment variables
load_dotenv()

# ANSI Colors
G = "\033[92m"
Y = "\033[93m"
R = "\033[91m"
B = "\033[94m"
C = "\033[96m"
W = "\033[97m"
E = "\033[0m"


def print_header(text):
    print(f"\n{B}{'=' * 70}{E}")
    print(f"{C}{text}{E}")
    print(f"{B}{'=' * 70}{E}\n")


def print_success(text):
    print(f"{G}✅ {text}{E}")


def print_error(text):
    print(f"{R}❌ {text}{E}")


def print_info(text):
    print(f"{B}ℹ️  {text}{E}")


def get_async_db_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    return url


async def main():
    print_header("🚀 SUPABASE MIGRATION SCHEMA FIX (ASYNC/UNIFIED)")

    db_url = get_async_db_url()
    if not db_url:
        print_error("DATABASE_URL not found!")
        return 1

    try:
        # Unified Factory
        engine = create_unified_async_engine(db_url, echo=False)

        async with engine.connect() as conn:
            # No nested transaction with asyncpg in the same way, but we use .begin()
            async with conn.begin():
                print_info("Creating/Checking supabase_migrations schema...")

                # Create Schema
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS supabase_migrations"))

                # Create Table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS supabase_migrations.schema_migrations (
                        version VARCHAR(255) PRIMARY KEY NOT NULL,
                        statements TEXT[],
                        name VARCHAR(255),
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """
                    )
                )

                # Sync Alembic
                print_info("Syncing Alembic history...")
                try:
                    result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                    alembic_versions = result.scalars().all()

                    result = await conn.execute(
                        text("SELECT version FROM supabase_migrations.schema_migrations")
                    )
                    synced_versions = result.scalars().all()

                    to_sync = set(alembic_versions) - set(synced_versions)

                    if to_sync:
                        print_info(f"Syncing {len(to_sync)} migrations...")
                        for v in to_sync:
                            await conn.execute(
                                text(
                                    """
                                INSERT INTO supabase_migrations.schema_migrations (version, name, statements)
                                VALUES (:v, :n, :s)
                            """
                                ),
                                {"v": v, "n": f"Migration {v}", "s": ["-- Synced from Alembic"]},
                            )
                    else:
                        print_success("All migrations already synced.")
                except Exception as e:
                    print_info(f"Skipping Alembic sync: {e}")

        await engine.dispose()
        print_success("Done!")

    except Exception as e:
        print_error(f"Error: {e}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print_error(f"Unhandled exception: {e}")
        sys.exit(1)
