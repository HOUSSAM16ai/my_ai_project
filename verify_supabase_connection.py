#!/usr/bin/env python3
"""
🔍 Supabase Connection Verification Script
==========================================

This script verifies the connection to Supabase database (local or remote).
It tests:
1. Database connectivity
2. SQLAlchemy session
3. Basic query execution
4. Available tables

Usage:
    python verify_supabase_connection.py
"""

import sys
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError, OperationalError

# Load environment variables
load_dotenv()

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

def replace_docker_hostname(url):
    """Replace Docker hostname 'db' with 'localhost' for external access"""
    if url and 'db:5432' in url:
        return url.replace('db:5432', 'localhost:5432')
    return url

def main():
    print_header("🗄️ Supabase Database Connection Verification")
    
    # Step 1: Check environment variables
    print_info("Step 1: Checking environment variables...")
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print_error("DATABASE_URL not found in environment variables")
        print_warning("Please ensure .env file exists with DATABASE_URL configured")
        return False
    
    # If running outside Docker, replace 'db' with 'localhost'
    database_url = replace_docker_hostname(database_url)
    if database_url != os.environ.get('DATABASE_URL'):
        print_info("Running outside Docker - using localhost instead of 'db' hostname")
    
    # Mask password in URL for display
    display_url = database_url
    if '@' in database_url:
        parts = database_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            if len(user_pass) >= 3:
                display_url = f"{user_pass[0]}:{user_pass[1]}:****@{parts[1]}"
    
    print_success(f"DATABASE_URL found: {display_url}")
    
    # Step 2: Import Flask app and database
    print_info("\nStep 2: Importing Flask application...")
    try:
        # Temporarily override DATABASE_URL for this script if needed
        os.environ['DATABASE_URL'] = replace_docker_hostname(os.environ.get('DATABASE_URL', ''))
        
        from app import create_app, db
        print_success("Flask app and database modules imported successfully")
    except ImportError as e:
        print_error(f"Failed to import Flask app: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error during import: {e}")
        return False
    
    # Step 3: Create app context
    print_info("\nStep 3: Creating application context...")
    try:
        app = create_app()
        print_success("Application created successfully")
    except (RuntimeError, ValueError) as e:
        print_error(f"Failed to create application: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error during app creation: {e}")
        return False
    
    # Step 4: Test database connection
    print_info("\nStep 4: Testing database connection...")
    try:
        with app.app_context():
            # Test basic connectivity
            result = db.session.execute(db.text("SELECT 1"))
            result.close()
            print_success("Database connection successful!")
            
            # Get database version
            result = db.session.execute(db.text("SELECT version()"))
            version = result.scalar()
            result.close()
            print_success(f"PostgreSQL Version: {version.split(',')[0]}")
            
            # Get current database name
            result = db.session.execute(db.text("SELECT current_database()"))
            db_name = result.scalar()
            result.close()
            print_success(f"Connected to database: {db_name}")
            
    except OperationalError as e:
        print_error(f"Database connection failed: {e}")
        print_warning("Make sure the database container is running:")
        print_warning("  docker-compose up -d db")
        return False
    except SQLAlchemyError as e:
        print_error(f"Database error: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error during database connection: {e}")
        return False
    
    # Step 5: List available tables
    print_info("\nStep 5: Checking available tables...")
    try:
        with app.app_context():
            # Query for user tables (excluding system tables)
            result = db.session.execute(db.text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            result.close()
            
            if tables:
                print_success(f"Found {len(tables)} tables in database:")
                for table in tables:
                    print(f"  📋 {table}")
            else:
                print_warning("No tables found in database")
                print_info("You may need to run migrations:")
                print_info("  flask db upgrade")
                
    except SQLAlchemyError as e:
        print_error(f"Failed to list tables: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error while listing tables: {e}")
        return False
    
    # Step 6: Test database service
    print_info("\nStep 6: Testing database service...")
    try:
        from app.services import database_service
        
        if database_service:
            with app.app_context():
                stats = database_service.get_database_stats()
                print_success(f"Database service working!")
                print_success(f"Total records across all tables: {stats.get('total_records', 0)}")
        else:
            print_warning("Database service not available")
            
    except ImportError as e:
        print_warning(f"Database service not available: {e}")
    except AttributeError as e:
        print_warning(f"Database service method not found: {e}")
    except Exception as e:
        print_warning(f"Database service test failed: {e}")
    
    # Final summary
    print_header("✅ Connection Verification Complete!")
    print_success("Supabase database is accessible and ready to use")
    print_info("\nNext steps:")
    print("  1. Access admin panel: http://localhost:5000/admin/database")
    print("  2. Login with admin credentials from .env file")
    print("  3. Start managing your database!")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\n\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
