#!/bin/bash
# -*- coding: utf-8 -*-
# 🚀 Quick Start Script for Supabase Verification
# نص سريع لبدء التحقق من Supabase

set -e

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🚀 CogniForge Supabase Verification System - Quick Start  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# التحقق من Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 غير مثبت!${NC}"
    echo -e "${YELLOW}💡 يرجى تثبيت Python 3.8 أو أحدث${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python 3 موجود${NC}"
python3 --version

# التحقق من ملف .env
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  ملف .env غير موجود${NC}"
    echo -e "${BLUE}📝 إنشاء ملف .env من .env.example...${NC}"
    
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ تم إنشاء ملف .env${NC}"
        echo -e "${YELLOW}💡 يرجى تحديث DATABASE_URL في ملف .env${NC}"
        echo ""
        echo -e "${BLUE}مثال:${NC}"
        echo -e "DATABASE_URL=postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:5432/postgres"
        echo ""
        read -p "هل تريد المتابعة؟ (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}👋 تم الإلغاء${NC}"
            exit 0
        fi
    else
        echo -e "${RED}❌ ملف .env.example غير موجود!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ ملف .env موجود${NC}"
fi

# التحقق من المكتبات المطلوبة
echo ""
echo -e "${BLUE}📦 التحقق من المكتبات المطلوبة...${NC}"

if python3 -c "import sqlalchemy" 2>/dev/null; then
    echo -e "${GREEN}✅ SQLAlchemy مثبت${NC}"
else
    echo -e "${YELLOW}⚠️  SQLAlchemy غير مثبت${NC}"
    echo -e "${BLUE}📥 تثبيت المكتبات...${NC}"
    pip install -q sqlalchemy psycopg2-binary python-dotenv
fi

if python3 -c "import dotenv" 2>/dev/null; then
    echo -e "${GREEN}✅ python-dotenv مثبت${NC}"
else
    echo -e "${YELLOW}⚠️  python-dotenv غير مثبت${NC}"
    pip install -q python-dotenv
fi

# القائمة الرئيسية
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              اختر نوع الاختبار الذي تريد تشغيله            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}1)${NC} 🔍 اختبار شامل كامل (موصى به)"
echo -e "   - التحقق من الاتصال"
echo -e "   - فحص جميع الجداول"
echo -e "   - التحقق من الهجرات"
echo -e "   - اختبار عمليات CRUD"
echo -e "   - إنشاء تقرير تفصيلي"
echo ""
echo -e "${GREEN}2)${NC} 💬 اختبار محادثات الأدمن"
echo -e "   - إنشاء محادثة اختبارية"
echo -e "   - إضافة رسائل"
echo -e "   - التحقق من الحفظ في Supabase"
echo ""
echo -e "${GREEN}3)${NC} 📚 عرض الدليل الكامل"
echo ""
echo -e "${GREEN}4)${NC} 🚪 الخروج"
echo ""

read -p "اختر (1-4): " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🚀 تشغيل الاختبار الشامل...${NC}"
        echo ""
        python3 supabase_verification_system.py
        ;;
    2)
        echo ""
        echo -e "${BLUE}💬 تشغيل اختبار محادثات الأدمن...${NC}"
        echo ""
        python3 test_admin_conversations_live.py
        ;;
    3)
        echo ""
        echo -e "${BLUE}📚 فتح الدليل الكامل...${NC}"
        echo ""
        if [ -f SUPABASE_VERIFICATION_GUIDE_AR.md ]; then
            if command -v less &> /dev/null; then
                less SUPABASE_VERIFICATION_GUIDE_AR.md
            else
                cat SUPABASE_VERIFICATION_GUIDE_AR.md
            fi
        else
            echo -e "${RED}❌ ملف الدليل غير موجود!${NC}"
        fi
        ;;
    4)
        echo ""
        echo -e "${YELLOW}👋 وداعاً!${NC}"
        exit 0
        ;;
    *)
        echo ""
        echo -e "${RED}❌ خيار غير صحيح!${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                     اكتمل التشغيل بنجاح                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
