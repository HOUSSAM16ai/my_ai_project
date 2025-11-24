# 🚀 حل مشاكل Docker على Codespaces

## 🔴 المشكلة: "Database is unreachable"

### **السبب:**
```
Codespaces يحاول الاتصال بـ PostgreSQL حقيقي
لكنه معطل أو معلق
```

---

## ✅ الحل السريع:

### **1. استخدم SQLite (الأسهل):**

في `.env.docker` أو عند التشغيل:
```bash
DATABASE_URL=sqlite+aiosqlite:///./cogniforge.db
docker-compose up --build
```

### **2. أو استخدم PostgreSQL (متقدم):**

```bash
# أولاً: شغّل PostgreSQL
docker-compose up postgres -d

# ثم: شغّل التطبيق
docker-compose up web
```

---

## 🔧 خطوات الإصلاح الكاملة:

### **الطريقة 1: SQLite (موصى بها للتطوير):**

```bash
# 1. حذف أي container معطل
docker-compose down -v

# 2. تنظيف النظام
docker system prune -a

# 3. تشغيل مع SQLite
export DATABASE_URL="sqlite+aiosqlite:///./cogniforge.db"
docker-compose up --build
```

### **الطريقة 2: PostgreSQL (إذا أردت قاعدة بيانات حقيقية):**

```bash
# في docker-compose.yml أضف:
# db:
#   image: postgres:15
#   environment:
#     POSTGRES_PASSWORD: admin
#     POSTGRES_DB: cogniforge

# ثم:
docker-compose up --build
```

---

## 📊 المقارنة:

| الجانب | SQLite | PostgreSQL |
|------|--------|------------|
| **التعقيد** | بسيط جداً ✅ | معقد قليلاً |
| **الأداء** | جيد للتطوير | أفضل للإنتاج |
| **التثبيت** | فوري | يحتاج container إضافي |
| **الموصى به** | ✅ للتطوير | للإنتاج |

---

## 🆘 إذا استمرت المشكلة:

```bash
# 1. افحص السجلات
docker-compose logs web

# 2. حذف قاعدة البيانات القديمة
rm -f cogniforge.db

# 3. ابدأ من جديد
docker-compose down
docker-compose up --build
```

---

## ✨ تذكر:

```
✅ SQLite = الخيار الأفضل للتطوير السريع
✅ PostgreSQL = للبيئات الحقيقية
✅ المشكلة عادة تكون في قاعدة البيانات
✅ استخدم SQLite أولاً للاختبار
```
