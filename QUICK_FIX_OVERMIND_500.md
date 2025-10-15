# ⚡ إصلاح سريع: خطأ 500 في Overmind CLI
# Quick Fix: Overmind CLI 500 Error

## 🎯 المشكلة / Problem

```
❌ Server error (500). Please check your connection and authentication.
```

---

## ✅ الحل السريع (30 ثانية) / Quick Solution (30 seconds)

### الخطوة 1: إنشاء ملف .env
### Step 1: Create .env file

```bash
cp .env.example .env
```

### الخطوة 2: احصل على مفتاح API
### Step 2: Get API Key

🔗 **OpenRouter (الموصى به):** https://openrouter.ai/keys  
🔗 **OpenAI (بديل):** https://platform.openai.com/api-keys

### الخطوة 3: أضف المفتاح إلى .env
### Step 3: Add Key to .env

```bash
# فتح الملف / Open file
nano .env

# إضافة المفتاح / Add key
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

# حفظ / Save: Ctrl+O, Enter
# خروج / Exit: Ctrl+X
```

### الخطوة 4: إعادة التشغيل
### Step 4: Restart

```bash
docker-compose restart web
# أو / OR
flask run
```

### الخطوة 5: اختبر!
### Step 5: Test!

```bash
flask mindgate ask "Hello, are you working now?"
```

---

## 🔍 ما زالت المشكلة موجودة؟ / Still Having Issues?

### التحقق من الإعدادات / Check Configuration
```bash
python3 check_api_config.py
```

### عرض السجلات / View Logs
```bash
docker-compose logs web | tail -50
```

### التشخيص الشامل / Full Diagnosis
```bash
python3 auto_diagnose_and_fix.py --auto-fix
```

---

## 📚 دليل كامل / Full Guide

للحصول على دليل شامل مع جميع التفاصيل:  
For comprehensive guide with all details:

📖 [OVERMIND_500_ERROR_SUPERHUMAN_FIX.md](OVERMIND_500_ERROR_SUPERHUMAN_FIX.md)

---

## ✨ ما تم إصلاحه / What Was Fixed

✅ رسائل خطأ ثنائية اللغة واضحة  
✅ Clear bilingual error messages

✅ تصنيف ذكي لأنواع الأخطاء  
✅ Smart classification of error types

✅ حلول عملية خطوة بخطوة  
✅ Practical step-by-step solutions

✅ سجلات محسّنة للمطورين  
✅ Enhanced logging for developers

---

**Built by Houssam Benmerah** 🚀
