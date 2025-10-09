# 🚀 دليل إعداد Supabase | Supabase Setup Guide

## نظرة عامة | Overview

تم تحديث المشروع للعمل مع قاعدة بيانات Supabase الخارجية مع دعم محسّن لـ GitHub Codespaces.  
The project has been updated to work with external Supabase database with enhanced support for GitHub Codespaces.

## التحديثات الرئيسية | Key Updates

### ✅ 1. docker-compose.yml
- ✨ تم إضافة متغيرات البيئة الصريحة باستخدام `${VAR}` بدلاً من `env_file`
- ✨ Added explicit environment variables using `${VAR}` syntax instead of `env_file`
- 🔧 يتم تحميل القيم تلقائياً من `.env` مع دعم القيم الافتراضية
- 🔧 Values are automatically loaded from `.env` with default value support

### ✅ 2. .env.example
- 📝 قسم Supabase واضح ومفصّل مع أمثلة عملية
- 📝 Clear and detailed Supabase section with practical examples
- 🌐 شرح بالعربية والإنجليزية لكل خيار
- 🌐 Bilingual explanations (Arabic & English) for each option
- ⚙️ إضافة متغيرات SUPABASE_URL وSUPABASE_ANON_KEY وSUPABASE_SERVICE_ROLE_KEY
- ⚙️ Added SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY variables

### ✅ 3. devcontainer.json
- 🔐 دعم Codespaces Secrets للأمان المحسّن
- 🔐 Codespaces Secrets support for enhanced security
- 🔄 تحميل تلقائي للأسرار من `Settings > Codespaces > Secrets`
- 🔄 Automatic loading of secrets from `Settings > Codespaces > Secrets`

---

## 📋 خطوات الإعداد | Setup Steps

### الطريقة 1: استخدام ملف .env (Development)

#### 1️⃣ نسخ ملف .env.example
```bash
cp .env.example .env
```

#### 2️⃣ الحصول على بيانات Supabase
انتقل إلى لوحة تحكم Supabase:  
Go to your Supabase Dashboard:
- **Project Settings** > **Database** > **Connection string** > **URI**

#### 3️⃣ اختر نوع الاتصال | Choose Connection Type

**Direct Connection (5432)** - للعمليات الكتابية | For write operations:
```
postgresql://postgres:YOUR_PASSWORD@YOUR-PROJECT-HOST.supabase.co:5432/postgres?sslmode=require
```

**Pooled Connection (6543)** - للتحميل العالي | For high load:
```
postgresql://postgres:YOUR_PASSWORD@YOUR-PROJECT-HOST.pooler.supabase.co:6543/postgres?sslmode=require
```

#### 4️⃣ تعديل .env
افتح `.env` وعدّل القيم التالية:
```bash
# قاعدة البيانات | Database
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@YOUR-PROJECT-HOST.supabase.co:5432/postgres?sslmode=require"

# للتكاملات المتقدمة (اختياري) | For advanced integrations (optional)
SUPABASE_URL="https://YOUR-PROJECT-REF.supabase.co"
SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# معلومات المشرف | Admin info
ADMIN_EMAIL="your-email@example.com"
ADMIN_PASSWORD="strong-password"
ADMIN_NAME="Your Name"

# مفاتيح AI | AI Keys
OPENROUTER_API_KEY="sk-or-v1-..."
SECRET_KEY="your-very-strong-secret-key"
```

⚠️ **مهم | Important**:
- إذا كانت كلمة المرور تحتوي على `@` أو `#` أو رموز خاصة، قم بترميزها
- If password contains `@`, `#` or special characters, percent-encode them:
  - `@` → `%40`
  - `#` → `%23`
  - `/` → `%2F`

#### 5️⃣ إعادة بناء الحاويات | Rebuild Containers
```bash
docker compose up -d --build
```

#### 6️⃣ تشغيل الترحيلات | Run Migrations
```bash
docker compose exec web flask db upgrade
```

---

### الطريقة 2: استخدام Codespaces Secrets (Production/Secure)

#### 1️⃣ إضافة الأسرار في GitHub
انتقل إلى:  
Go to:
- **Settings** > **Codespaces** > **Secrets** > **New secret**

أضف الأسرار التالية:  
Add the following secrets:

