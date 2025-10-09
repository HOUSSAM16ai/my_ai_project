#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Supabase Pooler Configuration Validator
==========================================

This script validates that the DATABASE_URL is configured correctly
to use Supabase Connection Pooler.

Usage:
    python3 validate_pooler_config.py
"""

import os
import sys
from urllib.parse import urlparse

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - use environment variables directly
    pass

# ANSI Colors
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
R = '\033[91m'  # Red
B = '\033[94m'  # Blue
C = '\033[96m'  # Cyan
E = '\033[0m'   # End

def print_header(text):
    """Print header"""
    print(f"\n{C}{'=' * 70}{E}")
    print(f"{C}{text}{E}")
    print(f"{C}{'=' * 70}{E}\n")

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

def validate_pooler_config():
    """Validate that DATABASE_URL is configured for pooler"""
    print_header("🔍 VALIDATING POOLER CONFIGURATION")
    
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print_error("DATABASE_URL not found in environment variables")
        print_info("Please create .env file with DATABASE_URL")
        return False
    
    print_success("DATABASE_URL found in environment")
    
    # Parse the URL
    try:
        parsed = urlparse(database_url)
    except Exception as e:
        print_error(f"Failed to parse DATABASE_URL: {e}")
        return False
    
    # Validation checks
    checks = {
        'uses_postgresql_protocol': False,
        'uses_pooler_hostname': False,
        'uses_pooler_port': False,
        'has_ssl_mode': False,
        'password_url_encoded': False,
    }
    
    # Check 1: PostgreSQL protocol
    if parsed.scheme in ['postgresql', 'postgres']:
        checks['uses_postgresql_protocol'] = True
        print_success(f"Protocol: {parsed.scheme}://")
    else:
        print_error(f"Protocol is '{parsed.scheme}' - should be 'postgresql'")
    
    # Check 2: Pooler hostname
    if 'pooler.supabase.com' in parsed.hostname or '':
        checks['uses_pooler_hostname'] = True
        print_success(f"Hostname: {parsed.hostname} (Pooler)")
    elif 'supabase.co' in parsed.hostname or '':
        print_warning(f"Hostname: {parsed.hostname} (Direct connection - not recommended)")
        print_info("Consider switching to pooler: [PROJECT-REF].pooler.supabase.com")
    else:
        print_warning(f"Hostname: {parsed.hostname} (Non-Supabase database)")
    
    # Check 3: Pooler port (6543)
    if parsed.port == 6543:
        checks['uses_pooler_port'] = True
        print_success(f"Port: {parsed.port} (Pooler/pgbouncer)")
    elif parsed.port == 5432:
        print_warning(f"Port: {parsed.port} (Direct connection - may have IPv6 issues)")
        print_info("Consider switching to pooler port: 6543")
    else:
        print_warning(f"Port: {parsed.port} (Non-standard)")
    
    # Check 4: SSL mode
    if 'sslmode=require' in database_url:
        checks['has_ssl_mode'] = True
        print_success("SSL Mode: require (secure)")
    else:
        print_warning("SSL Mode: not specified - add '?sslmode=require' to URL")
    
    # Check 5: Password URL encoding
    if '%40' in database_url or '@' not in parsed.password or '':
        checks['password_url_encoded'] = True
        print_success("Password: properly URL-encoded")
    else:
        print_error("Password: contains unencoded '@' symbol")
        print_info("Replace @ with %40 in password")
    
    # Summary
    print_header("📊 VALIDATION SUMMARY")
    
    all_passed = all(checks.values())
    pooler_recommended = checks['uses_pooler_hostname'] and checks['uses_pooler_port']
    
    if all_passed:
        print_success("All checks passed! ✨")
        if pooler_recommended:
            print_success("Using recommended Pooler connection 🎉")
        return True
    elif pooler_recommended:
        print_warning("Using Pooler connection with minor issues")
        print_info("Please fix the warnings above")
        return True
    else:
        print_warning("Using Direct connection (not recommended for Codespaces/Gitpod)")
        print_info("Consider migrating to Pooler connection")
        print_info("See: POOLER_MIGRATION_GUIDE.md")
        return False

def show_recommendations():
    """Show configuration recommendations"""
    print_header("💡 RECOMMENDATIONS")
    
    database_url = os.getenv('DATABASE_URL', '')
    
    if 'pooler.supabase.com:6543' in database_url and 'sslmode=require' in database_url:
        print_success("Configuration is optimal! No changes needed.")
        return
    
    print_info("For Codespaces/Gitpod, use Pooler connection:")
    print("\nRecommended DATABASE_URL format:")
    print(f"{C}postgresql://postgres:PASSWORD@PROJECT-REF.pooler.supabase.com:6543/postgres?sslmode=require{E}")
    
    print("\nFor the current project (aocnuqhxrhxgbfcgbxfy):")
    print(f"{C}postgresql://postgres:199720242025%40HOUSSAMbenmerah@aocnuqhxrhxgbfcgbxfy.pooler.supabase.com:6543/postgres?sslmode=require{E}")
    
    print("\nBenefits of Pooler:")
    print("  ✅ Resolves IPv6 compatibility issues")
    print("  ✅ More stable in containerized environments")
    print("  ✅ Better performance with concurrent connections")
    print("  ✅ Includes pgbouncer connection pooling layer")

def main():
    """Main validation flow"""
    print_header("🔧 SUPABASE POOLER CONFIGURATION VALIDATOR")
    
    result = validate_pooler_config()
    show_recommendations()
    
    print_header("✅ VALIDATION COMPLETE")
    
    if result:
        print_success("Configuration is valid and ready to use!")
        return 0
    else:
        print_warning("Configuration needs attention")
        print_info("See recommendations above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
