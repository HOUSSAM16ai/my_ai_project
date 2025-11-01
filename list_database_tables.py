#!/usr/bin/env python3
"""
📊 عرض جداول قاعدة البيانات / Database Tables Viewer
============================================================
سكريبت بسيط لعرض جميع الجداول الموجودة في قاعدة البيانات
A simple script to display all tables in the database

Author: CogniForge System
Version: 1.0.0
"""

import sys

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("⚠️  تحذير: مكتبة python-dotenv غير مثبتة")
    print("⚠️  Warning: python-dotenv not installed")
    print("    سيتم استخدام متغيرات البيئة المتاحة فقط")
    print("    Using available environment variables only\n")

from sqlalchemy import inspect, text

from app import create_app, db

# الألوان - Colors
G = "\033[92m"  # Green
Y = "\033[93m"  # Yellow
R = "\033[91m"  # Red
B = "\033[94m"  # Blue
C = "\033[96m"  # Cyan
M = "\033[95m"  # Magenta
E = "\033[0m"  # End
BOLD = "\033[1m"


def print_header(text_ar, text_en):
    """طباعة رأس مع خطوط - Print header with lines"""
    width = 80
    print(f"\n{BOLD}{B}{'=' * width}{E}")
    print(f"{BOLD}{C}{text_ar.center(width)}{E}")
    print(f"{BOLD}{C}{text_en.center(width)}{E}")
    print(f"{BOLD}{B}{'=' * width}{E}\n")


def print_section(text):
    """طباعة قسم - Print section"""
    print(f"\n{BOLD}{Y}{'─' * 80}{E}")
    print(f"{BOLD}{Y}{text}{E}")
    print(f"{BOLD}{Y}{'─' * 80}{E}")


def get_table_info(table_name):
    """الحصول على معلومات الجدول - Get table information"""
    try:
        # عد السجلات - Count records
        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = result.scalar()

        # الحصول على الأعمدة - Get columns
        inspector = inspect(db.engine)
        columns = inspector.get_columns(table_name)

        return {
            "count": count,
            "columns": len(columns),
            "column_names": [col["name"] for col in columns],
        }
    except Exception as e:
        return {"count": 0, "columns": 0, "column_names": [], "error": str(e)}


