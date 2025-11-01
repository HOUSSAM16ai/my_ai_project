#!/usr/bin/env python3
"""
🔥 ARCHITECTURAL PURITY VERIFICATION - ULTIMATE EDITION
========================================================
نظام التحقق الخارق من النقاء المعماري

هذا السكريبت يتحقق من أن المشروع بأكمله لديه:
✅ قاعدة بيانات خارقة قابلة للعمل مع السحابة (Supabase)
✅ بنية Overmind النقية (5 جداول فقط)
✅ لا توجد جداول قديمة (تنقية كاملة)
✅ Docker Compose نقي (لا قاعدة بيانات محلية)
✅ ملفات تحقق محدّثة

Version: 14.0 - Supreme Architectural Purity
Author: CogniForge Team
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI Colors
G = "\033[92m"  # Green
Y = "\033[93m"  # Yellow
R = "\033[91m"  # Red
B = "\033[94m"  # Blue
C = "\033[96m"  # Cyan
M = "\033[95m"  # Magenta
BOLD = "\033[1m"
E = "\033[0m"  # End


def print_header(text):
    """Print a bold header"""
    print(f"\n{BOLD}{M}{'=' * 80}{E}")
    print(f"{BOLD}{M}{text.center(80)}{E}")
    print(f"{BOLD}{M}{'=' * 80}{E}\n")


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
    print(f"{C}ℹ️  {text}{E}")


def check_docker_compose():
    """Check Docker Compose for architectural purity"""
    print_header("🐳 STEP 1: التحقق من Docker Compose")

    docker_file = Path("docker-compose.yml")
    if not docker_file.exists():
        print_error("ملف docker-compose.yml غير موجود!")
        return False

    content = docker_file.read_text()

    issues = []

    # Check for local db service
    if "db:" in content and "image: postgres" in content:
        issues.append("يوجد قسم db محلي - يجب إزالته!")

    # Check for depends_on db
    if "depends_on:" in content and "- db" in content:
        issues.append("يوجد depends_on: [db] - يجب إزالته!")

    # Check for pgdata volume
    if "pgdata:" in content:
        issues.append("يوجد volume pgdata - يجب إزالته!")

    if issues:
        print_error("Docker Compose غير نقي:")
        for issue in issues:
            print(f"   {R}• {issue}{E}")
        print_warning("يجب تحديث docker-compose.yml إلى v6.0 (Supabase Only)")
        return False
    else:
        print_success("Docker Compose نقي 100% - لا قاعدة بيانات محلية ✨")
        print_info("الإصدار: v6.0 (Supabase Only)")
        return True


def check_database_url():
    """Check DATABASE_URL configuration"""
    print_header("🔗 STEP 2: التحقق من DATABASE_URL")

    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print_error("DATABASE_URL غير موجود في ملف .env!")
        print_info("يجب إضافة DATABASE_URL الذي يشير إلى قاعدة بيانات سحابية")
        return False

    print_success("DATABASE_URL موجود")

    # Check if it's PostgreSQL
    if not db_url.startswith("postgresql://"):
        print_error("DATABASE_URL ليس PostgreSQL!")
        return False

    print_success("البروتوكول: PostgreSQL ✓")

    # Check if it's cloud-based (not localhost)
    if "localhost" in db_url or "127.0.0.1" in db_url or "@db:" in db_url:
        print_error("DATABASE_URL يشير إلى قاعدة بيانات محلية!")
        print_warning("يجب أن يشير إلى قاعدة بيانات سحابية (Supabase)")
        return False

    print_success("قاعدة بيانات سحابية ✓")

    # Check if Supabase
    if "supabase.co" in db_url:
        print_success("🎉 قاعدة بيانات Supabase - خارقة!")
    else:
        print_info("قاعدة بيانات PostgreSQL سحابية أخرى")

    return True


def check_models_purity():
    """Check models.py for architectural purity"""
    print_header("📊 STEP 3: التحقق من نقاء Models")

    models_file = Path("app/models.py")
    if not models_file.exists():
        print_error("ملف app/models.py غير موجود!")
        return False

    content = models_file.read_text()

    # Expected tables (Pure Overmind v14.0)
    expected_tables = [
        ("users", "class User"),
        ("missions", "class Mission"),
        ("mission_plans", "class MissionPlan"),
        ("tasks", "class Task"),
        ("mission_events", "class MissionEvent"),
    ]

    # Tables that should NOT exist (purified)
    purified_tables = [
        "class Subject",
        "class Lesson",
        "class Exercise",
        "class Submission",
        "class AdminConversation",
        "class AdminMessage",
    ]

    print_info("التحقق من الجداول المتوقعة (5 جداول):")
    all_good = True
    for table_name, class_name in expected_tables:
        if class_name in content:
            print_success(f"{table_name} ✓")
        else:
            print_error(f"{table_name} غير موجود!")
            all_good = False

    print_info("\nالتحقق من عدم وجود الجداول القديمة:")
    impurities = []
    for old_class in purified_tables:
        if old_class in content:
            impurities.append(old_class)
            print_error(f"{old_class} لا يجب أن يكون موجوداً!")
        else:
            print_success(f"{old_class} تم إزالته ✨")

    if impurities:
        print_error(f"\nشوائب معمارية: {len(impurities)} جدول قديم موجود!")
        return False

    if all_good:
        print_success("\n🔥 Models نقي 100% - بنية Overmind النقية!")
        return True

    return False


def check_verification_scripts():
    """Check that verification scripts are updated"""
    print_header("🔍 STEP 4: التحقق من سكريبتات التحقق")

    scripts_to_check = [
        ("verify_config.py", "Cloud-ready"),
        ("supabase_verification_system.py", "Purified v14.0"),
        ("check_migrations_status.py", "v14.0"),
    ]

    all_good = True
    for script, _marker in scripts_to_check:
        script_path = Path(script)
        if not script_path.exists():
            print_warning(f"{script} غير موجود")
            all_good = False
            continue

        content = script_path.read_text()

        # Check if updated (no old tables)

        # Check expected tables list
        if "expected_tables = [" in content or "expected_tables = [" in content.lower():
            # Find the expected_tables section
            if "subjects" in content and "expected_tables" in content:
                print_error(f"{script}: لا يزال يحتوي على جداول قديمة!")
                all_good = False
            else:
                print_success(f"{script}: محدّث ✓")
        else:
            print_info(f"{script}: لا يحتوي على expected_tables")

    if all_good:
        print_success("\n✅ جميع سكريبتات التحقق محدّثة!")

    return all_good


def check_migrations():
    """Check migration files"""
    print_header("🔄 STEP 5: التحقق من الهجرات")

    migrations_dir = Path("migrations/versions")
    if not migrations_dir.exists():
        print_error("مجلد migrations/versions غير موجود!")
        return False

    migration_files = list(migrations_dir.glob("*.py"))
    migration_files = [f for f in migration_files if not f.name.startswith("__")]

    print_info(f"عدد ملفات الهجرة: {len(migration_files)}")

    # Check for purification migration
    purify_migration = None
    for mig in migration_files:
        if "purify" in mig.stem.lower() or "20250103" in mig.stem:
            purify_migration = mig.stem
            break

    if purify_migration:
        print_success(f"🔥 هجرة التنقية موجودة: {purify_migration}")
    else:
        print_warning("هجرة التنقية غير موجودة - قد تحتاج إلى إنشائها")

    # List all migrations
    print_info("\nالهجرات الموجودة:")
    for mig in sorted(migration_files):
        print(f"   • {mig.stem}")

    return True


def generate_final_report(results):
    """Generate final architectural purity report"""
    print_header("🎯 التقرير النهائي - النقاء المعماري")

    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r)
    success_rate = (passed_checks / total_checks) * 100

    print(f"{BOLD}نسبة النقاء المعماري: {success_rate:.1f}%{E}")
    print(f"الاختبارات الناجحة: {passed_checks}/{total_checks}\n")

    # Detailed results
    for check_name, passed in results.items():
        status = f"{G}✅ PASS{E}" if passed else f"{R}❌ FAIL{E}"
        print(f"{status} - {check_name}")

    print()

    if success_rate == 100:
        print(f"{BOLD}{G}{'🎉' * 40}{E}")
        print(f"{BOLD}{G}النقاء المعماري الخارق - 100% نجاح!{E}")
        print(f"{BOLD}{G}{'🎉' * 40}{E}\n")

        print(f"{G}✨ قاعدة البيانات خارقة جاهزة للسحابة بنسبة 100%!{E}")
        print(f"{G}✨ بنية Overmind النقية - 5 جداول فقط!{E}")
        print(f"{G}✨ Docker Compose نقي - لا قاعدة بيانات محلية!{E}")
        print(f"{G}✨ جميع الجداول القديمة تم إزالتها!{E}")
        print(f"{G}✨ سكريبتات التحقق محدّثة بالكامل!{E}\n")

        print(f"{C}🔥 هذا هو 'النقاء المعماري' الحقيقي! 🔥{E}\n")

    elif success_rate >= 80:
        print(f"{Y}⚠️  النقاء المعماري جيد لكن يحتاج بعض التحسينات ({success_rate:.1f}%){E}\n")
    else:
        print(f"{R}❌ توجد مشاكل في النقاء المعماري ({success_rate:.1f}%){E}\n")
        print(f"{Y}يرجى مراجعة المشاكل أعلاه وإصلاحها{E}\n")

    # Recommendations
    if success_rate < 100:
        print_header("💡 التوصيات")

        if not results.get("docker_compose"):
            print(f"{Y}• تحديث docker-compose.yml إلى v6.0 (Supabase Only){E}")

        if not results.get("database_url"):
            print(f"{Y}• تحديث DATABASE_URL في .env ليشير إلى قاعدة بيانات سحابية{E}")

        if not results.get("models"):
            print(f"{Y}• تحديث app/models.py لإزالة الجداول القديمة (v14.0){E}")

        if not results.get("verification_scripts"):
            print(f"{Y}• تحديث سكريبتات التحقق لتطابق v14.0{E}")

        print()

    return success_rate == 100


def main():
    """Main verification flow"""
    print(f"\n{BOLD}{C}{'=' * 80}{E}")
    print(f"{BOLD}{C}🔥 نظام التحقق الخارق من النقاء المعماري - v14.0{E}")
    print(f"{BOLD}{C}SUPREME ARCHITECTURAL PURITY VERIFICATION SYSTEM{E}")
    print(f"{BOLD}{C}{'=' * 80}{E}\n")

    print(f"{M}هذا النظام يتحقق من أن المشروع بأكمله لديه:{E}")
    print(f"{M}✅ قاعدة بيانات خارقة قابلة للعمل مع السحابة (Supabase){E}")
    print(f"{M}✅ بنية Overmind النقية (5 جداول فقط){E}")
    print(f"{M}✅ لا توجد جداول قديمة (تنقية كاملة){E}")
    print(f"{M}✅ Docker Compose نقي (لا قاعدة بيانات محلية){E}\n")

    results = {}

    # Run all checks
    results["docker_compose"] = check_docker_compose()
    results["database_url"] = check_database_url()
    results["models"] = check_models_purity()
    results["verification_scripts"] = check_verification_scripts()
    results["migrations"] = check_migrations()

    # Generate final report
    success = generate_final_report(results)

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
