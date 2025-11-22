#!/usr/bin/env python3
"""
🚀 SUPABASE CONNECTION SETUP & VERIFICATION SCRIPT (ASYNC)
==========================================================
This script sets up and verifies the connection to the new Supabase project
using the Unified Engine Factory.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text

# FIX: Ensure app modules are importable
sys.path.append(os.getcwd())

from app.core.engine_factory import create_unified_async_engine

# Load environment variables
load_dotenv()

# ANSI Colors
G = "\033[92m"
Y = "\033[93m"
R = "\033[91m"
B = "\033[94m"
M = "\033[95m"
C = "\033[96m"
E = "\033[0m"


def print_header(text):
    print(f"\n{B}{'=' * 70}{E}")
    print(f"{C}{text}{E}")
    print(f"{B}{'=' * 70}{E}\n")


def print_success(text):
    print(f"{G}✅ {text}{E}")


def print_error(text):
    print(f"{R}❌ {text}{E}")


def print_warning(text):
    print(f"{Y}⚠️  {text}{E}")


def print_info(text):
    print(f"{B}ℹ️  {text}{E}")

def get_async_db_url():
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    return url

async def verify_environment():
    print_header("📋 STEP 1: VERIFY ENVIRONMENT VARIABLES")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print_error("DATABASE_URL not found!")
        return False

    print_success("Environment variables verified")
    return True

async def test_connection():
    print_header("🔌 STEP 2: TEST DATABASE CONNECTION (ASYNC/UNIFIED)")

    db_url = get_async_db_url()

    try:
        # Unified Factory
        engine = create_unified_async_engine(db_url, echo=False)

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print_success("Connection established successfully!")
            print_info(f"PostgreSQL version: {version.split(',')[0]}")

            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print_info(f"Connected to database: {db_name}")

        return engine
    except Exception as e:
        print_error(f"Connection failed: {e}")
        return None

async def check_tables(engine):
    print_header("📊 STEP 3: CHECK EXISTING TABLES")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.scalars().all()

            if tables:
                print_success(f"Found {len(tables)} tables in database:")
                for i, table in enumerate(tables, 1):
                    print(f"   {i}. {table}")
            else:
                print_warning("No tables found in database")

            return tables
    except Exception as e:
        print_error(f"Failed to check tables: {e}")
        return []

async def main():
    print(f"\n{M}{'=' * 70}{E}")
    print(f"{M}🚀 SUPABASE CONNECTION SETUP & VERIFICATION (ASYNC/UNIFIED){E}")
    print(f"{M}{'=' * 70}{E}\n")

    if not await verify_environment():
        return 1

    engine = await test_connection()
    if not engine:
        return 1

    await check_tables(engine)

    await engine.dispose()
    return 0

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except Exception as e:
        print_error(str(e))
        sys.exit(1)
