#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔄 Apply Database Migrations
============================

This script applies all pending database migrations to ensure the database
schema is up to date.

Usage:
    python3 apply_migrations.py

Features:
- Checks database connectivity
- Displays current migration status
- Applies pending migrations
- Verifies successful application
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Set Flask app for migrations
os.environ['FLASK_APP'] = 'app.py'

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def check_database_connection():
    """Check if database is accessible"""
    print_info("Step 1: Checking database connection...")
    
    try:
        from app import create_app, db
        app = create_app()
        
        with app.app_context():
            # Test basic connectivity
            db.session.execute(text("SELECT 1"))
            print_success("Database connection successful!")
            return True, app
            
    except OperationalError as e:
        print_error(f"Database connection failed: {e}")
        print_warning("Make sure the database is running and accessible")
        return False, None
    except Exception as e:
        print_error(f"Error connecting to database: {e}")
        return False, None


def get_current_migration_status(app):
    """Get current migration status"""
    print_info("\nStep 2: Checking current migration status...")
    
    try:
        from app import db
        
        with app.app_context():
            # Check if alembic_version table exists
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'alembic_version'
                )
            """))
            alembic_exists = result.scalar()
            result.close()
            
            if not alembic_exists:
                print_warning("No migrations have been applied yet")
                return []
            
            # Get applied migrations
            result = db.session.execute(
                text("SELECT version_num FROM alembic_version ORDER BY version_num")
            )
            versions = [row[0] for row in result.fetchall()]
            result.close()
            
            if versions:
                print_success(f"Found {len(versions)} applied migration(s)")
                print_info(f"Current migration: {versions[-1]}")
            else:
                print_warning("No migrations applied yet")
            
            return versions
            
    except Exception as e:
        print_warning(f"Could not check migration status: {e}")
        return []


def apply_migrations():
    """Apply database migrations using Flask-Migrate"""
    print_info("\nStep 3: Applying migrations...")
    
    import subprocess
    
    try:
        # Run flask db upgrade
        result = subprocess.run(
            ['flask', 'db', 'upgrade'],
            env={**os.environ, 'FLASK_APP': 'app.py'},
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print_success("Migrations applied successfully!")
            if result.stdout:
                print(f"\n{Colors.BLUE}Migration output:{Colors.END}")
                print(result.stdout)
            return True
        else:
            print_error("Failed to apply migrations")
            if result.stderr:
                print(f"\n{Colors.RED}Error output:{Colors.END}")
                print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print_error("Migration process timed out (>60s)")
        return False
    except FileNotFoundError:
        print_error("Flask command not found. Make sure Flask is installed.")
        return False
    except Exception as e:
        print_error(f"Error applying migrations: {e}")
        return False


def verify_migrations(app):
    """Verify that migrations were applied correctly"""
    print_info("\nStep 4: Verifying migrations...")
    
    try:
        from app import db
        
        with app.app_context():
            # Get updated migration status
            result = db.session.execute(
                text("SELECT version_num FROM alembic_version ORDER BY version_num")
            )
            versions = [row[0] for row in result.fetchall()]
            result.close()
            
            if versions:
                print_success(f"Total applied migrations: {len(versions)}")
                print_success(f"Latest migration: {versions[-1]}")
                
                # Check for expected tables
                result = db.session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """))
                tables = [row[0] for row in result.fetchall()]
                result.close()
                
                expected_tables = [
                    'users', 'subjects', 'lessons', 'exercises', 'submissions',
                    'missions', 'mission_plans', 'tasks', 'mission_events',
                    'admin_conversations', 'admin_messages'
                ]
                
                found_tables = [t for t in expected_tables if t in tables]
                
                if len(found_tables) == len(expected_tables):
                    print_success(f"All expected tables exist ({len(found_tables)}/{len(expected_tables)})")
                else:
                    print_warning(f"Some tables missing ({len(found_tables)}/{len(expected_tables)})")
                    missing = [t for t in expected_tables if t not in tables]
                    if missing:
                        print_warning(f"Missing tables: {', '.join(missing)}")
                
                return True
            else:
                print_warning("No migrations found after application")
                return False
                
    except Exception as e:
        print_error(f"Error verifying migrations: {e}")
        return False


def main():
    """Main execution function"""
    print_header("🔄 Apply Database Migrations")
    
    # Step 1: Check database connection
    connected, app = check_database_connection()
    if not connected:
        print_header("❌ Migration Failed")
        print_error("Cannot proceed without database connection")
        return False
    
    # Step 2: Get current migration status
    current_versions = get_current_migration_status(app)
    
    # Step 3: Apply migrations
    if not apply_migrations():
        print_header("❌ Migration Failed")
        return False
    
    # Step 4: Verify migrations
    if not verify_migrations(app):
        print_header("⚠️  Migration Completed with Warnings")
        return True  # Still return True as migrations were applied
    
    # Success!
    print_header("✅ Migrations Applied Successfully")
    print_success("Database schema is up to date!")
    print_info("\nNext steps:")
    print("  1. Verify connection: python3 setup_supabase_connection.py")
    print("  2. Start application: python3 run.py")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n\nMigration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
