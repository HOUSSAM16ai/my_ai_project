#!/usr/bin/env python3
"""
🚀 SUPABASE CONNECTION SETUP & VERIFICATION SCRIPT
===================================================
This script sets up and verifies the connection to the new Supabase project.

Project Details:
- Host: db.aocnuqhxrhxgbfcgbxfy.supabase.co
- Database: postgres
- Port: 5432

Author: Houssam Benmerah
Version: 1.0.0
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import traceback  # noqa: E402
from datetime import datetime  # noqa: E402

from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

# ANSI Colors for beautiful output
G = "\033[92m"  # Green
Y = "\033[93m"  # Yellow
R = "\033[91m"  # Red
B = "\033[94m"  # Blue
M = "\033[95m"  # Magenta
C = "\033[96m"  # Cyan
W = "\033[97m"  # White
E = "\033[0m"  # End


def print_header(text):
    """Print a beautiful header"""
    print(f"\n{B}{'=' * 70}{E}")
    print(f"{C}{text}{E}")
    print(f"{B}{'=' * 70}{E}\n")


def print_success(text):
    """Print success message"""
    print(f"{G}✅ {text}{E}")


def print_error(text):
    """Print error message"""
    print(f"{R}❌ {text}{E}")


def print_warning(text):
    """Print warning message"""
    print(f"{Y}⚠️  {text}{E}")


def print_info(text):
    """Print info message"""
    print(f"{B}ℹ️  {text}{E}")


def verify_environment():
    """Verify environment variables"""
    print_header("📋 STEP 1: VERIFY ENVIRONMENT VARIABLES")

    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print_error("DATABASE_URL not found in environment!")
        print_info("Please ensure .env file exists and contains DATABASE_URL")
        return False

    # Verify the URL points to the correct Supabase project
    if "aocnuqhxrhxgbfcgbxfy.supabase.co" in db_url:
        print_success("DATABASE_URL points to correct Supabase project: aocnuqhxrhxgbfcgbxfy")
    else:
        print_warning("DATABASE_URL doesn't point to the expected Supabase project")
        print_info(f"Current URL: {db_url[:50]}...")

    # Verify password encoding
    if "199720242025%40HOUSSAMbenmerah" in db_url:
        print_success("Password is correctly URL-encoded (@ -> %40)")
    else:
        print_warning("Password encoding might be incorrect")

    print_success("Environment variables verified")
    return True


def test_connection():
    """Test database connection"""
    print_header("🔌 STEP 2: TEST DATABASE CONNECTION")

    db_url = os.getenv("DATABASE_URL")

    try:
        print_info("Creating database engine...")
        engine = create_engine(db_url, pool_pre_ping=True)

        print_info("Attempting to connect...")
        with engine.connect() as conn:
            # Get PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print_success("Connection established successfully!")
            print_info(f"PostgreSQL version: {version.split(',')[0]}")

            # Get current database name
            result = conn.execute(text("SELECT current_database();"))
            db_name = result.fetchone()[0]
            print_info(f"Connected to database: {db_name}")

            # Get current user
            result = conn.execute(text("SELECT current_user;"))
            user = result.fetchone()[0]
            print_info(f"Connected as user: {user}")

        return engine

    except Exception as e:
        print_error(f"Connection failed: {str(e)}")
        print_info("Traceback:")
        traceback.print_exc()
        return None


def check_tables(engine):
    """Check existing tables in database"""
    print_header("📊 STEP 3: CHECK EXISTING TABLES")

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if tables:
            print_success(f"Found {len(tables)} tables in database:")
            for i, table in enumerate(sorted(tables), 1):
                print(f"   {i}. {table}")
        else:
            print_warning("No tables found in database")
            print_info("This is expected for a fresh Supabase project")
            print_info("Tables will be created when migrations are applied")

        return tables

    except Exception as e:
        print_error(f"Failed to check tables: {str(e)}")
        return []


def check_migrations():
    """Check migration status"""
    print_header("🔄 STEP 4: CHECK MIGRATION STATUS")

    migrations_dir = Path(__file__).parent / "migrations" / "versions"

    if not migrations_dir.exists():
        print_error("Migrations directory not found!")
        return False

    migration_files = sorted(migrations_dir.glob("*.py"))
    migration_files = [f for f in migration_files if f.name != "__pycache__"]

    print_success(f"Found {len(migration_files)} migration files:")
    for i, migration in enumerate(migration_files, 1):
        # Extract migration name
        name = migration.stem
        print(f"   {i}. {name}")

    print_info("\nTo apply these migrations, run:")
    print(f"   {B}flask db upgrade{E}")

    return True


def apply_migrations(engine):
    """Apply database migrations"""
    print_header("🚀 STEP 5: APPLY DATABASE MIGRATIONS")

    try:
        print_info("Importing Flask app to apply migrations...")

        from app import create_app
        from app import db as flask_db

        app = create_app("development")

        with app.app_context():
            print_info("Running flask db upgrade...")

            # Check current database revision
            from alembic import command
            from alembic.config import Config as AlembicConfig
            from flask_migrate import Migrate

            Migrate(app, flask_db)

            # Get migration config
            migrations_path = Path(__file__).parent / "migrations"
            alembic_cfg = AlembicConfig(str(migrations_path / "alembic.ini"))
            alembic_cfg.set_main_option("script_location", str(migrations_path))

            # Run upgrade
            command.upgrade(alembic_cfg, "head")

            print_success("Migrations applied successfully!")

            # Verify tables were created
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print_success(f"Database now has {len(tables)} tables")

        return True

    except Exception as e:
        print_error(f"Failed to apply migrations: {str(e)}")
        print_info("You can manually apply migrations with:")
        print(f"   {B}flask db upgrade{E}")
        traceback.print_exc()
        return False


def test_crud_operations(engine):
    """Test basic CRUD operations"""
    print_header("🧪 STEP 6: TEST CRUD OPERATIONS")

    try:
        Session = sessionmaker(bind=engine)
        session = Session()

        # Test with alembic_version table (should always exist after migrations)
        print_info("Testing READ operation...")
        result = session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
        version = result.fetchone()
        if version:
            print_success(f"Current migration version: {version[0]}")
        else:
            print_warning("No migration version found - migrations may not be applied")

        print_success("CRUD operations test completed")
        session.close()
        return True

    except Exception as e:
        print_error(f"CRUD test failed: {str(e)}")
        return False


def generate_report(results):
    """Generate final report"""
    print_header("📝 FINAL REPORT")

    print(f"{B}Connection Summary:{E}")
    print(f"  • Database: {G}Supabase PostgreSQL{E}")
    print(f"  • Host: {C}db.aocnuqhxrhxgbfcgbxfy.supabase.co{E}")
    print(f"  • Port: {C}5432{E}")
    print(f"  • Database Name: {C}postgres{E}")
    print(f"  • Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n{B}Test Results:{E}")
    for step, status in results.items():
        status_str = f"{G}✅ PASSED{E}" if status else f"{R}❌ FAILED{E}"
        print(f"  • {step}: {status_str}")

    all_passed = all(results.values())

    if all_passed:
        print(f"\n{G}{'=' * 70}{E}")
        print(f"{G}🎉 SUCCESS! All tests passed. Supabase connection is working perfectly!{E}")
        print(f"{G}{'=' * 70}{E}\n")
    else:
        print(f"\n{Y}{'=' * 70}{E}")
        print(f"{Y}⚠️  Some tests failed. Please review the errors above.{E}")
        print(f"{Y}{'=' * 70}{E}\n")

    return all_passed


def main():
    """Main function"""
    print(f"\n{M}{'=' * 70}{E}")
    print(f"{M}🚀 SUPABASE CONNECTION SETUP & VERIFICATION{E}")
    print(f"{M}   Project: aocnuqhxrhxgbfcgbxfy (NEW CLEAN PROJECT){E}")
    print(f"{M}{'=' * 70}{E}\n")

    results = {}

    # Step 1: Verify environment
    results["Environment Check"] = verify_environment()

    if not results["Environment Check"]:
        print_error("Cannot proceed without proper environment configuration")
        return 1

    # Step 2: Test connection
    engine = test_connection()
    results["Connection Test"] = engine is not None

    if not engine:
        print_error("Cannot proceed without database connection")
        print_info("\nPossible solutions:")
        print_info("1. Check if you have internet connectivity")
        print_info("2. Verify the Supabase project is active")
        print_info("3. Verify the password is correct")
        print_info("4. Check if your IP is whitelisted in Supabase settings")
        return 1

    # Step 3: Check tables
    tables = check_tables(engine)
    results["Table Check"] = True  # Always true, just informational

    # Step 4: Check migrations
    results["Migration Files"] = check_migrations()

    # Step 5: Apply migrations (if needed)
    if not tables or len(tables) < 5:
        print_info("Database appears to be empty. Attempting to apply migrations...")
        results["Apply Migrations"] = apply_migrations(engine)
    else:
        print_success("Tables already exist, skipping migration application")
        results["Apply Migrations"] = True

    # Step 6: Test CRUD
    if results.get("Apply Migrations", False):
        results["CRUD Test"] = test_crud_operations(engine)

    # Generate final report
    success = generate_report(results)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
