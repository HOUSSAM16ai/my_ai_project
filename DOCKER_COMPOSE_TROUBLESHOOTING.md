# Docker Compose - دليل حل المشاكل الشائعة
# Docker Compose Common Issues Guide

## 🔴 المشكلة 1: "no such service: run"
### Problem 1: "no such service: run"

**الخطأ الذي يظهر / Error shown:**
```bash
docker-compose run --rm \
-e ADMIN_EMAIL="..." \
-e ADMIN_PASSWORD="..." \
web flask users init-admin

# Error: no such service: run
```

**السبب / Cause:**
الأمر مكتوب بشكل خاطئ. كلمة `run` تم كتابتها في السطر الخطأ.
The command is malformed. The word `run` is on the wrong line.

**الحل / Solution:**
استخدم الأمر الصحيح على سطر واحد أو مع backslash بشكل صحيح:
Use the correct command on one line or with proper backslash:

```bash
# الطريقة الأولى: سطر واحد / Method 1: One line
docker-compose run --rm web flask users create-admin
# أو / or
docker compose run --rm web flask users create-admin

# الطريقة الثانية: عدة أسطر بشكل صحيح / Method 2: Multiple lines correctly
docker-compose run --rm \
  -e ADMIN_EMAIL="benmerahhoussam16@gmail.com" \
  -e ADMIN_PASSWORD="1111" \
  -e ADMIN_NAME="Houssam Benmerah" \
  web flask users create-admin
```

**ملاحظة / Note:**
- استخدم `docker-compose` (Docker Compose v1) أو `docker compose` (Docker Compose v2)
- Use `docker-compose` (Docker Compose v1) or `docker compose` (Docker Compose v2)
- كلاهما يعملان بنفس الطريقة / Both work the same way

---

## 🔴 المشكلة 2: الواجهة لا تظهر على المنفذ 5000
### Problem 2: Interface not showing on port 5000

**الأسباب المحتملة / Possible causes:**

### السبب 1: الخدمات غير مشغلة / Cause 1: Services not running

**التحقق / Check:**
```bash
docker-compose ps
```

**الحل / Solution:**
```bash
# إذا كانت الخدمات متوقفة / If services are stopped
docker-compose up -d

# التحقق من السجلات / Check logs
docker-compose logs web
```

### السبب 2: ملف .env غير موجود أو غير مكتمل / Cause 2: .env file missing or incomplete

**التحقق / Check:**
```bash
ls -la .env
```

**الحل / Solution:**
```bash
# إنشاء من المثال / Create from example
cp .env.example .env

# تعديل الملف وإضافة القيم المطلوبة / Edit file and add required values
nano .env  # أو vim أو أي محرر نصوص
```

**القيم المطلوبة / Required values:**
```env
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-xx.pooler.supabase.com:6543/postgres?sslmode=require
OPENROUTER_API_KEY=sk-or-v1-xxxxx
ADMIN_EMAIL=your-email@example.com
ADMIN_PASSWORD=your-secure-password
SECRET_KEY=your-random-secret-key
```

### السبب 3: قاعدة البيانات غير مهيأة / Cause 3: Database not initialized

**الحل / Solution:**
```bash
# تشغيل الترحيلات / Run migrations
docker-compose run --rm web flask db upgrade

# إنشاء المستخدم المشرف / Create admin user
docker-compose run --rm web flask users create-admin
```

### السبب 4: المنفذ 5000 مستخدم من برنامج آخر / Cause 4: Port 5000 used by another program

**التحقق / Check:**
```bash
# على Linux/Mac
lsof -i :5000

# على Windows
netstat -ano | findstr :5000
```

**الحل / Solution:**
```bash
# إيقاف البرنامج الآخر أو تغيير المنفذ في docker-compose.yml
# Stop other program or change port in docker-compose.yml

# مثال: تغيير المنفذ إلى 5001
# Example: Change port to 5001
# في docker-compose.yml / In docker-compose.yml:
# ports:
#   - "5001:5000"
```

---

## 🔴 المشكلة 3: خطأ في الاتصال بقاعدة البيانات
### Problem 3: Database connection error

