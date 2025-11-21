#!/usr/bin/env python3
"""
🚀 FIX SUPABASE MIGRATION SCHEMA - The Ultimate Solution
=========================================================
This script creates the Supabase migration schema and table that the
Supabase Dashboard expects, while maintaining compatibility with Alembic.
Adapted to work with PgBouncer transaction mode (using sync engine with explicit args if needed).
"""

import os
import sys
import traceback
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

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

def get_sync_db_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    # Ensure using psycopg2 or default sync driver
    # If it has +asyncpg, remove it
    url = url.replace("+asyncpg", "").replace("+aiosqlite", "")
    return url

def main():
    print_header("🚀 SUPABASE MIGRATION SCHEMA FIX")

    db_url = get_sync_db_url()
    if not db_url:
        print_error("DATABASE_URL not found!")
        return 1

    try:
        # Use standard create_engine (sync)
        # Note: psycopg2 typically works with PgBouncer unless server-side cursors are used.
        # We don't use server-side cursors here.
        engine = create_engine(db_url, pool_pre_ping=True)

        with engine.connect() as conn:
            trans = conn.begin()
            try:
                print_info("Creating/Checking supabase_migrations schema...")

                # Create Schema
                conn.execute(text("CREATE SCHEMA IF NOT EXISTS supabase_migrations"))

                # Create Table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS supabase_migrations.schema_migrations (
                        version VARCHAR(255) PRIMARY KEY NOT NULL,
                        statements TEXT[],
                        name VARCHAR(255),
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))

                # Sync Alembic
                print_info("Syncing Alembic history...")
                alembic_versions = conn.execute(text("SELECT version_num FROM alembic_version")).scalars().all()

                synced_versions = conn.execute(text("SELECT version FROM supabase_migrations.schema_migrations")).scalars().all()

                to_sync = set(alembic_versions) - set(synced_versions)

                if to_sync:
                    print_info(f"Syncing {len(to_sync)} migrations...")
                    for v in to_sync:
                        conn.execute(text("""
                            INSERT INTO supabase_migrations.schema_migrations (version, name, statements)
                            VALUES (:v, :n, :s)
                        """), {"v": v, "n": f"Migration {v}", "s": ["-- Synced from Alembic"]})
                else:
                    print_success("All migrations already synced.")

                trans.commit()
                print_success("Done!")

            except Exception as e:
                trans.rollback()
                raise e

    except Exception as e:
        print_error(f"Error: {e}")
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
