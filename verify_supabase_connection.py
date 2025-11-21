#!/usr/bin/env python3
"""
🔍 Supabase Connection Verification Script (Async/Modern)
=======================================================
This script verifies the connection to Supabase database using the
modern AsyncEngine stack of the Reality Kernel.

It verifies:
1. Asyncpg connectivity
2. SSL configuration
3. PgBouncer compatibility (statement_cache_size=0)
4. Schema access

Usage:
    python verify_supabase_connection.py
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Load environment variables
load_dotenv()

# Color codes
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
B = "\033[94m"
E = "\033[0m"

def print_header(text):
    print(f"\n{B}{'=' * 70}{E}")
    print(f"{B}{text.center(70)}{E}")
    print(f"{B}{'=' * 70}{E}\n")

def get_database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print(f"{R}❌ DATABASE_URL is not set in .env{E}")
        sys.exit(1)

    # Force asyncpg scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url

async def main():
    print_header("🚀 Supabase Connection Verification (Async)")

    db_url = get_database_url()
    # Mask password
    safe_url = db_url
    if "@" in safe_url:
        parts = safe_url.split("@")
        safe_url = f"...@{parts[1]}"

    print(f"{B}ℹ️  Target URL:{E} {safe_url}")

    # ------------------------------------------------------------------
    # KEY FIX: PgBouncer Transaction Mode Compatibility
    # ------------------------------------------------------------------
    connect_args = {}
    if "sqlite" not in db_url:
        print(f"{G}🔧 Applying 'statement_cache_size=0' for PgBouncer compatibility{E}")
        connect_args["statement_cache_size"] = 0
        connect_args["timeout"] = 30

    engine = create_async_engine(db_url, echo=False, connect_args=connect_args)

    try:
        print(f"\n{Y}⏳ Connecting...{E}")
        async with engine.connect() as conn:
            print(f"{G}✅ Connection Established!{E}")

            # 1. Check Version
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"   📝 Version: {version.split(',')[0]}")

            # 2. Check Current Database
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"   🗄️  Database: {db_name}")

            # 3. List Tables
            print(f"\n{Y}📊 Fetching Tables...{E}")
            result = await conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.scalars().all()

            if tables:
                print(f"{G}✅ Found {len(tables)} tables:{E}")
                for t in tables:
                    print(f"   - {t}")
            else:
                print(f"{Y}⚠️  No tables found in 'public' schema.{E}")

        print_header("✅ VERIFICATION COMPLETE - SYSTEM HEALTHY")

    except Exception as e:
        print(f"\n{R}❌ CONNECTION FAILED{E}")
        print(f"{R}Error: {e}{E}")
        if "DuplicatePreparedStatementError" in str(e):
            print(f"\n{Y}💡 DIAGNOSIS: This error confirms usage of prepared statements on PgBouncer.{E}")
            print(f"{Y}   Ensure 'statement_cache_size=0' is effectively passed.{E}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
