# 🏗️ خريطة المعمارية - تحديد الـ Domains

## 📦 الـ Domains الرئيسية المكتشفة

### 1. **Core Domain** - النواة الأساسية
```
app/core/
├── engine/          # محرك التنفيذ
├── gateway/         # بوابة الاتصالات
├── interfaces/      # الواجهات المجردة
├── kernel_v2/       # النواة الأساسية
├── patterns/        # الأنماط التصميمية
├── registry/        # سجل الخدمات
├── resilience/      # المرونة والتعافي
├── scaling/         # التوسع الأفقي
└── utils/           # أدوات مساعدة
```
**المسؤولية**: البنية التحتية الأساسية للنظام
**المشاكل**: خلط بين Infrastructure و Business Logic

---

### 2. **Services Domain** - الخدمات التطبيقية
```
app/services/
├── api_advanced_analytics_service.py      ⚠️ تعقيد: 95
├── security_metrics_engine.py             ⚠️ تعقيد: 76
├── user_analytics_metrics_service.py      ⚠️ تعقيد: 55
├── sre_error_budget_service.py            ⚠️ تعقيد: 39
├── project_context_service.py             ⚠️ تعقيد: 36
├── ai_adaptive_microservices.py           ⚠️ تعقيد: 34
└── agent_tools/
    ├── fs_tools.py                        ⚠️ تعقيد: 57
    └── search_tools.py                    ⚠️ تعقيد: 38
```
**المسؤولية**: منطق الأعمال والخدمات
**المشاكل**: 
- God Objects (ملفات ضخمة بمسؤوليات متعددة)
- انتهاك SRP بشكل واضح
- خلط بين Analytics + Security + AI

---

### 3. **API Domain** - واجهات البرمجة
```
app/api/
├── routers/         # مسارات API
└── v2/              # الإصدار الثاني
```
**المسؤولية**: نقاط الدخول HTTP
**الحالة**: جيدة نسبياً

---

### 4. **Middleware Domain** - الطبقة الوسيطة
```
app/middleware/
├── adapters/        # محولات
├── ai/              # ذكاء اصطناعي
├── security/        # أمان
├── error_handling/  # معالجة الأخطاء
├── observability/   # المراقبة
└── factory/         # المصانع
```
**المسؤولية**: معالجة الطلبات والاستجابات
**الحالة**: متوسطة

---

### 5. **Overmind Domain** - التخطيط والذكاء
```
app/overmind/
├── planning/
│   ├── deep_indexer_v2/     ⚠️ تعقيد: 33
│   ├── hyper_planner/
│   └── factory.py           ⚠️ تعقيد معقد
└── graph/
```
**المسؤولية**: التخطيط الذكي والتحليل
**المشاكل**: تعقيد عالي في المخططات

---

### 6. **Security Domain** - الأمان
```
app/security/
└── owasp_validator.py       ⚠️ تعقيد: 27
```
**المسؤولية**: التحقق الأمني
**المشاكل**: ملف واحد يقوم بكل شيء

---

### 7. **Infrastructure Domain** - البنية التحتية
```
app/infrastructure/
├── config/
└── patterns/
```
**المسؤولية**: الإعدادات والأنماط
**الحالة**: جيدة

---

### 8. **Plugins Domain** - الإضافات
```
app/plugins/
├── chat/
├── database/
└── llm/
```
**المسؤولية**: الوحدات القابلة للتوسع
**الحالة**: جيدة (تطبيق OCP)

---

## 🎯 المشاكل المعمارية الرئيسية

### 1. **انتهاك Separation of Concerns**
```
❌ الوضع الحالي:
app/services/api_advanced_analytics_service.py
├── Analytics Logic
├── ML Models
├── Report Generation
├── Data Storage
└── API Integration

✅ المطلوب:
app/analytics/
├── domain/
│   ├── models.py
│   └── interfaces.py
├── application/
│   ├── anomaly_detection.py
│   ├── report_generation.py
│   └── prediction.py
└── infrastructure/
    ├── storage.py
    └── ml_models.py
```

---

### 2. **God Objects في Services**

**الملفات المشكلة**:
1. `api_advanced_analytics_service.py` - 636 سطر
2. `security_metrics_engine.py` - 655 سطر
3. `agent_tools/fs_tools.py` - 544 سطر

**الحل**: تطبيق **Microservices Pattern** داخلياً

---

### 3. **خلط بين Layers**

```
❌ المشكلة:
Services → تستدعي مباشرة → Database
Services → تحتوي على → Business Logic + Infrastructure

✅ الحل:
API Layer → Application Layer → Domain Layer → Infrastructure Layer
```

---

## 🏗️ المعمارية المقترحة (Clean Architecture)

```
app/
├── domain/                    # Business Logic النقي
│   ├── analytics/
│   │   ├── entities.py
│   │   ├── value_objects.py
│   │   └── interfaces.py
│   ├── security/
│   └── monitoring/
│
├── application/               # Use Cases
│   ├── analytics/
│   │   ├── detect_anomalies.py
│   │   ├── generate_reports.py
│   │   └── predict_trends.py
│   ├── security/
│   └── monitoring/
│
├── infrastructure/            # التفاصيل التقنية
│   ├── persistence/
│   ├── external_services/
│   └── ml_models/
│
└── api/                       # نقاط الدخول
    └── routers/
```

---

## 📊 خطة التحويل

### Phase 1: Services Domain (الأولوية القصوى)
- [ ] تفكيك `api_advanced_analytics_service.py`
- [ ] تفكيك `security_metrics_engine.py`
- [ ] تفكيك `agent_tools/fs_tools.py`

### Phase 2: Core Domain
- [ ] فصل Business Logic عن Infrastructure
- [ ] إنشاء Interfaces واضحة

### Phase 3: Integration
- [ ] ربط الطبقات الجديدة
- [ ] كتابة Tests شاملة
- [ ] Migration تدريجي

---

## ✅ معايير النجاح

- [ ] كل Domain مستقل تماماً
- [ ] لا يوجد Circular Dependencies
- [ ] كل ملف < 200 سطر
- [ ] كل دالة تعقيد < 10
- [ ] Test Coverage > 80%