| Secret Name | Example Value |
|-------------|---------------|
| `DATABASE_URL` | `postgresql://postgres:pass@host.supabase.co:5432/postgres?sslmode=require` |
| `OPENROUTER_API_KEY` | `sk-or-v1-...` |
| `SECRET_KEY` | `your-strong-secret-key` |
| `ADMIN_EMAIL` | `admin@example.com` |
| `ADMIN_PASSWORD` | `strong-password` |
| `ADMIN_NAME` | `Admin User` |
| `SUPABASE_URL` | `https://xxx.supabase.co` |
| `SUPABASE_ANON_KEY` | `eyJhbGci...` |

#### 2️⃣ إنشاء أو إعادة بناء Codespace
- احذف Codespace الحالي إن وُجد
- Delete existing Codespace if any
- أنشئ Codespace جديد
- Create a new Codespace

سيتم تحميل الأسرار تلقائياً! 🎉  
Secrets will be loaded automatically! 🎉

---

## 🧪 التحقق من الإعداد | Verify Setup

### 1. فحص اتصال قاعدة البيانات | Check Database Connection
```bash
docker compose exec web python -c "from app import db; print('✅ Database connected!' if db.engine else '❌ Failed')"
```

### 2. فحص المتغيرات | Check Variables
```bash
docker compose exec web env | grep DATABASE_URL
docker compose exec web env | grep ADMIN_EMAIL
```

### 3. تشغيل السكربت التحقق | Run Verification Script
```bash
bash .devcontainer/on-attach.sh
```

---

## 🔧 استكشاف الأخطاء | Troubleshooting

### ❌ خطأ: "PostgreSQL غير جاهز" | "PostgreSQL not ready"
**الحل | Solution**:
1. تأكد من صحة `DATABASE_URL` في `.env`
2. تأكد من إضافة `?sslmode=require` في نهاية السلسلة
3. تحقق من أن قاعدة البيانات نشطة في Supabase Dashboard

### ❌ خطأ: "flask db غير متاح" | "flask db not available"
**الحل | Solution**:
```bash
# داخل الحاوية | Inside container
export FLASK_APP=run:app
pip install -r requirements.txt
flask db upgrade
```

### ❌ خطأ: "Cannot connect to database"
**الحل | Solution**:
1. تحقق من IP المسموح في Supabase:
   - **Project Settings** > **Database** > **Connection Pooling**
   - أضف `0.0.0.0/0` للسماح بجميع الاتصالات (للتطوير فقط)
   - Add `0.0.0.0/0` to allow all connections (development only)

2. تأكد من أن المنفذ صحيح (5432 للـ Direct، 6543 للـ Pooled)

---

## 📚 مصادر إضافية | Additional Resources

- [Supabase Database Documentation](https://supabase.com/docs/guides/database)
- [GitHub Codespaces Secrets](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-secrets-for-your-codespaces)
- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)

---

## ✅ القيم الافتراضية المدعومة | Supported Default Values

المتغيرات التالية لها قيم افتراضية في `docker-compose.yml`:  
The following variables have default values in `docker-compose.yml`:

```yaml
DEFAULT_AI_MODEL: anthropic/claude-3.7-sonnet:thinking
LOW_COST_MODEL: openai/gpt-4o-mini
FLASK_ENV: development
FLASK_DEBUG: 1
PLANNER_MAX_CHUNKS: 50
DISABLED_TOOLS: delete_file
# ... والمزيد | and more
```

لذا لا تحتاج لتعيينهم في `.env` إلا إذا أردت تغييرها.  
So you don't need to set them in `.env` unless you want to change them.

---

## 🎯 الخلاصة | Summary

بعد هذا التحديث، يمكنك:  
After this update, you can:

✅ الاتصال بـ Supabase مباشرة بدون قاعدة بيانات محلية  
✅ Connect to Supabase directly without local database

✅ استخدام Codespaces Secrets للأمان المحسّن  
✅ Use Codespaces Secrets for enhanced security

✅ رؤية جميع المتغيرات المستخدمة بوضوح في `docker-compose.yml`  
✅ See all used variables clearly in `docker-compose.yml`

✅ استخدام القيم الافتراضية المعقولة دون تكوين إضافي  
✅ Use sensible defaults without additional configuration

---

**هل تحتاج مساعدة؟ | Need Help?**  
افتح Issue في GitHub أو راجع ملفات التوثيق الأخرى في المشروع.  
Open an Issue on GitHub or check other documentation files in the project.
