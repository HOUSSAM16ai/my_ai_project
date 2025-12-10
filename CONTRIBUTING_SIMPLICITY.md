# 📘 دليل المساهمة في البساطة
# Contributing to Simplicity Guide

> **"البساطة هي الذكاء الأقصى" - ليوناردو دا فينشي**

---

## 🎯 مبادئ البساطة الصارمة

عند المساهمة في هذا المشروع، يجب الالتزام بأعلى معايير البساطة:

### المعايير الإلزامية

#### 📏 حدود الكود
```
✅ max_file_lines: 200       (الحد الأقصى لسطور الملف)
✅ max_function_lines: 20    (الحد الأقصى لسطور الدالة)
✅ max_complexity: 5         (التعقيد الدوري الأقصى)
✅ max_class_methods: 5      (الحد الأقصى للتوابع)
✅ max_parameters: 3         (الحد الأقصى للمعاملات)
✅ max_nesting: 2            (الحد الأقصى لعمق التداخل)
```

#### 🔍 جودة الكود
```
✅ Type hints على جميع الدوال العامة
✅ Docstrings على جميع الأصناف والدوال
✅ Error handling محكم وواضح
✅ Logging مناسب للتتبع
✅ Tests لكل وظيفة جديدة
```

---

## 🚀 كيفية المساهمة

### 1. Fork & Clone
```bash
# Fork المستودع ثم clone
git clone https://github.com/YOUR_USERNAME/my_ai_project.git
cd my_ai_project
```

### 2. إنشاء Branch جديد
```bash
# استخدم اسم وصفي
git checkout -b feature/simple-awesome-feature
```

### 3. تطبيق معايير البساطة

#### ✅ قبل الكتابة
- هل هذه الميزة ضرورية حقاً؟ (YAGNI)
- هل يمكن جعلها أبسط؟ (KISS)
- هل تخالف أي مبدأ من مبادئ SOLID؟

#### ✅ أثناء الكتابة
- اكتب كود واضح ومباشر
- دالة واحدة = مسؤولية واحدة
- استخدم أسماء واضحة ومعبرة
- تجنب التعقيد غير الضروري

#### ✅ بعد الكتابة
- راجع الكود وبسطه
- أضف اختبارات
- وثق الوظائف الجديدة
- تحقق من المعايير

---

## 📝 قواعد كتابة الكود

### قاعدة 1: البساطة أولاً

#### ❌ معقد
```python
def process_data(data: list, filter_func=None, transform_func=None, 
                 sort_key=None, reverse=False, limit=None, 
                 offset=0, include_metadata=False):
    """دالة معقدة جداً - 8 معاملات!"""
    result = []
    for item in data:
        if filter_func and not filter_func(item):
            continue
        if transform_func:
            item = transform_func(item)
        result.append(item)
    if sort_key:
        result.sort(key=sort_key, reverse=reverse)
    if offset:
        result = result[offset:]
    if limit:
        result = result[:limit]
    if include_metadata:
        return {"data": result, "count": len(result)}
    return result
```

#### ✅ بسيط
```python
def filter_data(data: list, predicate) -> list:
    """فلترة البيانات - مسؤولية واحدة"""
    return [item for item in data if predicate(item)]

def transform_data(data: list, transformer) -> list:
    """تحويل البيانات - مسؤولية واحدة"""
    return [transformer(item) for item in data]

def sort_data(data: list, key, reverse=False) -> list:
    """ترتيب البيانات - مسؤولية واحدة"""
    return sorted(data, key=key, reverse=reverse)

def paginate_data(data: list, offset=0, limit=None) -> list:
    """تقسيم البيانات إلى صفحات - مسؤولية واحدة"""
    end = offset + limit if limit else None
    return data[offset:end]
```

### قاعدة 2: استخدم Plugin System

#### ❌ تعديل الكود الأساسي
```python
# DON'T - لا تعدل الخدمات الموجودة
class ChatService:
    def process(self, message):
        # إضافة ميزة جديدة هنا = تعديل للكود الأساسي
        pass
```

#### ✅ أنشئ Plugin جديد
```python
# DO - أنشئ plugin منفصل
from app.core.interfaces import IPlugin

class MyFeaturePlugin(IPlugin):
    """ميزة جديدة كـ plugin منفصل"""
    
    @property
    def name(self) -> str:
        return "my_feature"
    
    # ... تطبيق بقية الواجهة

plugin = MyFeaturePlugin()
```

### قاعدة 3: Type Hints دائماً

