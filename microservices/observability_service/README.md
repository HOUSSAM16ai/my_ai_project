# Observability Service

## الدور والمسؤولية
خدمة مستقلة للمراقبة والتشخيص: جمع القياسات، التحليلات، والتنبؤات.

## التشغيل محليًا

```bash
uvicorn microservices.observability_service.main:app --reload --host 0.0.0.0 --port 8005
```

## الإعدادات الأساسية

- `SERVICE_NAME`: اسم الخدمة المعروض في `/health`.
- `LOG_LEVEL`: مستوى السجلات المطلوب.

## نقاط النهاية الأساسية

- `GET /health`
- `POST /telemetry`
- `GET /metrics`
- `POST /forecast`

## الاختبارات

```bash
pytest tests/services/observability_service
```

## التصحيح (Debug)

- تأكد من صحة حمولة `telemetry`.
- راجع السجلات عند فشل حساب المؤشرات.
