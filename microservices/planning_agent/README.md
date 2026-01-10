# Planning Agent Service

## الدور والمسؤولية
خدمة مستقلة لتوليد خطط تعليمية بناءً على أهداف المستخدم.

## التشغيل محليًا

```bash
uvicorn microservices.planning_agent.main:app --reload --host 0.0.0.0 --port 8001
```

## الإعدادات الأساسية

- `DATABASE_URL`: سلسلة اتصال قاعدة البيانات (افتراضيًا SQLite داخلية).
- `SERVICE_NAME`: اسم الخدمة المعروض في `/health`.

## نقاط النهاية الأساسية

- `GET /health`
- `POST /plans`
- `GET /plans`
- `GET /plans/{id}`

## الاختبارات

```bash
pytest tests/services/planning_agent
```

## التصحيح (Debug)

- افحص السجلات عبر الـ terminal.
- تحقق من إعدادات `DATABASE_URL` عند فشل الاتصال.
