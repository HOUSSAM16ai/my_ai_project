# Architecture Decision Record: Preventing Service Method Catastrophes

## التاريخ: 2026-01-03
## الحالة: مقبول ومطبق
## السياق: كارثة فقدان المحادثات بسبب أخطاء المسافات البادئة

## المشكلة

حدثت كارثة خطيرة في النظام حيث:
- جميع طرق الخدمة `AdminChatBoundaryService` كانت معرّفة **خارج الكلاس**
- سبب المشكلة: خطأ في المسافات البادئة (indentation error)
- النتيجة: `AttributeError` عند محاولة استدعاء أي طريقة
- التأثير: **عدم القدرة على إجراء محادثات أو عرض الرسائل**

### الأخطاء المكتشفة:
```
AttributeError: 'AdminChatBoundaryService' object has no attribute 'orchestrate_chat_stream'
AttributeError: 'AdminChatBoundaryService' object has no attribute 'list_user_conversations'
AttributeError: 'AdminChatBoundaryService' object has no attribute 'get_latest_conversation_details'
```

## القرار

تطبيق **نظام حماية متعدد الطبقات** لمنع تكرار هذه الكارثة:

### 1. Structure Validation Script
- سكريبت يفحص البنية قبل كل commit
- يكتشف تلقائياً الدوال المعرّفة خارج الكلاسات
- يفحص التناسق في المسافات البادئة
- الموقع: `scripts/validate_structure.py`

### 2. Integration Tests (E2E)
- اختبارات تكامل شاملة لوظيفة المحادثات
- تتحقق من إمكانية الوصول لجميع طرق الخدمة
- تكتشف `AttributeError` قبل الإنتاج
- الموقع: `tests/integration/test_chat_e2e.py`

### 3. GitHub Actions Workflow
- يفشل الـ CI/CD إذا وجد أخطاء بنية
- يمنع دمج الكود الذي يحتوي على أخطاء مماثلة
- الموقع: `.github/workflows/structure-validation.yml`

### 4. Docker Bytecode Prevention
- منع التخزين المؤقت للـ bytecode في Docker
- يضمن تحميل التعديلات الجديدة فوراً
- إضافة `PYTHONDONTWRITEBYTECODE=1`

## العواقب

### الإيجابيات:
✅ منع تكرار كوارث المسافات البادئة
✅ اكتشاف المشاكل تلقائياً قبل الإنتاج
✅ حماية متعددة الطبقات
✅ توثيق واضح للبنية الصحيحة

### السلبيات المحتملة:
⚠️ زيادة طفيفة في وقت CI/CD
⚠️ قد ينتج تحذيرات كاذبة في حالات نادرة

### التخفيف من السلبيات:
- السكريبت سريع (<5 ثوان)
- التحذيرات الكاذبة يمكن تخصيصها في السكريبت
- الفائدة تفوق التكلفة بكثير

## قواعد الكود الجديدة

### 1. بنية الكلاسات:
```python
class ServiceName:
    """Docstring"""
    
    def __init__(self):
        # Initialization
        pass
    
    def public_method(self):
        # ✅ يجب أن تكون الدوال العامة داخل الكلاس
        pass
    
    def _private_method(self):
        # ✅ الدوال الخاصة بالكلاس داخله
        pass


# ✅ الدوال المساعدة على مستوى الموديول
def _module_helper():
    pass

# ✅ دوال Singleton getters
def get_service_name() -> ServiceName:
    pass
```

### 2. المسافات البادئة:
- استخدم **4 spaces** للمسافة البادئة
- جميع الدوال العامة للخدمة **يجب** أن تكون داخل الكلاس
- الدوال المساعدة الخاصة (`_helper`) تكون على مستوى الموديول

### 3. الاختبارات:
- يجب أن تكون هناك اختبارات E2E لكل خدمة حرجة
- يجب أن تتحقق الاختبارات من إمكانية الوصول للدوال

## التنفيذ

تم تنفيذ الحلول في الكوميتات التالية:
- `0fe4099`: إصلاح بنية `AdminChatBoundaryService`
- `40258c7`: تحديث الاختبارات
- `c3f814b`: منع مشاكل bytecode في Docker
- الكوميت الحالي: إضافة نظام الحماية المتعدد الطبقات

## المراجعة

سيتم مراجعة هذا القرار:
- عند اكتشاف أنماط جديدة من الأخطاء
- بعد 3 أشهر من التطبيق
- عند تحديث بنية الكود بشكل كبير

## المراجع

- Python PEP 8: Style Guide for Python Code
- GitHub Actions Best Practices
- Test-Driven Development (TDD) Principles

---

**ملاحظة نهائية:**
هذه الكارثة علمتنا أهمية:
1. **الاختبارات التلقائية الشاملة**
2. **الفحص المستمر للبنية**
3. **عدم الاعتماد على المراجعة اليدوية فقط**
4. **التوثيق الواضح للمعايير**

**لا يجب أن تتكرر هذه الكارثة مرة أخرى.**
