#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
✅ QUICK CONFIGURATION CHECK
============================
This script verifies that all Supabase configuration is correct.
It doesn't require internet connection - just checks local setup.

Usage:
    python3 verify_config.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

# ANSI Colors
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
R = '\033[91m'  # Red
B = '\033[94m'  # Blue
C = '\033[96m'  # Cyan
E = '\033[0m'   # End

def check_env_file():
    """Check if .env file exists"""
    env_path = Path('.env')
    if env_path.exists():
        print(f"{G}✅ .env file exists{E}")
        return True
    else:
        print(f"{R}❌ .env file NOT found{E}")
        print(f"{Y}   Please create .env file in the project root{E}")
        return False

def check_database_url():
    """Check DATABASE_URL configuration"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        print(f"{R}❌ DATABASE_URL not found in environment{E}")
        return False
    
    print(f"{G}✅ DATABASE_URL is configured{E}")
    
    # Check essential components (Supabase cloud-ready)
    checks = {
        'PostgreSQL protocol': db_url.startswith('postgresql://'),
        'Contains host': '@' in db_url and '/' in db_url.split('@')[-1],
        'Contains port': ':5432/' in db_url or ':6543/' in db_url,  # 5432 or 6543 (pooler)
    }
    
    # Check if Supabase (optional, not required for architectural purity)
    if 'supabase.co' in db_url:
        print(f"{G}   ✓ Supabase cloud database detected{E}")
        checks['Cloud-ready Supabase'] = True
    else:
        print(f"{Y}   ℹ Non-Supabase PostgreSQL (still cloud-ready){E}")
    
    all_good = True
    for check, passed in checks.items():
        if passed:
            print(f"{G}   ✓ {check}{E}")
        else:
            print(f"{R}   ✗ {check}{E}")
            all_good = False
    
    return all_good

def check_admin_config():
    """Check admin configuration"""
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')
    admin_name = os.getenv('ADMIN_NAME')
    
    checks = {
        'ADMIN_EMAIL': admin_email,
        'ADMIN_PASSWORD': admin_password,
        'ADMIN_NAME': admin_name,
    }
    
    all_good = True
    for key, value in checks.items():
        if value:
            print(f"{G}✅ {key} is configured{E}")
        else:
            print(f"{Y}⚠️  {key} not configured{E}")
            all_good = False
    
    return all_good

def check_migrations():
    """Check if migration files exist"""
    migrations_dir = Path('migrations/versions')
    
    if not migrations_dir.exists():
        print(f"{R}❌ Migrations directory not found{E}")
        return False
    
    migration_files = list(migrations_dir.glob('*.py'))
    migration_files = [f for f in migration_files if not f.name.startswith('__')]
    
    if migration_files:
        print(f"{G}✅ Found {len(migration_files)} migration files{E}")
        for migration in sorted(migration_files):
            print(f"   • {migration.stem}")
        return True
    else:
        print(f"{R}❌ No migration files found{E}")
        return False

def check_helper_scripts():
    """Check if helper scripts exist"""
    scripts = [
        'setup_supabase_connection.py',
        'apply_migrations.py',
        'check_migrations_status.py',
        'supabase_verification_system.py',
    ]
    
    all_exist = True
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            print(f"{G}✅ {script}{E}")
        else:
            print(f"{Y}⚠️  {script} not found{E}")
            all_exist = False
    
    return all_exist

def main():
    print(f"\n{C}{'=' * 70}{E}")
    print(f"{C}✅ CLOUD-READY DATABASE CONFIGURATION VERIFICATION{E}")
    print(f"{C}   🔥 PURIFIED OVERMIND ARCHITECTURE - v14.0{E}")
    print(f"{C}{'=' * 70}{E}\n")
    
    results = []
    
    # Check .env file
    print(f"\n{B}1. Checking .env file...{E}")
    results.append(check_env_file())
    
    # Check DATABASE_URL
    print(f"\n{B}2. Checking DATABASE_URL...{E}")
    results.append(check_database_url())
    
    # Check admin config
    print(f"\n{B}3. Checking admin configuration...{E}")
    results.append(check_admin_config())
    
    # Check migrations
    print(f"\n{B}4. Checking migration files...{E}")
    results.append(check_migrations())
    
    # Check helper scripts
    print(f"\n{B}5. Checking helper scripts...{E}")
    results.append(check_helper_scripts())
    
    # Summary
    print(f"\n{C}{'=' * 70}{E}")
    
    if all(results):
        print(f"{G}🎉 SUCCESS! All configuration checks passed!{E}")
        print(f"\n{B}Next steps:{E}")
        print(f"   1. Run: {C}python3 apply_migrations.py{E}")
        print(f"   2. Run: {C}python3 setup_supabase_connection.py{E}")
        print(f"   3. Start app: {C}python3 run.py{E}")
    else:
        print(f"{Y}⚠️  Some configuration items need attention{E}")
        print(f"   Please review the issues above")
    
    print(f"{C}{'=' * 70}{E}\n")
    
    return 0 if all(results) else 1

if __name__ == '__main__':
    exit(main())
