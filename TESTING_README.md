# 🧪 دليل نظام الاختبار الشامل

## 🎯 نظرة عامة

هذا المشروع يستخدم نظام اختبار متقدم ومتعدد المستويات لضمان **100% تغطية** و **100% mutation score**.

---

## 🚀 البدء السريع

### تشغيل جميع الاختبارات
```bash
./scripts/run_comprehensive_tests.sh
```

### تشغيل اختبارات محددة
```bash
# اختبارات الوحدات فقط
pytest tests/validators/ tests/utils/ -v

# اختبارات Property-based
pytest tests/property_based/ -v --hypothesis-show-statistics

# اختبارات Fuzzing
pytest tests/fuzzing/ -v -m fuzz

# اختبارات الأمان
pytest tests/security/ -v -m security

# اختبارات التكامل
pytest tests/integration/ -v
```

### قياس التغطية
```bash
# تغطية شاملة مع تقرير HTML
pytest --cov=app --cov-report=html --cov-report=term-missing

# فتح التقرير
open htmlcov/index.html

# تغطية مع فشل إذا أقل من 100%
pytest --cov=app --cov-fail-under=100
```

---

## 📁 هيكل الاختبارات

```
tests/
├── validators/              # اختبارات التحقق من البيانات
│   ├── test_base_validator_comprehensive.py
│   └── test_schemas_comprehensive.py
│
├── utils/                   # اختبارات الأدوات المساعدة
│   ├── test_text_processing_comprehensive.py
│   └── test_service_locator_comprehensive.py
│
├── property_based/          # اختبارات قائمة على الخصائص
│   └── test_validators_properties.py
│
├── fuzzing/                 # اختبارات Fuzzing
│   └── test_text_processing_fuzzing.py
│
├── security/                # اختبارات الأمان
│   └── test_validators_security.py
│
├── integration/             # اختبارات التكامل
│   └── test_validators_integration.py
│
└── conftest.py             # إعدادات pytest مشتركة
```

---

## 🧪 أنواع الاختبارات

### 1. Unit Tests (اختبارات الوحدات)
**الهدف**: اختبار كل دالة/كلاس بشكل منفصل

**مثال**:
```python
def test_validate_success_with_valid_data():
    """Test successful validation with all required fields"""
    data = {"name": "John Doe", "age": 30}
    success, validated, errors = BaseValidator.validate(SimpleSchema, data)
    
    assert success is True
    assert validated == {"name": "John Doe", "age": 30}
    assert errors is None
```

**تشغيل**:
```bash
pytest tests/validators/test_base_validator_comprehensive.py -v
```

### 2. Property-Based Tests
**الهدف**: اختبار خصائص عامة مع آلاف الحالات المولدة تلقائيًا

**مثال**:
```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.text(min_size=1, max_size=100))
def test_validate_any_string_name(self, name):
    """Property: Any non-empty string should be valid for name field"""
    data = {"name": name}
    success, validated, errors = BaseValidator.validate(SimpleSchema, data)
    
    assert success is True
    assert validated["name"] == name
```

**تشغيل**:
```bash
pytest tests/property_based/ -v --hypothesis-show-statistics
```

### 3. Fuzzing Tests
**الهدف**: اكتشاف أخطاء غير متوقعة بمدخلات عشوائية

**مثال**:
```python
def test_fuzz_random_bytes(self):
    """Test with random byte sequences"""
    for _ in range(100):
        random_bytes = bytes(random.randint(0, 255) for _ in range(1000))
        text = random_bytes.decode("utf-8", errors="ignore")
        result = strip_markdown_fences(text)
        assert isinstance(result, str)
```

**تشغيل**:
```bash
pytest tests/fuzzing/ -v -m fuzz --timeout=300
```

### 4. Security Tests
**الهدف**: اختبار مقاومة الهجمات الأمنية

**مثال**:
```python
def test_sql_injection_patterns(self):
    """Test that SQL injection patterns are handled safely"""
    injection_patterns = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
    ]
    
    for pattern in injection_patterns:
        data = {"text": pattern}
        success, validated, errors = BaseValidator.validate(TestSchema, data)
        assert success is True
```

**تشغيل**:
```bash
pytest tests/security/ -v -m security
```

### 5. Integration Tests
**الهدف**: اختبار تفاعل الوحدات مع بعضها