```python
# ✅ Good
def calculate_sum(numbers: list[int]) -> int:
    """حساب المجموع مع type hints"""
    return sum(numbers)

# ❌ Bad
def calculate_sum(numbers):
    """بدون type hints"""
    return sum(numbers)
```

### قاعدة 4: Docstrings واضحة

```python
def process_user_data(user_id: int, include_history: bool = False) -> dict:
    """
    معالجة بيانات المستخدم.
    Process user data.
    
    Args:
        user_id: معرف المستخدم
        include_history: تضمين السجل التاريخي
    
    Returns:
        dict: بيانات المستخدم المعالجة
    
    Raises:
        ValueError: إذا كان user_id غير صالح
    """
    pass
```

---

## 🧪 الاختبارات

### اختبار كل plugin جديد

```python
# tests/plugins/test_my_plugin.py

import pytest
from app.plugins.my_plugin.plugin import plugin

@pytest.mark.asyncio
async def test_plugin_initialization():
    """اختبار تهيئة الإضافة"""
    await plugin.initialize()
    assert plugin._initialized is True

@pytest.mark.asyncio
async def test_plugin_health():
    """اختبار صحة الإضافة"""
    health = await plugin.health_check()
    assert health["status"] == "healthy"

def test_plugin_properties():
    """اختبار خصائص الإضافة"""
    assert plugin.name == "my_plugin"
    assert plugin.version
    assert plugin.plugin_type
```

### تشغيل الاختبارات

```bash
# جميع الاختبارات
pytest

# اختبارات plugin محدد
pytest tests/plugins/test_my_plugin.py

# مع التغطية
pytest --cov=app --cov-report=html
```

---

## 📋 Checklist قبل الـ Commit

قبل عمل commit، تأكد من:

- [ ] الكود يتبع معايير البساطة الصارمة
- [ ] لا توجد دوال أكثر من 20 سطر
- [ ] لا توجد ملفات أكثر من 200 سطر
- [ ] التعقيد الدوري < 5 لكل دالة
- [ ] Type hints على جميع الدوال العامة
- [ ] Docstrings واضحة وكاملة
- [ ] الاختبارات تمر بنجاح
- [ ] لا توجد تغييرات كاسرة (Breaking Changes)
- [ ] التوثيق محدث

### فحص تلقائي

```bash
# فحص جودة الكود
python /tmp/strict_simplicity_audit.py

# فحص التعقيد
radon cc app/ -a -nb

# فحص Type hints
mypy app/

# تنسيق الكود
black app/
isort app/
```

---

## 🔄 عملية المراجعة

### ما نبحث عنه في المراجعة

#### ✅ نقبل
- كود بسيط وواضح
- plugins جديدة تتبع المعايير
- تحسينات تدريجية
- توثيق محدث
- اختبارات كاملة

#### ❌ نرفض
- كود معقد بدون ضرورة
- دوال كبيرة (>20 سطر)
- تغييرات كاسرة
- بدون اختبارات
- بدون توثيق

---

## 💡 نصائح للمساهمين

### 1. ابدأ صغيراً
- ساهم بـ plugin واحد بسيط أولاً
- لا تحاول إعادة كتابة كل شيء
- تحسينات تدريجية أفضل

### 2. اسأل أولاً
- إذا كنت غير متأكد، افتح Issue
- ناقش التصميم قبل التنفيذ
- اطلب مراجعة مبكرة

### 3. اتبع المعايير
- المعايير موجودة لضمان الجودة
- لا تحاول التحايل عليها
- إذا كانت المعايير تمنعك، ناقش السبب

### 4. وثق كل شيء
- الكود الجيد يشرح نفسه
- التوثيق يشرح السبب
- الأمثلة تشرح الاستخدام

---

## 📞 الحصول على المساعدة

### لديك سؤال؟
- افتح [Issue](https://github.com/ai-for-solution-labs/my_ai_project/issues)
- اقرأ [التوثيق](./PLUGIN_SYSTEM_GUIDE.md)
- راجع [الأمثلة](./app/plugins/)

### وجدت Bug؟
- ابحث في Issues الموجودة أولاً
- قدم تفاصيل كاملة
- أضف خطوات إعادة الإنتاج
- اقترح حل إن أمكن

---

## 🌟 شكراً للمساهمة!

نقدر وقتك ومساهمتك في جعل هذا المشروع أبسط وأفضل!

**تذكر**: البساطة ليست سهلة، لكنها تستحق الجهد. 💪

---

**Built with ❤️ by Contributors Following Simplicity Principles**
