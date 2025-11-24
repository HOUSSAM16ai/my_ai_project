# 🚀 تشغيل التطبيق على GitHub Codespaces

## الطريقة السهلة:

### 1. في Codespaces Shell اكتب:

```bash
docker-compose up --build
```

### 2. انتظر دقيقة أو دقيتين، ثم:

```
http://localhost:8000
```

---

## المشاكل الشائعة والحلول:

### ❌ "Can't create container"

**الحل:**
```bash
docker-compose down
docker system prune -a
docker-compose up --build
```

### ❌ "Port already in use"

**الحل:**
```bash
docker-compose down
docker-compose up --build
```

### ❌ "Database locked"

**الحل:**
```bash
rm -f cogniforge.db
docker-compose up --build
```

---

## مراقبة التطبيق:

```bash
# شاهد السجلات
docker-compose logs -f web

# اختبر الخادم
curl http://localhost:8000/health
```

---

## المتطلبات:

- ✅ Docker (موجود في Codespaces)
- ✅ Docker Compose (موجود في Codespaces)
- ✅ المنفذ 8000 متاح

---

**أن يعمل التطبيق الآن على Codespaces!** ✨
