#!/usr/bin/env python3
"""
🔄 MIGRATION STATUS CHECKER (Async/Modern)
==========================================
Checks migration status using the Unified Engine Factory.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text

# FIX: Ensure app modules are importable
sys.path.append(os.getcwd())

from app.core.engine_factory import create_unified_async_engine

# Load environment variables
load_dotenv()

# Colors
G = "\033[92m"
Y = "\033[93m"
R = "\033[91m"
B = "\033[94m"
E = "\033[0m"


def get_database_url():
    url = os.environ.get("DATABASE_URL")
    if not url:
        return "sqlite+aiosqlite:///./test.db"
    return url


async def check_status():
    print(f"\n{B}{'='*60}{E}")
    print(f"{B}🔄 MIGRATION STATUS CHECKER (Async/Unified){E}")
    print(f"{B}{'='*60}{E}\n")

    db_url = get_database_url()

    # Use Unified Factory
    engine = create_unified_async_engine(db_url, echo=False)

    try:
        async with engine.connect() as conn:
            # Check alembic_version
            try:
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                versions = result.scalars().all()
                if versions:
                    print(f"{G}✅ Current Migration Version: {versions[-1]}{E}")
                else:
                    print(f"{Y}⚠️  alembic_version table is empty.{E}")
            except Exception:
                print(f"{Y}⚠️  alembic_version table does not exist.{E}")

            # List Tables
            try:
                result = await conn.execute(
                    text(
                        """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                """
                    )
                )
                tables = result.scalars().all()
                print(f"\n{G}📊 Tables Found ({len(tables)}):{E}")
                for t in tables:
                    print(f"   - {t}")
            except Exception:
                pass

    except Exception as e:
        print(f"{R}❌ Error: {e}{E}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_status())
