# 📘 دليل إعادة الهيكلة - Playbook

## ✅ ما تم إنجازه

### الملف الأول: `api_advanced_analytics_service.py`

**قبل**:
- 636 سطر
- تعقيد: 95
- 7 مسؤوليات مختلطة
- أعلى دالة: تعقيد 21

**بعد**:
- 12 ملف منفصل
- متوسط 50-80 سطر/ملف
- تعقيد أقصى: 12
- كل كلاس مسؤولية واحدة

**النتائج**:
```
✅ 10/10 اختبارات نجحت
✅ 8/8 اختبارات OCP نجحت
✅ لا توجد دالة بتعقيد > 12
✅ جميع مبادئ SOLID مطبقة
```

---

## 🎯 الملفات المتبقية (حسب الأولوية)

### Priority 1 - حرج

1. **`security_metrics_engine.py`** (تعقيد: 76)
   - 655 سطر
   - 5 دوال معقدة
   - أعلى: 21

2. **`agent_tools/fs_tools.py`** (تعقيد: 57)
   - 544 سطر
   - 4 دوال معقدة
   - أعلى: 21

### Priority 2 - مهم

3. **`user_analytics_metrics_service.py`** (تعقيد: 55)
4. **`sre_error_budget_service.py`** (تعقيد: 39)
5. **`agent_tools/search_tools.py`** (تعقيد: 38)

---

## 📋 Playbook - خطوات التنفيذ

### Phase 1: التحليل (15 دقيقة)

```bash
# 1. تحليل التعقيد
radon cc app/services/TARGET_FILE.py -s

# 2. تحديد المسؤوليات
grep -n "^class\|^def\|^    def" app/services/TARGET_FILE.py

# 3. رسم خريطة الاعتماديات
grep -n "import\|from" app/services/TARGET_FILE.py
```

**الأسئلة الرئيسية**:
- ما هي المسؤوليات المختلفة؟
- أي دوال تعقيدها > 10؟
- ما هي الـ Domains المناسبة؟

---

### Phase 2: التصميم (20 دقيقة)

**قالب التصميم**:

```
app/NEW_DOMAIN/
├── domain/
│   ├── entities.py          # الكيانات النقية
│   ├── value_objects.py     # القيم الثابتة
│   └── interfaces.py        # الواجهات المجردة
│
├── application/
│   ├── use_case_1.py        # حالة استخدام 1
│   ├── use_case_2.py        # حالة استخدام 2
│   └── use_case_3.py        # حالة استخدام 3
│
├── infrastructure/
│   └── repository.py        # التخزين
│
└── api/
    └── facade.py            # الواجهة الموحدة
```

**قواعد التصميم**:
1. كل كلاس مسؤولية واحدة (SRP)
2. كل interface قابل للتوسع (OCP)
3. كل dependency يُحقن (DIP)
4. لا circular dependencies
5. كل دالة تعقيد < 10

---

### Phase 3: التنفيذ (60 دقيقة)

#### Step 1: Domain Layer

```python
# entities.py
@dataclass
class Entity:
    """كيان نقي - لا يعتمد على أي شيء"""
    id: str
    name: str
    # ... fields only

# interfaces.py
class Repository(Protocol):
    """واجهة التخزين"""
    def save(self, entity: Entity) -> None: ...
    def get(self, id: str) -> Entity | None: ...
```

#### Step 2: Application Layer

```python
# use_case.py
class UseCase:
    """حالة استخدام - SRP"""
    
    def __init__(self, repository: Repository):
        self.repository = repository
    
    def execute(self, data: dict) -> Result:
        """تنفيذ - تعقيد < 10"""
        # منطق بسيط ومركز
        pass
```

#### Step 3: Infrastructure Layer

```python
# repository.py
class ConcreteRepository:
    """تطبيق محدد - DIP"""
    
    def save(self, entity: Entity) -> None:
        # تفاصيل التخزين
        pass
```

#### Step 4: API Layer

```python
# facade.py
class Facade:
    """واجهة موحدة"""
    
    def __init__(
        self,
        repository: Repository,
        use_case: UseCase
    ):
        self.repository = repository
        self.use_case = use_case
    
    def operation(self, data: dict) -> Result:
        return self.use_case.execute(data)
```

---

### Phase 4: الاختبار (30 دقيقة)

```python
# test_refactored.py
class TestRepository:
    """اختبار التخزين"""
    def test_save_and_retrieve(self):
        repo = ConcreteRepository()
        entity = Entity(id="1", name="test")
        repo.save(entity)
        assert repo.get("1") == entity

class TestUseCase:
    """اختبار حالة الاستخدام"""
    def test_execute(self):
        repo = MockRepository()
        use_case = UseCase(repo)
        result = use_case.execute({"data": "test"})
        assert result.success

class TestOCP:
    """اختبار قابلية التوسع"""
    def test_can_add_new_implementation(self):
        # يمكن إضافة تطبيق جديد دون تعديل الموجود
        pass

class TestComplexity:
    """اختبار التعقيد"""
    def test_no_function_exceeds_10(self):
        result = subprocess.run(
            ["radon", "cc", "app/NEW_DOMAIN/", "-n", "C"],
            capture_output=True
        )
        assert "- C" not in result.stdout
```

