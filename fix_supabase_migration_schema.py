#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 FIX SUPABASE MIGRATION SCHEMA - The Ultimate Solution
=========================================================
This script creates the Supabase migration schema and table that the
Supabase Dashboard expects, while maintaining compatibility with Alembic.

Problem:
    Supabase Dashboard shows error:
    "ERROR: 42P01: relation 'supabase_migrations.schema_migrations' does not exist"

Solution:
    - Creates supabase_migrations schema
    - Creates schema_migrations table with correct structure
    - Syncs Alembic migration history to Supabase format
    - Maintains both systems in harmony

Usage:
    python3 fix_supabase_migration_schema.py

Author: Houssam Benmerah
Version: 1.0.0 - The Superhuman Solution
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import traceback

# ANSI Colors for beautiful output
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
R = '\033[91m'  # Red
B = '\033[94m'  # Blue
M = '\033[95m'  # Magenta
C = '\033[96m'  # Cyan
W = '\033[97m'  # White
E = '\033[0m'   # End

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

def create_supabase_migration_schema(engine):
    """Create the supabase_migrations schema and schema_migrations table"""
    print_header("🔧 CREATING SUPABASE MIGRATION SCHEMA")
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()
            
            try:
                # Check if schema exists
                print_info("Checking if supabase_migrations schema exists...")
                result = conn.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'supabase_migrations'
                """))
                schema_exists = result.fetchone() is not None
                
                if schema_exists:
                    print_success("supabase_migrations schema already exists")
                else:
                    print_info("Creating supabase_migrations schema...")
                    conn.execute(text("CREATE SCHEMA supabase_migrations"))
                    print_success("Created supabase_migrations schema")
                
                # Check if table exists
                print_info("Checking if schema_migrations table exists...")
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'supabase_migrations' 
                    AND table_name = 'schema_migrations'
                """))
                table_exists = result.fetchone() is not None
                
                if table_exists:
                    print_success("schema_migrations table already exists")
                else:
                    print_info("Creating schema_migrations table...")
                    # Create table with Supabase-compatible structure
                    conn.execute(text("""
                        CREATE TABLE supabase_migrations.schema_migrations (
                            version VARCHAR(255) PRIMARY KEY NOT NULL,
                            statements TEXT[],
                            name VARCHAR(255),
                            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        )
                    """))
                    print_success("Created schema_migrations table")
                
                # Commit the transaction
                trans.commit()
                print_success("Supabase migration schema setup complete!")
                return True
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        print_error(f"Failed to create schema: {str(e)}")
        print_info(traceback.format_exc())
        return False

def sync_alembic_to_supabase(engine):
    """Sync Alembic migration history to Supabase format"""
    print_header("🔄 SYNCING ALEMBIC MIGRATIONS TO SUPABASE")
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Get Alembic migrations
                print_info("Reading Alembic migration history...")
                result = conn.execute(text(
                    "SELECT version_num FROM alembic_version ORDER BY version_num"
                ))
                alembic_versions = [row[0] for row in result.fetchall()]
                
                if not alembic_versions:
                    print_warning("No Alembic migrations found")
                    trans.commit()
                    return True
                
                print_success(f"Found {len(alembic_versions)} Alembic migrations")
                
                # Get existing Supabase migrations
                print_info("Checking existing Supabase migrations...")
                result = conn.execute(text(
                    "SELECT version FROM supabase_migrations.schema_migrations ORDER BY version"
                ))
                supabase_versions = [row[0] for row in result.fetchall()]
                
                # Find migrations to sync
                to_sync = [v for v in alembic_versions if v not in supabase_versions]
                
                if not to_sync:
                    print_success("All Alembic migrations already synced to Supabase")
                    trans.commit()
                    return True
                
                print_info(f"Syncing {len(to_sync)} migrations to Supabase format...")
                
                # Get migration file names from migrations/versions
                migrations_dir = Path(__file__).parent / 'migrations' / 'versions'
                migration_files = {}
                
                if migrations_dir.exists():
                    for file in migrations_dir.glob('*.py'):
                        if file.name.startswith('__'):
                            continue
                        # Extract version from filename (e.g., "0fe9bd3b1f3c_final_unified_schema_genesis.py")
                        parts = file.stem.split('_', 1)
                        if len(parts) == 2:
                            version, name = parts
                            migration_files[version] = name.replace('_', ' ').title()
                
                # Sync each migration
                for version in to_sync:
                    migration_name = migration_files.get(version, f"Migration {version}")
                    
                    print_info(f"  📌 Syncing: {version} - {migration_name}")
                    
                    conn.execute(text("""
                        INSERT INTO supabase_migrations.schema_migrations 
                        (version, name, statements, applied_at)
                        VALUES (:version, :name, :statements, NOW())
                    """), {
                        'version': version,
                        'name': migration_name,
                        'statements': [f'-- Alembic migration: {version}']
                    })
                
                trans.commit()
                print_success(f"Successfully synced {len(to_sync)} migrations!")
                
                return True
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        print_error(f"Failed to sync migrations: {str(e)}")
        print_info(traceback.format_exc())
        return False

