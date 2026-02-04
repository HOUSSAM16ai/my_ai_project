#!/usr/bin/env python3
"""
🛠️ سكربت إصلاح وتشخيص خطأ linked_mission_id

يقوم بـ:
1. التحقق من وجود العمود في قاعدة البيانات
2. إضافة العمود إذا لم يكن موجوداً
3. إنشاء الفهرس للأداء الأفضل

الاستخدام:
    python scripts/fix_linked_mission_id_check.py
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def check_and_fix():
    """Check if linked_mission_id column exists and add it if missing."""
    from sqlalchemy import create_engine, inspect, text

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in environment")
        print("   Please set DATABASE_URL in your .env file")
        return False

    # Handle async URLs
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check if table exists
            inspector = inspect(engine)
            if "admin_conversations" not in inspector.get_table_names():
                print("❌ Table 'admin_conversations' does not exist")
                print("   Run: alembic upgrade head")
                return False

            # Check if column exists
            columns = [col["name"] for col in inspector.get_columns("admin_conversations")]

            if "linked_mission_id" in columns:
                print("✅ Column 'linked_mission_id' already exists!")
                return True

            print("⚠️ Column 'linked_mission_id' is missing")
            print("🔧 Adding column...")

            # Add the column
            conn.execute(
                text(
                    """
                ALTER TABLE admin_conversations
                ADD COLUMN IF NOT EXISTS linked_mission_id INTEGER
            """
                )
            )

            # Create index
            conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS ix_admin_conversations_linked_mission_id
                ON admin_conversations(linked_mission_id)
            """
                )
            )

            conn.commit()

            print("✅ Column 'linked_mission_id' added successfully!")
            print("✅ Index created successfully!")
            return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("💡 Alternative: Run this SQL in Supabase SQL Editor:")
        print()
        print("   ALTER TABLE admin_conversations")
        print("   ADD COLUMN IF NOT EXISTS linked_mission_id INTEGER;")
        print()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Checking admin_conversations.linked_mission_id column")
    print("=" * 60)
    print()

    success = check_and_fix()

    print()
    print("=" * 60)
    if success:
        print("✅ Done! The error should be fixed now.")
    else:
        print("⚠️ Manual intervention required. See instructions above.")
    print("=" * 60)
