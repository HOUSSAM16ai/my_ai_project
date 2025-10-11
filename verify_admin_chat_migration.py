#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 MIGRATION VERIFICATION SCRIPT
=================================
Verifies that the admin_conversations and admin_messages tables exist in the database.

This script checks:
1. Database connection
2. Table existence
3. Table structure (columns)
4. Indexes

Author: CogniForge System
Version: 1.0.0
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from sqlalchemy import inspect, text

# Colors
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
R = '\033[91m'  # Red
B = '\033[94m'  # Blue
M = '\033[95m'  # Magenta
C = '\033[96m'  # Cyan
E = '\033[0m'   # End
BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{B}{BOLD}{'=' * 80}{E}")
    print(f"{B}{BOLD}{text:^80}{E}")
    print(f"{B}{BOLD}{'=' * 80}{E}\n")


def verify_tables():
    """Verify that required tables exist"""
    
    print_header("🔍 DATABASE MIGRATION VERIFICATION")
    
    app = create_app()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            all_tables = inspector.get_table_names()
            
            print(f"{C}📊 Connected to database:{E}")
            database_url = os.getenv('DATABASE_URL', 'Not set')
            if 'supabase' in database_url:
                print(f"  Type: {M}Supabase (PostgreSQL){E}")
            else:
                print(f"  Type: {Y}Local/Other{E}")
            
            # Check for required tables
            required_tables = ['admin_conversations', 'admin_messages']
            
            print(f"\n{C}🔍 Checking required tables...{E}\n")
            
            all_exist = True
            for table in required_tables:
                if table in all_tables:
                    print(f"{G}✅ {table:<30} EXISTS{E}")
                    
                    # Get columns
                    columns = inspector.get_columns(table)
                    print(f"   Columns: {len(columns)}")
                    
                    # Show key columns
                    key_columns = [col['name'] for col in columns[:5]]
                    print(f"   Sample: {', '.join(key_columns)}...")
                    
                    # Get indexes
                    indexes = inspector.get_indexes(table)
                    print(f"   Indexes: {len(indexes)}")
                    
                else:
                    print(f"{R}❌ {table:<30} MISSING{E}")
                    all_exist = False
            
            if not all_exist:
                print(f"\n{R}{BOLD}⚠️  MIGRATION REQUIRED!{E}\n")
                print(f"{Y}The admin chat tables are missing. You need to run migrations:{E}")
                print(f"\n{B}   flask db upgrade{E}\n")
                print(f"{Y}Or specifically apply the admin chat migration:{E}")
                print(f"\n{B}   flask db upgrade 20251011_admin_chat{E}\n")
                return False
            
            # Additional verification - try to query the tables
            print(f"\n{C}🧪 Testing table access...{E}\n")
            
            try:
                result = db.session.execute(text("SELECT COUNT(*) FROM admin_conversations"))
                conv_count = result.scalar()
                print(f"{G}✅ admin_conversations is accessible (rows: {conv_count}){E}")
            except Exception as e:
                print(f"{R}❌ Cannot access admin_conversations: {e}{E}")
                return False
            
            try:
                result = db.session.execute(text("SELECT COUNT(*) FROM admin_messages"))
                msg_count = result.scalar()
                print(f"{G}✅ admin_messages is accessible (rows: {msg_count}){E}")
            except Exception as e:
                print(f"{R}❌ Cannot access admin_messages: {e}{E}")
                return False
            
            # Success!
            print(f"\n{G}{BOLD}{'=' * 80}{E}")
            print(f"{G}{BOLD}{'✅ ALL CHECKS PASSED! DATABASE IS READY!':^80}{E}")
            print(f"{G}{BOLD}{'=' * 80}{E}\n")
            
            print(f"{M}📊 Summary:{E}")
            print(f"  • Tables: ✅ All required tables exist")
            print(f"  • Access: ✅ Can query tables successfully")
            print(f"  • Data: {conv_count} conversations, {msg_count} messages")
            
            if conv_count == 0:
                print(f"\n{Y}💡 Tip: No conversations yet. Use the admin chat feature to create some!{E}")
            
            return True
            
        except Exception as e:
            print(f"\n{R}❌ Verification failed with error:{E}")
            print(f"{R}{str(e)}{E}")
            import traceback
            traceback.print_exc()
            return False


def show_table_structure():
    """Show detailed table structure"""
    
    print_header("📋 DETAILED TABLE STRUCTURE")
    
    app = create_app()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            for table_name in ['admin_conversations', 'admin_messages']:
                print(f"\n{C}{BOLD}Table: {table_name}{E}")
                print(f"{'-' * 80}")
                
                columns = inspector.get_columns(table_name)
                
                print(f"\n{Y}Columns:{E}")
                for col in columns:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f" DEFAULT {col['default']}" if col['default'] else ""
                    print(f"  • {col['name']:<30} {str(col['type']):<20} {nullable}{default}")
                
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    print(f"\n{Y}Indexes:{E}")
                    for idx in indexes:
                        unique = " (UNIQUE)" if idx.get('unique') else ""
                        print(f"  • {idx['name']:<40} {', '.join(idx['column_names'])}{unique}")
                
                foreign_keys = inspector.get_foreign_keys(table_name)
                if foreign_keys:
                    print(f"\n{Y}Foreign Keys:{E}")
                    for fk in foreign_keys:
                        print(f"  • {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
                
        except Exception as e:
            print(f"\n{R}❌ Error showing table structure: {e}{E}")


if __name__ == "__main__":
    print(f"\n{Y}Starting Database Migration Verification...{E}\n")
    
    success = verify_tables()
    
    if success:
        show_table_structure()
        print(f"\n{G}✅ Verification completed successfully!{E}")
        print(f"\n{C}Next step: Test the admin chat persistence with:{E}")
        print(f"{B}   python test_admin_chat_persistence.py{E}\n")
        sys.exit(0)
    else:
        print(f"\n{R}❌ Verification failed!{E}")
        print(f"\n{Y}Please apply migrations first:{E}")
        print(f"{B}   flask db upgrade{E}\n")
        sys.exit(1)
