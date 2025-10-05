#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app, db
from sqlalchemy import inspect, text

# الألوان
G = '\033[92m'  # Green
Y = '\033[93m'  # Yellow
R = '\033[91m'  # Red
B = '\033[94m'  # Blue
E = '\033[0m'   # End
BOLD = '\033[1m'


def print_header(text):
    print(f"\n{BOLD}{B}{'='*70}{E}")
    print(f"{BOLD}{B}{text.center(70)}{E}")
    print(f"{BOLD}{B}{'='*70}{E}\n")


def check_migrations():
    """فحص حالة الهجرات"""
    
    app = create_app()
    
    with app.app_context():
        print_header("🔄 فحص حالة الهجرات")
        
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
                
                # التحقق من هجرة جداول الأدمن
                admin_migration = 'c670e137ea84'
                if any(admin_migration in v for v in versions):
                    print(f"{G}✅ هجرة جداول الأدمن مطبقة ({admin_migration}){E}")
                else:
                    print(f"{R}❌ هجرة جداول الأدمن غير مطبقة!{E}")
                    print(f"{Y}💡 يجب تطبيق هجرة {admin_migration}{E}")
            else:
                print(f"{R}❌ لا توجد هجرات مطبقة!{E}")
                print(f"{Y}💡 يرجى تشغيل: flask db upgrade{E}")
            
            # فحص الجداول الموجودة
            print(f"\n{Y}📊 فحص الجداول الموجودة...{E}")
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"{G}✅ عدد الجداول: {len(tables)}{E}\n")
            
            expected_tables = [
                'users', 'subjects', 'lessons', 'exercises', 'submissions',
                'missions', 'mission_plans', 'tasks', 'mission_events',
                'admin_conversations', 'admin_messages'
            ]
            
            print(f"{B}🔍 الجداول المتوقعة:{E}")
            for table in expected_tables:
                if table in tables:
                    # عد السجلات
                    try:
                        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        print(f"   {G}✅{E} {table:<25} ({count} سجل)")
                    except:
                        print(f"   {Y}⚠️{E}  {table:<25} (موجود لكن حدث خطأ)")
                else:
                    print(f"   {R}❌{E} {table:<25} (غير موجود!)")
            
            # جداول إضافية
            extra_tables = [t for t in tables if t not in expected_tables and not t.startswith('alembic')]
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
            elif not versions:
                print(f"{R}❌ لا توجد هجرات مطبقة!{E}")
                print(f"{Y}💡 الحل:{E}")
                print(f"   {B}flask db upgrade{E}\n")
            else:
                print(f"{G}✅ كل شيء على ما يرام! جميع الجداول موجودة والهجرات مطبقة{E}\n")
            
            # معلومات إضافية
            print(f"{B}📚 معلومات إضافية:{E}")
            print(f"   • عدد الهجرات: {len(versions)}")
            print(f"   • عدد الجداول: {len(tables)}")
            print(f"   • الجداول المتوقعة: {len(expected_tables)}")
            print(f"   • الجداول الموجودة من المتوقعة: {len([t for t in expected_tables if t in tables])}")
            
            # نسبة النجاح
            success_rate = (len([t for t in expected_tables if t in tables]) / len(expected_tables)) * 100
            print(f"\n{BOLD}نسبة النجاح: {success_rate:.1f}%{E}")
            
            if success_rate == 100:
                print(f"{G}🎉 ممتاز! جميع الجداول موجودة!{E}\n")
            elif success_rate >= 80:
                print(f"{Y}⚠️  بعض الجداول مفقودة{E}\n")
            else:
                print(f"{R}❌ العديد من الجداول مفقودة!{E}\n")
            
        except Exception as e:
            print(f"{R}❌ حدث خطأ: {str(e)}{E}")
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
        print(f"{R}❌ خطأ غير متوقع: {str(e)}{E}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
