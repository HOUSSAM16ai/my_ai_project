# Memory Agent Service

## الدور والمسؤولية
خدمة مستقلة لإدارة الذاكرة والسياق (التخزين، البحث، الاسترجاع).

## التشغيل محليًا

```bash
uvicorn microservices.memory_agent.main:app --reload --host 0.0.0.0 --port 8002
```

## الإعدادات الأساسية

- `DATABASE_URL`: سلسلة اتصال قاعدة البيانات (افتراضيًا SQLite داخلية).
- `SERVICE_NAME`: اسم الخدمة المعروض في `/health`.

## نقاط النهاية الأساسية

- `GET /health`
- `POST /memories`
- `GET /memories/search`
- `GET /memories/{id}`

## الاختبارات

```bash
pytest tests/services/memory_agent
```

## التصحيح (Debug)

- تأكد من صحة بيانات الإدخال في عمليات الحفظ والبحث.
- راجع إعدادات قاعدة البيانات عند ظهور أخطاء اتصال.