**الخطأ / Error:**
```
could not connect to server: Connection refused
```

**الحل / Solution:**

1. **تحقق من DATABASE_URL في .env:**
```bash
grep DATABASE_URL .env
```

2. **تأكد من استخدام الرابط الصحيح من Supabase:**
   - افتح لوحة تحكم Supabase / Open Supabase Dashboard
   - اذهب إلى Project Settings > Database
   - انسخ "Connection string" > URI
   - استخدم "Connection pooling" (port 6543) للتطوير
   - أضف `?sslmode=require` في النهاية

3. **تأكد من ترميز الأحرف الخاصة في كلمة المرور:**
```
@ → %40
# → %23
$ → %24
```

---

## ✅ الأوامر الصحيحة للاستخدام اليومي
## ✅ Correct Commands for Daily Use

### بدء التطبيق / Start Application
```bash
# الطريقة السهلة / Easy way
./docker-quick-start.sh

# أو يدوياً / Or manually
docker-compose up -d
```

### عرض حالة الخدمات / Show Service Status
```bash
docker-compose ps
```

### عرض السجلات / View Logs
```bash
# كل الخدمات / All services
docker-compose logs -f

# خدمة معينة / Specific service
docker-compose logs -f web
```

### إيقاف الخدمات / Stop Services
```bash
docker-compose stop
```

### إعادة تشغيل / Restart
```bash
docker-compose restart
```

### حذف كل شيء والبدء من جديد / Delete everything and start fresh
```bash
docker-compose down -v
docker-compose up -d
```

---

## 🔧 أوامر Flask المفيدة
## 🔧 Useful Flask Commands

### إدارة قاعدة البيانات / Database Management
```bash
# ترحيل قاعدة البيانات / Migrate database
docker-compose run --rm web flask db upgrade

# إنشاء ترحيل جديد / Create new migration
docker-compose run --rm web flask db migrate -m "Description"

# التراجع / Rollback
docker-compose run --rm web flask db downgrade

# حالة قاعدة البيانات / Database health
docker-compose run --rm web flask db health

# إحصائيات / Statistics
docker-compose run --rm web flask db stats
```

### إدارة المستخدمين / User Management
```bash
# إنشاء مستخدم مشرف / Create admin user
docker-compose run --rm web flask users create-admin

# أو استخدم / Or use
docker-compose run --rm web flask users init-admin

# عرض كل المستخدمين / List all users
docker-compose run --rm web flask users list

# إنشاء مستخدم عادي / Create regular user
docker-compose run --rm web flask users create --email user@example.com --name "User Name"
```

### Overmind (مخطط المهام) / Overmind (Task Planner)
```bash
# عرض كل المهام / List all missions
docker-compose run --rm web flask overmind list

# إنشاء مهمة جديدة / Create new mission
docker-compose run --rm web flask overmind create --objective "Task description"

# حالة مهمة / Mission status
docker-compose run --rm web flask overmind status <mission_id>
```

---

## 🆘 الحصول على المساعدة
## 🆘 Getting Help

إذا استمرت المشاكل، تحقق من:
If problems persist, check:

1. **السجلات / Logs:**
   ```bash
   docker-compose logs -f web
   ```

2. **ملف .env:** تأكد من وجود جميع المتغيرات المطلوبة
   **File .env:** Make sure all required variables exist

3. **اتصال قاعدة البيانات:** جرب الاتصال يدوياً
   **Database connection:** Try connecting manually

4. **المستندات:**
   - `SETUP_GUIDE.md` - دليل الإعداد الكامل
   - `DATABASE_GUIDE_AR.md` - دليل قاعدة البيانات
   - `README.md` - نظرة عامة

---

## 🚀 نصائح للأداء الأفضل
## 🚀 Tips for Better Performance

1. **استخدم Connection Pooling من Supabase (port 6543)**
2. **أضف `?sslmode=require` إلى DATABASE_URL**
3. **تحقق من السجلات بانتظام**
4. **احتفظ بنسخة احتياطية من .env**
5. **استخدم docker-compose logs لتتبع الأخطاء**

---

**Built with ❤️ by Houssam Benmerah**
