#!/usr/bin/env python3
"""
🚀 QUICK MIGRATION SCRIPT - Apply All Migrations to Supabase
==============================================================
This script applies all pending migrations to the Supabase database.

Usage:
    python3 apply_migrations.py

Requirements:
    - Internet connection
    - Valid DATABASE_URL in .env file
    - Flask and dependencies installed

Author: Houssam Benmerah
"""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI Colors
G = "\033[92m"  # Green
Y = "\033[93m"  # Yellow
R = "\033[91m"  # Red
B = "\033[94m"  # Blue
C = "\033[96m"  # Cyan
E = "\033[0m"  # End


def main():
    print(f"\n{C}{'=' * 70}{E}")
    print(f"{C}🚀 APPLYING MIGRATIONS TO SUPABASE{E}")
    print(f"{C}{'=' * 70}{E}\n")

    # Check DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print(f"{R}❌ DATABASE_URL not found in .env file{E}")
        return 1

    if "aocnuqhxrhxgbfcgbxfy" in db_url:
        print(f"{G}✅ DATABASE_URL points to Supabase project: aocnuqhxrhxgbfcgbxfy{E}")
    else:
        print(f"{Y}⚠️  DATABASE_URL doesn't point to expected Supabase project{E}")

    print(f"\n{B}📋 Migration files to apply:{E}")

    migrations_dir = Path(__file__).parent / "migrations" / "versions"
    migration_files = sorted(migrations_dir.glob("*.py"))
    migration_files = [f for f in migration_files if not f.name.startswith("__")]

    for i, migration in enumerate(migration_files, 1):
        print(f"   {i}. {migration.stem}")

    print(f"\n{B}🔄 Running: flask db upgrade{E}\n")

    # Run flask db upgrade with FLASK_APP in environment
    env = os.environ.copy()
    env["FLASK_APP"] = "app.py"
    result = subprocess.run(["flask", "db", "upgrade"], env=env, capture_output=False)

    if result.returncode == 0:
        print(f"\n{G}{'=' * 70}{E}")
        print(f"{G}🎉 SUCCESS! All migrations applied successfully!{E}")
        print(f"{G}{'=' * 70}{E}\n")

        # Show tables
        print(f"{B}📊 Verifying tables in database...{E}\n")
        os.system("python3 check_migrations_status.py")

        # Optionally sync to Supabase format
        print(f"\n{B}🔄 Syncing migrations to Supabase format...{E}")
        print(f"{Y}💡 This fixes the Dashboard migration history display{E}\n")
        sync_result = os.system("python3 fix_supabase_migration_schema.py")

        if sync_result == 0:
            print(f"\n{G}✅ Supabase migration schema is up to date!{E}")
        else:
            print(f"\n{Y}⚠️  Migration sync had issues, but your migrations are applied{E}")
            print(f"{Y}   You can run 'python3 fix_supabase_migration_schema.py' manually later{E}")

        return 0
    else:
        print(f"\n{R}{'=' * 70}{E}")
        print(f"{R}❌ Migration failed! Please check the errors above.{E}")
        print(f"{R}{'=' * 70}{E}\n")

        print(f"{Y}💡 Troubleshooting tips:{E}")
        print("   1. Check internet connection")
        print("   2. Verify DATABASE_URL is correct")
        print("   3. Make sure Supabase project is active")
        print("   4. Check if your IP is whitelisted in Supabase")

        return 1


if __name__ == "__main__":
    sys.exit(main())
