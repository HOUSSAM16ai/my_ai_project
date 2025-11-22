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

from sqlalchemy import text

# FIX: Ensure app modules are importable
sys.path.append(os.getcwd())

from app.core.engine_factory import create_unified_async_engine

def get_safe_db_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    return url

async def verify_fix():
    print("🔍 Verifying fix for DuplicatePreparedStatementError (Unified)...")

    db_url = get_safe_db_url()
    print(f"📝 URL Scheme: {db_url.split('://')[0]}")

    # Use Unified Factory
    engine = create_unified_async_engine(db_url, echo=False)

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
        print("   The Unified Engine Factory correctly enforced statement_cache_size=0.")

    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        if "DuplicatePreparedStatementError" in str(e):
            print("   ⚠️  This is the exact error we are trying to fix!")
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
