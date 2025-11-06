# دليل مرئي: كيفية استخدام Docker Compose بشكل صحيح
# Visual Guide: How to Use Docker Compose Correctly

## ❌ الطريقة الخاطئة / WRONG WAY

```bash
# خطأ: كلمة run في السطر الخطأ والنص مختلط
# Error: The word 'run' is on the wrong line and text is mixed up
# THIS IS THE ACTUAL ERROR THE USER MADE - DO NOT COPY THIS!
docker-compose run --rm \
-e ADMIN_EMAIL="benmerahhoussam16@gmail.com" \
-e ADMIdocker-compose run --rm web flask db upgradeN_PASSWORD="1111" \
web flask users init-admin
```

❌ **النتيجة / Result:**
```
no such service: run
```

**لماذا حدث الخطأ؟ / Why did this error occur?**
- النص مختلط ومكتوب بشكل غير صحيح
- The text is mixed up and written incorrectly
- `run` appears in the wrong line
- Environment variables are malformed

---

## ✅ الطريقة الصحيحة / CORRECT WAY

### الخيار 1️⃣: سطر واحد (الأسهل)
### Option 1️⃣: One Line (Easiest)

```bash
docker-compose run --rm web flask users create-admin
```

أو / or

```bash
docker compose run --rm web flask users create-admin
```

---

### الخيار 2️⃣: عدة أسطر مع متغيرات البيئة
### Option 2️⃣: Multiple Lines with Environment Variables

```bash
docker-compose run --rm \
  -e ADMIN_EMAIL="benmerahhoussam16@gmail.com" \
  -e ADMIN_PASSWORD="1111" \
  -e ADMIN_NAME="Houssam Benmerah" \
  web flask users create-admin
```

**ملاحظة مهمة / Important Note:**
- ✅ استخدم `\` في نهاية السطر للمتابعة في السطر التالي
- ✅ Use `\` at the end of the line to continue on the next line
- ✅ كل سطر بعد `\` يجب أن يبدأ بمسافات (indentation)
- ✅ Each line after `\` should start with spaces (indentation)

---

## 📋 الأوامر الشائعة / Common Commands

### 1. بدء التطبيق / Start Application

```bash
# البناء أولاً / Build first
docker-compose build

# ثم التشغيل / Then run
docker-compose up -d
```

**الاختصار / Shortcut:**
```bash
# كل شيء مرة واحدة / Everything at once
./docker-quick-start.sh
```

---

### 2. ترحيل قاعدة البيانات / Database Migration

```bash
docker-compose run --rm web flask db upgrade
```

أو مع docker compose v2 / or with docker compose v2:
```bash
docker compose run --rm web flask db upgrade
```

---

### 3. إنشاء مستخدم مشرف / Create Admin User

```bash
# الطريقة 1 / Method 1
docker-compose run --rm web flask users create-admin

# الطريقة 2 (نفس الأمر) / Method 2 (same command)
docker-compose run --rm web flask users init-admin
```

**مع تحديد البيانات يدوياً / With manual data specification:**
```bash
docker-compose run --rm \
  -e ADMIN_EMAIL="your-email@example.com" \
  -e ADMIN_PASSWORD="your-password" \
  -e ADMIN_NAME="Your Name" \
  web flask users create-admin
```

---

### 4. عرض السجلات / View Logs

```bash
# كل الخدمات / All services
docker-compose logs -f

# خدمة واحدة فقط / One service only
docker-compose logs -f web
```

---

### 5. حالة الخدمات / Service Status

```bash
docker-compose ps
```

**المخرج المتوقع / Expected output:**
```
NAME                IMAGE              STATUS         PORTS
flask-frontend      my_ai_project_web  Up 2 minutes  0.0.0.0:5000->5000/tcp
fastapi-ai-service  ai_service         Up 2 minutes  0.0.0.0:8001->8000/tcp
```

---

## 🔧 استكشاف الأخطاء / Troubleshooting

### المشكلة: لا تظهر الواجهة على المنفذ 5000
### Problem: Interface not showing on port 5000

```bash
# الخطوة 1: تحقق من حالة الخدمات
# Step 1: Check service status
docker-compose ps

