# User Service

## الدور والمسؤولية
خدمة مستقلة لإدارة المستخدمين والملفات الشخصية والصلاحيات.

## التشغيل محليًا

```bash
uvicorn microservices.user_service.main:app --reload --host 0.0.0.0 --port 8003
```

## الإعدادات الأساسية

- `DATABASE_URL`: سلسلة اتصال قاعدة البيانات (افتراضيًا SQLite داخلية).
- `SERVICE_NAME`: اسم الخدمة المعروض في `/health`.

## نقاط النهاية الأساسية

- `GET /health`
- `POST /users`
- `GET /users`
- `GET /users/{id}`
- `PUT /users/{id}`

## الاختبارات

```bash
pytest tests/services/user_service
```

## التصحيح (Debug)

- راجع بيانات الطلب عند فشل التحقق.
- تحقق من صلاحية الاتصال بقاعدة البيانات عند الأعطال.