**مثال**:
```python
def test_create_user_workflow(self):
    """Test complete user creation workflow"""
    # Step 1: Validate input
    user_data = {"username": "john_doe", "email": "john@example.com"}
    success, validated, errors = BaseValidator.validate(UserSchema, user_data)
    assert success is True
    
    # Step 2: Format success response
    response = BaseValidator.format_success_response(validated)
    assert response["success"] is True
```

**تشغيل**:
```bash
pytest tests/integration/ -v
```

---

## 🧬 Mutation Testing

### ما هو Mutation Testing؟
Mutation testing يختبر **جودة الاختبارات نفسها** عن طريق إدخال أخطاء صغيرة (طفرات) في الكود ومعرفة إذا كانت الاختبارات تكتشفها.

### التشغيل
```bash
# تشغيل mutation testing على وحدة محددة
mutmut run --paths-to-mutate=app/validators/base.py

# عرض النتائج
mutmut results

# عرض طفرة محددة
mutmut show 1

# توليد تقرير HTML
mutmut html --directory mutation_report
open mutation_report/index.html
```

### فهم النتائج
- **Killed**: الطفرة تم اكتشافها (جيد ✅)
- **Survived**: الطفرة لم تُكتشف (سيء ❌ - يحتاج اختبار إضافي)
- **Timeout**: الطفرة سببت تجمد
- **Suspicious**: نتيجة غير متوقعة

---

## 📊 قياس التغطية

### تشغيل مع تقرير مفصل
```bash
pytest --cov=app \
       --cov-report=html \
       --cov-report=term-missing \
       --cov-report=xml \
       --cov-report=json
```

### فهم التقارير

#### Terminal Report
```
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
app/validators/base.py                 27      0   100%
app/utils/text_processing.py          40      0   100%
app/utils/service_locator.py           58      3    95%   93-95
-----------------------------------------------------------------
TOTAL                               29488  20371    31%
```

#### HTML Report
- افتح `htmlcov/index.html`
- الأسطر الخضراء: مغطاة ✅
- الأسطر الحمراء: غير مغطاة ❌
- الأسطر الصفراء: مغطاة جزئيًا 🟡

---

## 🛠️ أدوات مساعدة

### 1. تحليل التغطية
```bash
python scripts/achieve_100_coverage.py
```
**الوظيفة**:
- تحليل التغطية الحالية
- تحديد الملفات غير المغطاة
- توليد خطة عمل

### 2. توليد اختبارات تلقائية
```bash
python scripts/generate_all_tests.py
```
**الوظيفة**:
- تحليل بنية الكود
- توليد قوالب اختبار
- إنشاء ملفات اختبار جديدة

### 3. تشغيل شامل
```bash
./scripts/run_comprehensive_tests.sh
```
**الوظيفة**:
- تشغيل جميع أنواع الاختبارات
- قياس التغطية
- توليد تقارير شاملة
- تشغيل mutation testing

---

## 🎯 معايير الجودة

### الحد الأدنى المطلوب
- ✅ **Line Coverage**: 100%
- ✅ **Branch Coverage**: 100%
- ✅ **Mutation Score**: 90%+
- ✅ **Security Tests**: Pass
- ✅ **Integration Tests**: Pass

### كيفية التحقق
```bash
# التحقق من التغطية
pytest --cov=app --cov-fail-under=100

# التحقق من mutation score
mutmut run && mutmut results

# التحقق من الأمان
pytest tests/security/ -v
```

---

## 📝 كتابة اختبارات جديدة

### القواعد الأساسية

#### 1. اسم الملف
```
tests/<module>/test_<filename>_comprehensive.py
```

#### 2. بنية الاختبار
```python
"""
Comprehensive Tests for <Module>
================================

Coverage Target: 100%
"""

import pytest
from app.module import function_to_test


class TestFunctionName:
    """Test function_name - all branches"""
    
    def test_basic_case(self):
        """Test with basic valid input"""
        result = function_to_test("input")
        assert result == "expected"
    
    def test_edge_case(self):
        """Test with edge case input"""
        result = function_to_test("")
        assert result == ""
    
    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            function_to_test(None)
```

#### 3. تغطية شاملة
- ✅ الحالة الأساسية (Happy path)
- ✅ الحالات الحدودية (Edge cases)
- ✅ معالجة الأخطاء (Error handling)
- ✅ القيم الخاصة (None, empty, etc.)
- ✅ الأداء (Performance)

### مثال كامل