# الخطوة 2: إذا كانت متوقفة، قم بتشغيلها
# Step 2: If stopped, start them
docker-compose up -d

# الخطوة 3: تحقق من السجلات
# Step 3: Check logs
docker-compose logs web

# الخطوة 4: افتح المتصفح
# Step 4: Open browser
# http://localhost:5000
```

---

### المشكلة: خطأ في الاتصال بقاعدة البيانات
### Problem: Database connection error

```bash
# 1. تحقق من .env
# 1. Check .env
cat .env | grep DATABASE_URL

# 2. تأكد من أن DATABASE_URL صحيح
# 2. Make sure DATABASE_URL is correct
# يجب أن يكون مثل / Should look like:
# DATABASE_URL=postgresql://postgres.xxx:pass@xxx.pooler.supabase.com:6543/postgres?sslmode=require

# 3. جرب الترحيلات مرة أخرى
# 3. Try migrations again
docker-compose run --rm web flask db upgrade
```

---

## 🎯 نصائح مهمة / Important Tips

### 1. استخدم المسافات بشكل صحيح / Use Spaces Correctly

❌ **خطأ / Wrong:**
```bash
docker-compose run --rm\
-e ADMIN_EMAIL="..."
web flask users create-admin
```

✅ **صحيح / Correct:**
```bash
docker-compose run --rm \
  -e ADMIN_EMAIL="..." \
  web flask users create-admin
```

---

### 2. استخدم علامات التنصيص / Use Quotes

❌ **خطأ (إذا كان البريد يحتوي على مسافات) / Wrong (if email has spaces):**
```bash
-e ADMIN_EMAIL=my email@example.com
```

✅ **صحيح / Correct:**
```bash
-e ADMIN_EMAIL="my-email@example.com"
```

---

### 3. تحقق من الأخطاء الإملائية / Check for Typos

❌ **خطأ / Wrong:**
```bash
docker-compse run --rm web flask users create-admin
#       ^ خطأ إملائي / typo
```

✅ **صحيح / Correct:**
```bash
docker-compose run --rm web flask users create-admin
```

---

## 📚 الملفات المساعدة / Helper Files

### للحصول على مساعدة سريعة / For Quick Help:

1. **دليل البدء السريع / Quick Start Guide:**
   ```bash
   ./docker-quick-start.sh
   ```

2. **دليل استكشاف الأخطاء / Troubleshooting Guide:**
   ```bash
   cat DOCKER_COMPOSE_TROUBLESHOOTING.md
   ```

3. **دليل الإعداد الكامل / Complete Setup Guide:**
   ```bash
   cat SETUP_GUIDE.md
   ```

---

## 🚀 التدفق الكامل للبدء / Complete Startup Flow

```bash
# 1. إنشاء ملف .env
# 1. Create .env file
cp .env.example .env
# ثم عدل .env وأضف DATABASE_URL و OPENROUTER_API_KEY
# Then edit .env and add DATABASE_URL and OPENROUTER_API_KEY

# 2. بناء الصور
# 2. Build images
docker-compose build

# 3. ترحيل قاعدة البيانات
# 3. Migrate database
docker-compose run --rm web flask db upgrade

# 4. إنشاء مستخدم مشرف
# 4. Create admin user
docker-compose run --rm web flask users create-admin

# 5. تشغيل الخدمات
# 5. Start services
docker-compose up -d

# 6. التحقق من الحالة
# 6. Check status
docker-compose ps

# 7. فتح المتصفح
# 7. Open browser
# http://localhost:5000
```

---

## 💡 اختصار سريع / Quick Shortcut

بدلاً من تنفيذ كل الأوامر يدوياً، استخدم:
Instead of running all commands manually, use:

```bash
./docker-quick-start.sh
```

هذا السكريبت سيقوم بكل شيء تلقائياً! ✨
This script will do everything automatically! ✨

---

**Built with ❤️ by Houssam Benmerah**
