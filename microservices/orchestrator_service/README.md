# Orchestrator Service

## الدور والمسؤولية
خدمة تنسيق للوكلاء المستقلين مع واجهات API لتسجيل الوكلاء وإدارة المهام.

## التشغيل محليًا

```bash
uvicorn microservices.orchestrator_service.main:app --reload --host 0.0.0.0 --port 8004
```

## الإعدادات الأساسية

- `DATABASE_URL`: سلسلة اتصال قاعدة البيانات (افتراضيًا SQLite داخلية).
- `SERVICE_NAME`: اسم الخدمة المعروض في `/health`.

## نقاط النهاية الأساسية

- `GET /health`
- `GET /orchestrator/agents`
- `POST /orchestrator/tasks`
- `GET /orchestrator/tasks`

## الاختبارات

```bash
pytest tests/services/orchestrator_service
```

## التصحيح (Debug)

- تأكد من إعداد روابط الوكلاء في الإعدادات.
- راجع السجلات عند فشل الاتصال بالوكلاء.