def list_tables():
    """عرض جميع الجداول - List all tables"""

    app = create_app()

    with app.app_context():
        print_header("📊 جداول قاعدة البيانات", "📊 Database Tables")

        try:
            # الاتصال بقاعدة البيانات - Connect to database
            print(f"{Y}🔍 جاري الاتصال بقاعدة البيانات...{E}")
            print(f"{Y}🔍 Connecting to database...{E}\n")

            db.session.execute(text("SELECT 1"))
            print(f"{G}✅ الاتصال ناجح!{E}")
            print(f"{G}✅ Connection successful!{E}\n")

            # الحصول على قائمة الجداول - Get table list
            inspector = inspect(db.engine)
            all_tables = inspector.get_table_names()

            # تصنيف الجداول - Categorize tables
            core_tables = []
            overmind_tables = []
            system_tables = []
            other_tables = []

            # الجداول المتوقعة - Expected tables (PURIFIED v14.0)
            table_categories = {
                # Core Overmind Tables Only (النقي)
                "users": ("core", "👤", "جدول المستخدمين", "User accounts"),
                # Overmind System Tables
                "missions": ("overmind", "🎯", "جدول المهام الرئيسية", "Main missions"),
                "mission_plans": ("overmind", "📋", "جدول خطط المهام", "Mission plans"),
                "tasks": ("overmind", "✅", "جدول المهام الفرعية", "Sub-tasks"),
                "mission_events": ("overmind", "📊", "جدول أحداث المهام", "Mission events"),
                # System Tables
                "alembic_version": ("system", "🔄", "جدول إصدارات الهجرات", "Migration versions"),
            }

            # تصنيف الجداول الموجودة - Categorize existing tables
            for table in all_tables:
                if table in table_categories:
                    category = table_categories[table][0]
                    if category == "core":
                        core_tables.append(table)
                    elif category == "overmind":
                        overmind_tables.append(table)
                    elif category == "system":
                        system_tables.append(table)
                else:
                    other_tables.append(table)

            # عرض الإحصائيات العامة - Display general statistics
            print_section("📈 الإحصائيات العامة / General Statistics")
            print(f"{BOLD}إجمالي عدد الجداول / Total Tables:{E} {C}{len(all_tables)}{E}")
            print(f"  • {G}الجداول الأساسية / Core Tables:{E} {len(core_tables)}")
            print(f"  • {B}جداول Overmind / Overmind Tables:{E} {len(overmind_tables)}")
            print(f"  • {Y}جداول النظام / System Tables:{E} {len(system_tables)}")
            if other_tables:
                print(f"  • {C}جداول أخرى / Other Tables:{E} {len(other_tables)}")

            # عرض الجداول الأساسية - Display core tables
            if core_tables:
                print_section(f"👤 الجداول الأساسية / Core Tables ({len(core_tables)})")
                for table in sorted(core_tables):
                    icon, _, desc_ar, desc_en = table_categories.get(
                        table, ("", "📄", table, table)
                    )[1:]
                    info = get_table_info(table)
                    if "error" in info:
                        print(f"{R}❌ {icon} {table:<25}{E} ({desc_ar})")
                        print(f"   {R}خطأ: {info['error']}{E}")
                    else:
                        print(f"{G}✅ {icon} {table:<25}{E}")
                        print(f"   {C}📝 الوصف / Description:{E} {desc_ar} / {desc_en}")
                        print(f"   {C}🔢 عدد السجلات / Records:{E} {info['count']}")
                        print(f"   {C}📋 عدد الأعمدة / Columns:{E} {info['columns']}")
                        print()

            # عرض جداول Overmind - Display Overmind tables
            if overmind_tables:
                print_section(f"🎯 جداول Overmind / Overmind Tables ({len(overmind_tables)})")
                for table in sorted(overmind_tables):
                    icon, _, desc_ar, desc_en = table_categories.get(
                        table, ("", "📄", table, table)
                    )[1:]
                    info = get_table_info(table)
                    if "error" in info:
                        print(f"{R}❌ {icon} {table:<25}{E} ({desc_ar})")
                        print(f"   {R}خطأ: {info['error']}{E}")
                    else:
                        print(f"{G}✅ {icon} {table:<25}{E}")
                        print(f"   {C}📝 الوصف / Description:{E} {desc_ar} / {desc_en}")
                        print(f"   {C}🔢 عدد السجلات / Records:{E} {info['count']}")
                        print(f"   {C}📋 عدد الأعمدة / Columns:{E} {info['columns']}")
                        print()

            # عرض جداول النظام - Display system tables
            if system_tables:
                print_section(f"🔧 جداول النظام / System Tables ({len(system_tables)})")
                for table in sorted(system_tables):
                    icon, _, desc_ar, desc_en = table_categories.get(
                        table, ("", "📄", table, table)
                    )[1:]
                    info = get_table_info(table)
                    if "error" in info:
                        print(f"{R}❌ {icon} {table:<25}{E} ({desc_ar})")
                    else:
                        print(f"{G}✅ {icon} {table:<25}{E}")
                        print(f"   {C}📝 الوصف / Description:{E} {desc_ar} / {desc_en}")
                        print(f"   {C}📋 عدد الأعمدة / Columns:{E} {info['columns']}")
                        print()

            # عرض الجداول الأخرى - Display other tables
            if other_tables:
                print_section(f"📋 جداول أخرى / Other Tables ({len(other_tables)})")
                for table in sorted(other_tables):
                    info = get_table_info(table)
                    if "error" in info:
                        print(f"{R}❌ 📄 {table:<25}{E}")
                        print(f"   {R}خطأ: {info['error']}{E}")
                    else:
                        print(f"{C}• {table:<25}{E}")
                        print(f"   {C}🔢 عدد السجلات / Records:{E} {info['count']}")
                        print(f"   {C}📋 عدد الأعمدة / Columns:{E} {info['columns']}")
                        print()

            # التحقق من الجداول المفقودة - Check for missing tables
            expected_tables = [t for t in table_categories if table_categories[t][0] != "system"]
            missing_tables = [t for t in expected_tables if t not in all_tables]

            if missing_tables:
                print_section("⚠️ جداول مفقودة / Missing Tables")
                print(f"{Y}الجداول التالية متوقعة لكنها غير موجودة:{E}")
                print(f"{Y}The following tables are expected but not found:{E}\n")
                for table in sorted(missing_tables):
                    icon, _, desc_ar, desc_en = table_categories.get(
                        table, ("", "📄", table, table)
                    )[1:]
                    print(f"{R}❌ {icon} {table:<25}{E} ({desc_ar} / {desc_en})")
                print(f"\n{Y}💡 لإنشاء الجداول المفقودة، قم بتشغيل:{E}")
                print(f"{Y}💡 To create missing tables, run:{E}")
                print(f"   {B}flask db upgrade{E}\n")
            else:
                print_section("✅ التحقق من الجداول / Table Verification")
                print(f"{G}✅ جميع الجداول المتوقعة موجودة!{E}")
                print(f"{G}✅ All expected tables are present!{E}\n")

            # ملخص نهائي - Final summary
            print_header("✨ ملخص", "✨ Summary")
            print(f"{BOLD}📊 إجمالي الجداول / Total Tables:{E} {C}{len(all_tables)}{E}")
            print(
                f"{BOLD}✅ الجداول الموجودة / Present Tables:{E} {G}{len(all_tables) - len(missing_tables)}/{len(expected_tables) + len(system_tables)}{E}"
            )
            if missing_tables:
                print(f"{BOLD}❌ الجداول المفقودة / Missing Tables:{E} {R}{len(missing_tables)}{E}")
            print()

            return True

        except Exception as e:
            print(f"\n{R}❌ حدث خطأ / Error occurred:{E}")
            print(f"{R}{str(e)}{E}\n")
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    try:
        print(f"\n{BOLD}{C}{'=' * 80}{E}")
        print(f"{BOLD}{C}{'📊 عرض جداول قاعدة البيانات / Database Tables Viewer'.center(80)}{E}")
        print(f"{BOLD}{C}{'=' * 80}{E}\n")

        success = list_tables()

        if success:
            print(f"{G}✅ تم بنجاح! / Completed successfully!{E}\n")
            sys.exit(0)
        else:
            print(f"{R}❌ فشلت العملية / Operation failed{E}\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Y}👋 تم الإلغاء / Cancelled{E}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{R}❌ خطأ غير متوقع / Unexpected error:{E}")
        print(f"{R}{str(e)}{E}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)