---

### Phase 5: التحقق (15 دقيقة)

```bash
# 1. تشغيل الاختبارات
pytest tests/test_NEW_DOMAIN.py -v

# 2. قياس التعقيد
radon cc app/NEW_DOMAIN/ -a -s

# 3. التحقق من التغطية
pytest --cov=app/NEW_DOMAIN tests/test_NEW_DOMAIN.py

# 4. التحقق من الأنماط
mypy app/NEW_DOMAIN/
```

**معايير النجاح**:
- [ ] جميع الاختبارات تنجح
- [ ] لا توجد دالة تعقيد > 10
- [ ] Test coverage > 80%
- [ ] لا أخطاء mypy
- [ ] لا circular dependencies

---

## 🔄 مثال عملي: `security_metrics_engine.py`

### التحليل

```python
# الملف الحالي
SecurityMetricsEngine (655 سطر)
├── calculate_developer_security_score()    # 21 ⚠️
├── generate_comprehensive_report()         # 20 ⚠️
├── _generate_recommendations()             # 13 ⚠️
├── predict_future_risk()                   # 11 ⚠️
└── calculate_security_debt()               # 11 ⚠️
```

**المسؤوليات المكتشفة**:
1. حساب النقاط (Scoring)
2. توليد التقارير (Reporting)
3. التوقعات (Prediction)
4. التوصيات (Recommendations)
5. حساب الديون (Debt Calculation)

### التصميم المقترح

```
app/security_metrics/
├── domain/
│   ├── entities.py
│   │   ├── SecurityScore
│   │   ├── SecurityReport
│   │   └── SecurityDebt
│   ├── value_objects.py
│   │   ├── RiskLevel
│   │   └── SecurityMetric
│   └── interfaces.py
│       ├── ScoreCalculator
│       ├── ReportGenerator
│       └── RiskPredictor
│
├── application/
│   ├── score_calculation.py
│   │   └── DeveloperScoreCalculator
│   ├── report_generation.py
│   │   └── ComprehensiveReportGenerator
│   ├── risk_prediction.py
│   │   └── FutureRiskPredictor
│   └── debt_calculation.py
│       └── SecurityDebtCalculator
│
├── infrastructure/
│   └── metrics_repository.py
│
└── api/
    └── security_metrics_facade.py
```

### الكود المقترح

```python
# domain/entities.py
@dataclass
class SecurityScore:
    developer_id: str
    score: float
    breakdown: dict[str, float]
    timestamp: datetime

# domain/interfaces.py
class ScoreCalculator(ABC):
    @abstractmethod
    def calculate(self, data: dict) -> SecurityScore:
        pass

# application/score_calculation.py
class DeveloperScoreCalculator(ScoreCalculator):
    def calculate(self, data: dict) -> SecurityScore:
        # منطق بسيط - تعقيد < 10
        base_score = self._calculate_base_score(data)
        penalties = self._calculate_penalties(data)
        bonuses = self._calculate_bonuses(data)
        
        return SecurityScore(
            developer_id=data['developer_id'],
            score=base_score - penalties + bonuses,
            breakdown={
                'base': base_score,
                'penalties': penalties,
                'bonuses': bonuses
            },
            timestamp=datetime.now(UTC)
        )
    
    def _calculate_base_score(self, data: dict) -> float:
        # تعقيد < 10
        pass
```

---

## 📊 تتبع التقدم

### الملفات المكتملة

- [x] `api_advanced_analytics_service.py` ✅
  - التعقيد: 95 → 12 (-87%)
  - الأسطر: 636 → 50-80 (-87%)
  - الاختبارات: 18/18 ✅

### الملفات قيد العمل

- [ ] `security_metrics_engine.py`
  - التعقيد الحالي: 76
  - الهدف: < 10
  - الحالة: جاهز للبدء

### الملفات المتبقية

- [ ] `agent_tools/fs_tools.py` (57)
- [ ] `user_analytics_metrics_service.py` (55)
- [ ] `sre_error_budget_service.py` (39)
- [ ] `agent_tools/search_tools.py` (38)

---

## 🎯 الأهداف النهائية

| المقياس | الحالي | الهدف | التقدم |
|---------|--------|-------|--------|
| التعقيد الكلي | 1,602 | 400 | 6% |
| الملفات المعقدة | 78 | 0 | 1% |
| متوسط التعقيد | 13.8 | 5 | - |
| Test Coverage | 60% | 80% | - |

---

## 💡 نصائح مهمة

1. **ابدأ صغيراً**: لا تحاول إعادة هيكلة كل شيء دفعة واحدة
2. **اختبر باستمرار**: اكتب الاختبارات قبل الكود
3. **استخدم Git**: commit بعد كل خطوة ناجحة
4. **راجع التصميم**: تأكد من تطبيق SOLID قبل الكتابة
5. **قس النتائج**: استخدم radon لقياس التحسن

---

## 🚀 الخطوة التالية

```bash
# ابدأ بالملف التالي
cd /app
python refactor_next_file.py security_metrics_engine.py
```

