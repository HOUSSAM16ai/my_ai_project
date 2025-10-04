#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# ANSI Colors
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
R = '\033[91m'  # Red
B = '\033[94m'  # Blue
C = '\033[96m'  # Cyan
E = '\033[0m'   # End

def main():
    print(f"\n{C}{'=' * 70}{E}")
    print(f"{C}🚀 APPLYING MIGRATIONS TO SUPABASE{E}")
    print(f"{C}{'=' * 70}{E}\n")
    
    # Check DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print(f"{R}❌ DATABASE_URL not found in .env file{E}")
        return 1
    
    if 'aocnuqhxrhxgbfcgbxfy' in db_url:
        print(f"{G}✅ DATABASE_URL points to Supabase project: aocnuqhxrhxgbfcgbxfy{E}")
    else:
        print(f"{Y}⚠️  DATABASE_URL doesn't point to expected Supabase project{E}")
    
    # Set Flask app
    os.environ['FLASK_APP'] = 'app.py'
    
    print(f"\n{B}📋 Migration files to apply:{E}")
    
    migrations_dir = Path(__file__).parent / 'migrations' / 'versions'
    migration_files = sorted(migrations_dir.glob('*.py'))
    migration_files = [f for f in migration_files if not f.name.startswith('__')]
    
    for i, migration in enumerate(migration_files, 1):
        print(f"   {i}. {migration.stem}")
    
    print(f"\n{B}🔄 Running: flask db upgrade{E}\n")
    
    # Run flask db upgrade
    result = os.system('flask db upgrade')
    
    if result == 0:
        print(f"\n{G}{'=' * 70}{E}")
        print(f"{G}🎉 SUCCESS! All migrations applied successfully!{E}")
        print(f"{G}{'=' * 70}{E}\n")
        
        # Show tables
        print(f"{B}📊 Verifying tables in database...{E}\n")
        os.system('python3 check_migrations_status.py')
        
        return 0
    else:
        print(f"\n{R}{'=' * 70}{E}")
        print(f"{R}❌ Migration failed! Please check the errors above.{E}")
        print(f"{R}{'=' * 70}{E}\n")
        
        print(f"{Y}💡 Troubleshooting tips:{E}")
        print(f"   1. Check internet connection")
        print(f"   2. Verify DATABASE_URL is correct")
        print(f"   3. Make sure Supabase project is active")
        print(f"   4. Check if your IP is whitelisted in Supabase")
        
        return 1

if __name__ == '__main__':
    sys.exit(main())
