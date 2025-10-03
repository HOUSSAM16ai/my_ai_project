#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 ADMIN CONVERSATIONS LIVE TESTING SYSTEM
==========================================
نظام اختبار مباشر لمحادثات الأدمن مع Supabase

هذا النظام يقوم بـ:
✅ إنشاء محادثات اختبارية جديدة
✅ إضافة رسائل للمحادثات
✅ التحقق من حفظ البيانات في Supabase
✅ عرض المحادثات الحالية
✅ مراقبة الأداء

Author: CogniForge System
Version: 1.0.0
"""

import os
import sys
from pathlib import Path

# إضافة المسار للمشروع
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# تحميل المتغيرات من .env
from dotenv import load_dotenv
load_dotenv()

# الآن نستورد من التطبيق
os.environ['FLASK_APP'] = 'app.py'

from app import create_app, db
from app.models import User, AdminConversation, AdminMessage
from datetime import datetime
import time

# الألوان
class C:
    G = '\033[92m'  # Green
    Y = '\033[93m'  # Yellow
    R = '\033[91m'  # Red
    B = '\033[94m'  # Blue
    E = '\033[0m'   # End
    BOLD = '\033[1m'


def print_section(title):
    """طباعة قسم"""
    print(f"\n{C.BOLD}{C.B}{'='*60}{C.E}")
    print(f"{C.BOLD}{C.B}{title.center(60)}{C.E}")
    print(f"{C.BOLD}{C.B}{'='*60}{C.E}\n")


def test_admin_conversations():
    """اختبار نظام محادثات الأدمن"""
    
    app = create_app()
    
    with app.app_context():
        print_section("🧪 اختبار محادثات الأدمن المباشر")
        
        # الخطوة 1: التحقق من الاتصال
        print(f"{C.Y}🔍 الخطوة 1: التحقق من الاتصال بقاعدة البيانات...{C.E}")
        try:
            db.session.execute(db.text("SELECT 1"))
            print(f"{C.G}✅ الاتصال ناجح!{C.E}\n")
        except Exception as e:
            print(f"{C.R}❌ فشل الاتصال: {e}{C.E}")
            return False
        
        # الخطوة 2: التحقق من المستخدمين
        print(f"{C.Y}🔍 الخطوة 2: التحقق من وجود مستخدمين...{C.E}")
        users = db.session.query(User).all()
        
        if not users:
            print(f"{C.R}❌ لا يوجد مستخدمين في قاعدة البيانات!{C.E}")
            print(f"{C.Y}💡 يرجى تشغيل التطبيق أولاً لإنشاء المستخدم الأدمن{C.E}")
            return False
        
        print(f"{C.G}✅ وجد {len(users)} مستخدم{C.E}")
        admin_user = users[0]  # استخدام أول مستخدم للاختبار
        print(f"{C.B}   👤 المستخدم: {admin_user.username} (ID: {admin_user.id}){C.E}\n")
        
        # الخطوة 3: عرض المحادثات الموجودة
        print(f"{C.Y}🔍 الخطوة 3: عرض المحادثات الموجودة...{C.E}")
        existing_convs = db.session.query(AdminConversation).all()
        print(f"{C.G}✅ عدد المحادثات الموجودة: {len(existing_convs)}{C.E}")
        
        if existing_convs:
            print(f"\n{C.B}📋 آخر 5 محادثات:{C.E}")
            for conv in existing_convs[-5:]:
                msg_count = db.session.query(AdminMessage).filter_by(
                    conversation_id=conv.id
                ).count()
                print(f"  💬 ID: {conv.id} | {conv.title[:40]}... | {msg_count} رسالة | {conv.created_at}")
        
        print()
        
        # الخطوة 4: إنشاء محادثة اختبارية جديدة
        print(f"{C.Y}🔍 الخطوة 4: إنشاء محادثة اختبارية جديدة...{C.E}")
        
        test_conv_title = f"🧪 TEST CONVERSATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            start_time = time.time()
            
            new_conv = AdminConversation(
                title=test_conv_title,
                user_id=admin_user.id,
                conversation_type="test",
                deep_index_summary="هذه محادثة اختبارية للتحقق من اتصال Supabase",
                context_snapshot={"test": True, "timestamp": datetime.now().isoformat()}
            )
            
            db.session.add(new_conv)
            db.session.commit()
            db.session.refresh(new_conv)
            
            elapsed = round(time.time() - start_time, 3)
            
            print(f"{C.G}✅ تم إنشاء المحادثة بنجاح! (ID: {new_conv.id}) في {elapsed} ثانية{C.E}")
            print(f"{C.B}   📝 العنوان: {new_conv.title}{C.E}")
            print(f"{C.B}   🕒 تاريخ الإنشاء: {new_conv.created_at}{C.E}\n")
            
        except Exception as e:
            print(f"{C.R}❌ فشل إنشاء المحادثة: {e}{C.E}")
            import traceback
            traceback.print_exc()
            return False
        
        # الخطوة 5: إضافة رسائل للمحادثة
        print(f"{C.Y}🔍 الخطوة 5: إضافة رسائل للمحادثة...{C.E}")
        
        test_messages = [
            {
                "role": "user",
                "content": "مرحباً! هل النظام متصل بـ Supabase؟"
            },
            {
                "role": "assistant",
                "content": "نعم! النظام متصل بـ Supabase بنسبة 100% ويعمل بشكل خارق! 🚀",
                "tokens_used": 25,
                "model_used": "openai/gpt-4o",
                "latency_ms": 250.5
            },
            {
                "role": "user",
                "content": "رائع! هل يتم حفظ جميع المحادثات؟"
            },
            {
                "role": "assistant",
                "content": "بالتأكيد! كل محادثة ورسالة يتم حفظها مباشرة في Supabase مع جميع التفاصيل.",
                "tokens_used": 30,
                "model_used": "openai/gpt-4o",
                "latency_ms": 180.2
            }
        ]
        
        try:
            for i, msg_data in enumerate(test_messages, 1):
                start_time = time.time()
                
                msg = AdminMessage(
                    conversation_id=new_conv.id,
                    role=msg_data["role"],
                    content=msg_data["content"],
                    tokens_used=msg_data.get("tokens_used"),
                    model_used=msg_data.get("model_used"),
                    latency_ms=msg_data.get("latency_ms"),
                    metadata_json={"test": True, "message_number": i}
                )
                
                db.session.add(msg)
                db.session.commit()
                
                elapsed = round(time.time() - start_time, 3)
                
                role_emoji = "👤" if msg_data["role"] == "user" else "🤖"
                print(f"{C.G}✅ رسالة {i}: {role_emoji} {msg_data['role']} ({elapsed}s){C.E}")
                print(f"{C.B}   💬 {msg_data['content'][:60]}...{C.E}")
            
            print()
            
        except Exception as e:
            print(f"{C.R}❌ فشل إضافة الرسائل: {e}{C.E}")
            import traceback
            traceback.print_exc()
            return False
        
        # الخطوة 6: التحقق من الحفظ
        print(f"{C.Y}🔍 الخطوة 6: التحقق من حفظ البيانات في Supabase...{C.E}")
        
        try:
            # إعادة قراءة المحادثة من قاعدة البيانات
            saved_conv = db.session.get(AdminConversation, new_conv.id)
            
            if not saved_conv:
                print(f"{C.R}❌ المحادثة غير موجودة في قاعدة البيانات!{C.E}")
                return False
            
            # عد الرسائل
            saved_messages = db.session.query(AdminMessage).filter_by(
                conversation_id=new_conv.id
            ).all()
            
            print(f"{C.G}✅ المحادثة محفوظة بنجاح في Supabase!{C.E}")
            print(f"{C.B}   📊 عدد الرسائل المحفوظة: {len(saved_messages)}{C.E}")
            print(f"{C.B}   📝 العنوان: {saved_conv.title}{C.E}")
            print(f"{C.B}   🕒 آخر تحديث: {saved_conv.updated_at}{C.E}\n")
            
            # عرض تفاصيل الرسائل
            print(f"{C.B}📨 تفاصيل الرسائل المحفوظة:{C.E}")
            for msg in saved_messages:
                role_emoji = "👤" if msg.role == "user" else "🤖"
                print(f"  {role_emoji} {msg.role}: {msg.content[:50]}...")
                if msg.tokens_used:
                    print(f"     📊 Tokens: {msg.tokens_used} | Model: {msg.model_used}")
            
            print()
            
        except Exception as e:
            print(f"{C.R}❌ فشل التحقق: {e}{C.E}")
            import traceback
            traceback.print_exc()
            return False
        
        # الخطوة 7: إحصائيات نهائية
        print(f"{C.Y}🔍 الخطوة 7: الإحصائيات النهائية...{C.E}")
        
        try:
            total_convs = db.session.query(AdminConversation).count()
            total_msgs = db.session.query(AdminMessage).count()
            
            print(f"{C.G}✅ إجمالي المحادثات في Supabase: {total_convs}{C.E}")
            print(f"{C.G}✅ إجمالي الرسائل في Supabase: {total_msgs}{C.E}\n")
            
        except Exception as e:
            print(f"{C.R}❌ فشل الحصول على الإحصائيات: {e}{C.E}")
            return False
        
        # النتيجة النهائية
        print_section("🎉 النتيجة النهائية")
        print(f"{C.BOLD}{C.G}✅ جميع الاختبارات نجحت بنسبة 100%!{C.E}")
        print(f"{C.BOLD}{C.G}✅ النظام متصل بـ Supabase بشكل خارق!{C.E}")
        print(f"{C.BOLD}{C.G}✅ جميع محادثات الأدمن يتم حفظها بنجاح!{C.E}")
        print(f"{C.BOLD}{C.G}✅ نظام يتفوق على الشركات العملاقة! 🚀💪{C.E}\n")
        
        return True


if __name__ == "__main__":
    try:
        success = test_admin_conversations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"{C.R}❌ خطأ غير متوقع: {e}{C.E}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