def verify_setup(engine):
    """Verify that everything is set up correctly"""
    print_header("✅ VERIFYING SETUP")
    
    try:
        with engine.connect() as conn:
            # Check schema
            print_info("Checking supabase_migrations schema...")
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'supabase_migrations'
            """))
            if result.fetchone():
                print_success("✓ supabase_migrations schema exists")
            else:
                print_error("✗ supabase_migrations schema NOT found")
                return False
            
            # Check table
            print_info("Checking schema_migrations table...")
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'supabase_migrations' 
                AND table_name = 'schema_migrations'
            """))
            if result.fetchone():
                print_success("✓ schema_migrations table exists")
            else:
                print_error("✗ schema_migrations table NOT found")
                return False
            
            # Check migrations count
            print_info("Counting synced migrations...")
            result = conn.execute(text(
                "SELECT COUNT(*) FROM supabase_migrations.schema_migrations"
            ))
            count = result.scalar()
            print_success(f"✓ {count} migrations in Supabase format")
            
            # Show sample migrations
            if count > 0:
                print_info("Sample migrations:")
                result = conn.execute(text("""
                    SELECT version, name, applied_at 
                    FROM supabase_migrations.schema_migrations 
                    ORDER BY applied_at 
                    LIMIT 5
                """))
                for row in result.fetchall():
                    print(f"  • {row[0]} - {row[1]} (applied: {row[2]})")
            
            return True
            
    except Exception as e:
        print_error(f"Verification failed: {str(e)}")
        print_info(traceback.format_exc())
        return False

def main():
    """Main function"""
    print_header("🚀 SUPABASE MIGRATION SCHEMA FIX - SUPERHUMAN SOLUTION")
    
    print(f"{W}This script will fix the Supabase Dashboard migration history error{E}")
    print(f"{W}by creating the required schema and syncing Alembic migrations.{E}\n")
    
    # Check DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print_error("DATABASE_URL not found in environment!")
        print_info("Please ensure .env file exists and contains DATABASE_URL")
        return 1
    
    print_info(f"Database: {db_url.split('@')[1].split('/')[0] if '@' in db_url else 'Unknown'}")
    
    try:
        # Create engine
        print_info("Creating database connection...")
        engine = create_engine(db_url, pool_pre_ping=True)
        
        # Test connection
        print_info("Testing connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print_success(f"Connected! PostgreSQL version: {version.split(',')[0]}")
        
        # Step 1: Create schema and table
        if not create_supabase_migration_schema(engine):
            print_error("Failed to create schema!")
            return 1
        
        # Step 2: Sync Alembic migrations
        if not sync_alembic_to_supabase(engine):
            print_error("Failed to sync migrations!")
            return 1
        
        # Step 3: Verify setup
        if not verify_setup(engine):
            print_error("Verification failed!")
            return 1
        
        # Success!
        print_header("🎉 SUCCESS!")
        print(f"{G}{'=' * 70}{E}")
        print(f"{G}The Supabase migration schema has been fixed!{E}")
        print(f"{G}{'=' * 70}{E}\n")
        
        print(f"{W}What was done:{E}")
        print(f"  ✅ Created supabase_migrations schema")
        print(f"  ✅ Created schema_migrations table")
        print(f"  ✅ Synced Alembic migrations to Supabase format")
        print(f"  ✅ Verified all setup\n")
        
        print(f"{C}Next steps:{E}")
        print(f"  1. Refresh your Supabase Dashboard")
        print(f"  2. Go to Database → Migrations")
        print(f"  3. You should now see your migration history!")
        print(f"  4. Run this script again after applying new migrations\n")
        
        print(f"{Y}Note:{E} This project uses Alembic for migrations, not Supabase CLI.")
        print(f"{Y}      This script bridges the two systems for Dashboard compatibility.\n")
        
        return 0
        
    except Exception as e:
        print_error(f"Fatal error: {str(e)}")
        print_info(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())