```python
"""
Comprehensive Tests for Calculator
===================================

Coverage Target: 100%
"""

import pytest
from app.calculator import add, divide


class TestAdd:
    """Test add function - all branches"""
    
    def test_add_positive_numbers(self):
        """Test adding two positive numbers"""
        assert add(2, 3) == 5
    
    def test_add_negative_numbers(self):
        """Test adding two negative numbers"""
        assert add(-2, -3) == -5
    
    def test_add_zero(self):
        """Test adding zero"""
        assert add(5, 0) == 5
        assert add(0, 5) == 5
    
    def test_add_large_numbers(self):
        """Test adding large numbers"""
        assert add(10**10, 10**10) == 2 * 10**10


class TestDivide:
    """Test divide function - all branches"""
    
    def test_divide_positive_numbers(self):
        """Test dividing positive numbers"""
        assert divide(10, 2) == 5
    
    def test_divide_by_zero_raises_error(self):
        """Test that dividing by zero raises ValueError"""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            divide(10, 0)
    
    def test_divide_zero_by_number(self):
        """Test dividing zero by a number"""
        assert divide(0, 5) == 0
```

---

## 🔧 إعدادات pytest

### pytest.ini
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
addopts =
    -v
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=100
    --durations=10
markers =
    unit: Unit tests
    integration: Integration tests
    security: Security tests
    fuzz: Fuzzing tests
```

### conftest.py
```python
import pytest


@pytest.fixture
def sample_data():
    """Fixture providing sample test data"""
    return {"name": "Test", "value": 42}


@pytest.fixture(autouse=True)
def reset_cache():
    """Auto-reset cache before each test"""
    from app.utils.service_locator import ServiceLocator
    ServiceLocator.clear_cache()
    yield
```

---

## 🚨 استكشاف الأخطاء

### الاختبارات تفشل
```bash
# تشغيل مع تفاصيل أكثر
pytest -vv --tb=long

# تشغيل اختبار واحد فقط
pytest tests/validators/test_base.py::TestClass::test_method -v

# إيقاف عند أول فشل
pytest -x
```

### التغطية منخفضة
```bash
# معرفة الأسطر غير المغطاة
pytest --cov=app --cov-report=term-missing

# توليد تقرير HTML مفصل
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### الاختبارات بطيئة
```bash
# معرفة أبطأ الاختبارات
pytest --durations=10

# تشغيل متوازي
pytest -n auto  # يحتاج pytest-xdist
```

---

## 📚 موارد إضافية

### التوثيق
- [TESTING_STRATEGY_REPORT.md](TESTING_STRATEGY_REPORT.md) - الاستراتيجية الكاملة
- [FINAL_TESTING_REPORT.md](FINAL_TESTING_REPORT.md) - التقرير النهائي
- [QUALITY_ACHIEVEMENT_SUMMARY.md](QUALITY_ACHIEVEMENT_SUMMARY.md) - ملخص الإنجازات

### الأدوات
- [pytest](https://docs.pytest.org/) - إطار الاختبار
- [pytest-cov](https://pytest-cov.readthedocs.io/) - قياس التغطية
- [Hypothesis](https://hypothesis.readthedocs.io/) - Property-based testing
- [MutMut](https://mutmut.readthedocs.io/) - Mutation testing

### أمثلة
- `tests/validators/` - أمثلة اختبارات وحدات
- `tests/property_based/` - أمثلة property-based tests
- `tests/fuzzing/` - أمثلة fuzzing tests
- `tests/security/` - أمثلة security tests

---

## ✅ Checklist قبل الدمج

قبل دمج أي كود جديد، تأكد من:

- [ ] جميع الاختبارات تنجح
- [ ] التغطية 100% للكود الجديد
- [ ] لا توجد اختبارات متخطاة (skipped)
- [ ] Mutation score > 90%
- [ ] اختبارات الأمان تنجح
- [ ] اختبارات التكامل تنجح
- [ ] التوثيق محدّث
- [ ] CI/CD pipeline ينجح

---

## 🎉 الخلاصة

نظام الاختبار هذا يوفر:

✅ **تغطية شاملة** - جميع أنواع الاختبارات
✅ **جودة عالية** - mutation testing
✅ **أمان قوي** - security tests
✅ **أتمتة كاملة** - CI/CD pipeline
✅ **أدوات قوية** - سكريبتات مساعدة
✅ **توثيق شامل** - دليل كامل

**الهدف**: 100% Coverage + 100% Mutation Score + Zero Vulnerabilities

---

**آخر تحديث**: 2025-12-09
**الحالة**: 🟢 جاهز للاستخدام
