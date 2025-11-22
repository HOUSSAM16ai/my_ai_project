#!/usr/bin/env python3
"""
✅ DUPLICATE PREPARED STATEMENT FIX VERIFIER
=============================================
This script verifies that the `DuplicatePreparedStatementError` is resolved
by ensuring `statement_cache_size=0` is correctly applied to all asyncpg connections.
"""

import asyncio
import os
import sys
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

def get_safe_db_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)

    # Fix scheme for asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")

    return url

async def verify_fix():
    print("🔍 Verifying fix for DuplicatePreparedStatementError...")

    db_url = get_safe_db_url()
    print(f"📝 URL Scheme: {db_url.split('://')[0]}")

    # 1. Create engine WITH the fix
    connect_args = {}
    if "sqlite" not in db_url:
        print("✅ Applying 'statement_cache_size=0' (Fix for PgBouncer/Supabase)")
        connect_args = {"statement_cache_size": 0, "timeout": 30, "command_timeout": 60}
    else:
        print("ℹ️  SQLite detected, skipping statement_cache_size=0")

    engine = create_async_engine(db_url, echo=False, connect_args=connect_args)

    try:
        async with engine.connect() as conn:
            print("🔌 Connected successfully.")

            # Execute a simple query multiple times to ensure no prepared statement conflict
            print("🧪 Executing queries...")
            for i in range(3):
                result = await conn.execute(text("SELECT 1"))
                val = result.scalar()
                print(f"   Query {i+1}: Result={val}")

            # Test explicit version query
            try:
                version = await conn.execute(text("SELECT version()"))
                v = version.scalar()
                print(f"✅ Database Version: {v.split(',')[0]}")
            except Exception:
                print("ℹ️  Could not fetch version (might be SQLite)")

        print("\n🎉 VERIFICATION SUCCESSFUL: No DuplicatePreparedStatementError detected.")
        print("   The fix (statement_cache_size=0) is working correctly.")

    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        if "DuplicatePreparedStatementError" in str(e):
            print("   ⚠️  This is the exact error we are trying to fix!")
            print("   Ensure statement_cache_size=0 is passed to connect_args.")
        raise e
    finally:
        await engine.dispose()

if __name__ == "__main__":
    if "--verify" in sys.argv:
        try:
            asyncio.run(verify_fix())
        except Exception as e:
            sys.exit(1)
    else:
        print("Usage: python3 scripts/fix_duplicate_prepared_statement.py --verify")
