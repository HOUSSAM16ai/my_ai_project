#!/usr/bin/env python3
"""
🔄 MIGRATION STATUS CHECKER
===========================
فحص حالة الهجرات بسرعة

هذا السكريبت يعرض:
- الهجرات المطبقة حالياً
- آخر هجرة
- جداول قاعدة البيانات الموجودة
- توصيات للإصلاح

Author: CogniForge System
Version: 1.0.0
"""

import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from sqlalchemy import inspect, text  # noqa: E402

from app import create_app, db  # noqa: E402

# الألوان
G = "\033[92m"  # Green
Y = "\033[93m"  # Yellow
R = "\033[91m"  # Red
B = "\033[94m"  # Blue
E = "\033[0m"  # End
BOLD = "\033[1m"


def print_header(text):
    print(f"\n{BOLD}{B}{'=' * 70}{E}")
    print(f"{BOLD}{B}{text.center(70)}{E}")
    print(f"{BOLD}{B}{'=' * 70}{E}\n")


def check_migrations():
    """فحص حالة الهجرات"""

    app = create_app()

    with app.app_context():
        print_header("🔄 فحص حالة الهجرات - v14.0 Purified")

        try:
            # الاتصال
            print(f"{Y}🔍 الاتصال بقاعدة البيانات...{E}")
            db.session.execute(text("SELECT 1"))
            print(f"{G}✅ الاتصال ناجح!{E}\n")

            # فحص جدول الهجرات
            print(f"{Y}📋 فحص جدول alembic_version...{E}")
            result = db.session.execute(
                text("SELECT version_num FROM alembic_version ORDER BY version_num")
            )
            versions = [row[0] for row in result.fetchall()]

            if versions:
                print(f"{G}✅ عدد الهجرات المطبقة: {len(versions)}{E}\n")

                print(f"{B}📌 جميع الهجرات المطبقة:{E}")
                for i, version in enumerate(versions, 1):
                    print(f"   {i}. {version}")

                print(f"\n{G}✅ آخر هجرة: {versions[-1]}{E}\n")

                # Check for purification migration
                purify_migration = "20250103_purify_db"
                admin_migration = "c670e137ea84"

                if purify_migration in versions:
                    print(f"{G}🔥 هجرة التنقية مطبقة! قاعدة البيانات نقية ومجهزة للسحابة{E}")
                elif any(admin_migration in v for v in versions):
                    print(f"{Y}⚠️  هجرة الأدمن القديمة موجودة - يُنصح بتطبيق هجرة التنقية{E}")
                    print(f"{Y}💡 للتنقية الكاملة: flask db upgrade (لتطبيق {purify_migration}){E}")
            else:
                print(f"{R}❌ لا توجد هجرات مطبقة!{E}")
                print(f"{Y}💡 يرجى تشغيل: flask db upgrade{E}")

            # فحص الجداول الموجودة
            print(f"\n{Y}📊 فحص الجداول الموجودة...{E}")
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            print(f"{G}✅ عدد الجداول: {len(tables)}{E}\n")

            expected_tables = [
                "users",  # User accounts
                "missions",  # Main missions
                "mission_plans",  # Mission execution plans
                "tasks",  # Sub-tasks
                "mission_events",  # Mission event logs
            ]

            # Purified tables (should NOT exist)
            purified_tables = [
                "subjects",
                "lessons",
                "exercises",
                "submissions",
                "admin_conversations",
                "admin_messages",
                "task_dependencies",
            ]

            print(f"{B}🔍 الجداول المتوقعة (Overmind v14.0):{E}")
            for table in expected_tables:
                if table in tables:
                    # عد السجلات
                    try:
                        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        print(f"   {G}✅{E} {table:<25} ({count} سجل)")
                    except Exception:
                        print(f"   {Y}⚠️{E}  {table:<25} (موجود لكن حدث خطأ)")
                else:
                    print(f"   {R}❌{E} {table:<25} (غير موجود!)")

            # Check for purified tables
            print(f"\n{B}🔥 فحص النقاء المعماري:{E}")
            impurities_found = False
            for table in purified_tables:
                if table in tables:
                    print(f"   {R}⚠️  {table:<25} (يجب حذفه!){E}")
                    impurities_found = True
                else:
                    print(f"   {G}✨{E} {table:<25} (تم تنقيته)")

            if not impurities_found:
                print(f"\n{G}🎉 النقاء المعماري 100%! جميع الجداول القديمة محذوفة{E}")

            # جداول إضافية
            all_known = expected_tables + purified_tables + ["alembic_version"]
            extra_tables = [t for t in tables if t not in all_known]
            if extra_tables:
                print(f"\n{B}📋 جداول إضافية:{E}")
                for table in extra_tables:
                    print(f"   • {table}")

            # التوصيات
            print_header("💡 التوصيات")

            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                print(f"{R}❌ توجد جداول مفقودة: {', '.join(missing_tables)}{E}")
                print(f"{Y}💡 الحل: تشغيل الهجرات{E}")
                print(f"   {B}flask db upgrade{E}\n")
            elif impurities_found:
                print(f"{Y}⚠️  توجد جداول قديمة يجب تنقيتها{E}")
                print(f"{Y}💡 الحل: تطبيق هجرة التنقية{E}")
                print(f"   {B}flask db upgrade{E}\n")
            elif not versions:
                print(f"{R}❌ لا توجد هجرات مطبقة!{E}")
                print(f"{Y}💡 الحل:{E}")
                print(f"   {B}flask db upgrade{E}\n")
            else:
                print(f"{G}✅ كل شيء مثالي! قاعدة بيانات نقية جاهزة للسحابة 100%{E}\n")

            # معلومات إضافية
            print(f"{B}📚 معلومات إضافية:{E}")
            print(f"   • عدد الهجرات: {len(versions)}")
            print(f"   • عدد الجداول: {len(tables)}")
            print(f"   • الجداول المتوقعة: {len(expected_tables)}")
            print(
                f"   • الجداول الموجودة من المتوقعة: {len([t for t in expected_tables if t in tables])}"
            )

            # نسبة النجاح
            success_rate = (
                len([t for t in expected_tables if t in tables]) / len(expected_tables)
            ) * 100
            print(f"\n{BOLD}نسبة النجاح: {success_rate:.1f}%{E}")

            if success_rate == 100:
                print(f"{G}🎉 ممتاز! جميع الجداول موجودة!{E}\n")
            elif success_rate >= 80:
                print(f"{Y}⚠️  بعض الجداول مفقودة{E}\n")
            else:
                print(f"{R}❌ العديد من الجداول مفقودة!{E}\n")

        except Exception as e:
            print(f"{R}❌ حدث خطأ: {e!s}{E}")
            import traceback

            traceback.print_exc()
            return False

        return True


if __name__ == "__main__":
    try:
        check_migrations()
    except KeyboardInterrupt:
        print(f"\n{Y}👋 تم الإلغاء{E}")
        sys.exit(1)
    except Exception as e:
        print(f"{R}❌ خطأ غير متوقع: {e!s}{E}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
