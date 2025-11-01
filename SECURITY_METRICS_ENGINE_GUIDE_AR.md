# 🚀 محرك المقاييس والتحليلات الأمنية

## نظرة عامة

محرك المقاييس والتحليلات الأمنية هو نظام تحليل أمني عالمي مستوحى من منصات الأمان في Google و Meta و Microsoft و OpenAI و Apple و Amazon. يوفر خوارزميات متقدمة لتسجيل المخاطر والتحليلات التنبؤية وكشف الشذوذات وإعداد التقارير الأمنية الشاملة.

## 🎯 المميزات الرئيسية

### 1. **تسجيل المخاطر المتقدم (نمط FAANG)**
- حساب المخاطر متعدد العوامل باستخدام الخطورة والعمر والتعرض ومضاعفات CWE
- أوزان الخطورة مستوحاة من CVSS
- تحليل التعرض على أساس المسارات (api/, auth/, admin/ = تعرض أعلى)
- تضخيم العمر (النتائج القديمة تحمل مخاطر أعلى)
- درجات مخاطر موحدة من 0-100

### 2. **التحليلات التنبؤية**
- التنبؤ بالمخاطر المستقبلية باستخدام الانحدار الخطي
- تسجيل الثقة باستخدام منهجية R²
- تصنيف الاتجاه (متدهور، محسّن، مستقر)
- أفق تنبؤ قابل للتكوين (افتراضي: 30 يومًا)

### 3. **كشف الشذوذات**
- كشف الشذوذات الإحصائية باستخدام Z-Score
- عتبة قابلة للتكوين (افتراضي: انحرافان معياريان)
- تحليل متعدد المقاييس (النتائج الحرجة، النتائج الجديدة، أوقات الإصلاح، معدل الإيجابيات الكاذبة)
- تصنيف الخطورة (عالي، متوسط)

### 4. **تسجيل أداء المطورين**
- اللعبنة مع درجات حرفية (A+ إلى F)
- نظام عقوبات مرجح على أساس الخطورة
- نظام مكافأة/عقوبة الوقت إلى الإصلاح
- تتبع معدل الإصلاح
- بطاقات أداء فردية للمطورين

### 5. **حساب الدين الأمني**
- تحليل التأثير المالي بالدولار الأمريكي
- تقدير التكلفة على أساس الوقت
- مضاعف العمر للدين التقني
- تفصيل على أساس الخطورة
- حساب الوقت المقدر للإصلاح

### 6. **تحليل الاتجاهات**
- حسابات المتوسط المتحرك (7 أيام و30 يومًا)
- مقاييس السرعة والتقلب
- تحديد اتجاه الاتجاه
- المقارنة التاريخية

## 📊 نماذج البيانات

### SecurityFinding (نتيجة أمنية)

يمثل نتيجة أمنية واحدة من تحليل الكود.

```python
@dataclass
class SecurityFinding:
    id: str                          # المعرف الفريد
    severity: str                    # CRITICAL, HIGH, MEDIUM, LOW, INFO
    rule_id: str                     # قاعدة الأمان التي تم تشغيلها
    file_path: str                   # موقع الملف
    line_number: int                 # رقم السطر في الملف
    message: str                     # وصف النتيجة
    cwe_id: Optional[str]            # معرف CWE (مثل CWE-89)
    owasp_category: Optional[str]    # فئة OWASP
    first_seen: datetime             # وقت الاكتشاف الأول
    last_seen: datetime              # آخر وقت تم رؤيته
    false_positive: bool             # علامة إيجابية كاذبة
    fixed: bool                      # حالة الإصلاح
    fix_time_hours: Optional[float]  # الوقت المستغرق للإصلاح
    developer_id: Optional[str]      # المطور المسؤول
```

### SecurityMetrics (المقاييس الأمنية)

لقطة شاملة للمقاييس الأمنية.

```python
@dataclass
class SecurityMetrics:
    # المقاييس في الوقت الفعلي
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    
    # مقاييس السرعة
    findings_per_1000_loc: float
    new_findings_last_24h: int
    fixed_findings_last_24h: int
    
    # مقاييس الجودة
    false_positive_rate: float
    mean_time_to_detect: float
    mean_time_to_fix: float
    
    # مقاييس المخاطر
    overall_risk_score: float
    security_debt_score: float
    trend_direction: str
    
    # مقاييس الفريق
    findings_per_developer: Dict[str, int]
    fix_rate_per_developer: Dict[str, float]
    
    timestamp: datetime
```

## 🔧 أمثلة الاستخدام

### تسجيل المخاطر الأساسي

```python
from datetime import datetime, timedelta
from app.services.security_metrics_engine import (
    SecurityFinding,
    SecurityMetricsEngine
)

# إنشاء المحرك
engine = SecurityMetricsEngine()

# إنشاء نتائج عينة
findings = [
    SecurityFinding(
        id="1",
        severity="CRITICAL",
        rule_id="sql-injection",
        file_path="app/api/routes.py",
        line_number=45,
        message="ثغرة حقن SQL",
        cwe_id="CWE-89",
        developer_id="dev_001",
        first_seen=datetime.now() - timedelta(days=15)
    ),
    SecurityFinding(
        id="2",
        severity="HIGH",
        rule_id="hardcoded-secret",
        file_path="app/config.py",
        line_number=12,
        message="مفتاح API مشفر",
        cwe_id="CWE-798",
        developer_id="dev_002",
        first_seen=datetime.now() - timedelta(days=5),
        fixed=True,
        fix_time_hours=24.0
    )
]

# حساب درجة المخاطر
risk_score = engine.calculate_advanced_risk_score(
    findings,
    code_metrics={'lines_of_code': 50000, 'public_endpoints': 25}
)
print(f"درجة المخاطر: {risk_score}/100")
```

### توليد تقرير شامل

```python
# توليد تقرير تحليل كامل
report = engine.generate_comprehensive_report(
    findings,
    code_metrics={'lines_of_code': 50000, 'public_endpoints': 25},
    hourly_rate=100.0
)

# الوصول إلى أقسام التقرير
print(f"إجمالي النتائج: {report['summary']['total_findings']}")
print(f"مستوى المخاطر: {report['risk_analysis']['risk_level']}")
print(f"الدين الأمني: ${report['security_debt']['total_debt_usd']}")
print(f"التوصيات: {report['recommendations']}")
```

### التحليلات التنبؤية

```python
from app.services.security_metrics_engine import SecurityMetrics

# إنشاء مقاييس تاريخية (30 يومًا)
historical_metrics = []
for i in range(30):
    historical_metrics.append(
        SecurityMetrics(
            total_findings=10 - i // 10,
            critical_count=max(0, 3 - i // 10),
            high_count=4,
            medium_count=2,
            low_count=1,
            findings_per_1000_loc=1.0,
            new_findings_last_24h=1,
            fixed_findings_last_24h=2,
            false_positive_rate=0.05,
            mean_time_to_detect=2.0,
            mean_time_to_fix=20.0,
            overall_risk_score=70.0 - i * 2,
            security_debt_score=50.0,
            trend_direction='IMPROVING',
            findings_per_developer={},
            fix_rate_per_developer={}
        )
    )

# التنبؤ بالمخاطر المستقبلية
prediction = engine.predict_future_risk(historical_metrics, days_ahead=30)
print(f"المخاطر المتوقعة: {prediction['predicted_risk']}/100")
print(f"الثقة: {prediction['confidence']}%")
print(f"الاتجاه: {prediction['trend']}")
```

### كشف الشذوذات

```python
# المقاييس الحالية
current = SecurityMetrics(
    total_findings=50,
    critical_count=30,
    high_count=10,
    medium_count=5,
    low_count=5,
    findings_per_1000_loc=1.0,
    new_findings_last_24h=45,
    fixed_findings_last_24h=0,
    false_positive_rate=0.1,
    mean_time_to_detect=1.0,
    mean_time_to_fix=100.0,
    overall_risk_score=95.0,
    security_debt_score=90.0,
    trend_direction='DEGRADING',
    findings_per_developer={},
    fix_rate_per_developer={}
)

# كشف الشذوذات
anomalies = engine.detect_anomalies(
    current,
    historical_metrics,
    threshold_std=2.0
)

for anomaly in anomalies:
    print(f"شذوذ: {anomaly['metric']}")
    print(f"  الحالي: {anomaly['current_value']}")
    print(f"  المتوقع: {anomaly['expected_value']}")
    print(f"  Z-Score: {anomaly['z_score']}")
    print(f"  الخطورة: {anomaly['severity']}")
```

### تتبع أداء المطورين

```python
# حساب درجة أمان المطور
dev_score = engine.calculate_developer_security_score(
    findings,
    developer_id="dev_001"
)

print(f"المطور: {dev_score['developer_id']}")
print(f"درجة الأمان: {dev_score['security_score']}/100")
print(f"الدرجة: {dev_score['grade']}")
print(f"النتائج المقدمة: {dev_score['findings_introduced']}")
print(f"النتائج المصلحة: {dev_score['findings_fixed']}")
print(f"معدل الإصلاح: {dev_score['fix_rate']}%")
```

### تحليل الدين الأمني

```python
# حساب الدين الأمني
debt = engine.calculate_security_debt(
    findings,
    hourly_rate=100.0
)

print(f"إجمالي الدين الأمني: ${debt['total_debt_usd']}")
print(f"الوقت المقدر للإصلاح: {debt['estimated_fix_time_hours']} ساعة")
print(f"الدين حسب الخطورة:")
for severity, amount in debt['debt_by_severity'].items():
    print(f"  {severity}: ${amount}")
```

### تحليل الاتجاهات

```python
# تحليل الاتجاهات الأمنية
trends = engine.analyze_trends(
    historical_metrics,
    window_days=30
)

print(f"المخاطر الحالية: {trends['current_risk']}/100")
print(f"المتوسط المتحرك 7 أيام: {trends['ma_7_days']}")
print(f"المتوسط المتحرك 30 يومًا: {trends['ma_30_days']}")
print(f"السرعة: {trends['velocity']}")
print(f"التقلب: {trends['volatility']}")
print(f"الاتجاه: {trends['trend']}")
```

## 📈 تفاصيل الخوارزميات

### 1. صيغة تسجيل المخاطر المتقدمة

```
المخاطر = Σ(الخطورة × العمر × التعرض × مضاعف_CWE) / عامل_التطبيع

حيث:
- الخطورة: الوزن على أساس خطورة النتيجة (CRITICAL=10، HIGH=7.5، إلخ.)
- العمر: 1 + (أيام_القدم / 30)، محدود عند 5x
- التعرض: على أساس مسار الملف (api/auth/admin = 1.5x، tests = 0.5x)
- مضاعف_CWE: مضاعف المخاطر لأنواع CWE المحددة
- عامل_التطبيع: يقيس إلى نطاق 0-100
```

### 2. الانحدار الخطي (التحليلات التنبؤية)

```
المخاطر_المستقبلية = الميل × x_المستقبل + التقاطع

حيث:
- الميل = Σ((x - x_mean) × (y - y_mean)) / Σ((x - x_mean)²)
- التقاطع = y_mean - الميل × x_mean
- الثقة = R² × 100
```

### 3. كشف الشذوذات بـ Z-Score

```
Z = (القيمة_الحالية - المتوسط) / الانحراف_المعياري

شذوذ إذا |Z| > العتبة (افتراضي: 2.0)
```

### 4. درجة أمان المطور

```
الدرجة = 100 - Σ(أوزان_الخطورة × النتائج_غير_المصلحة) + مكافأة_الوقت

الدرجات:
- A+: 90-100
- A:  80-89
- B:  70-79
- C:  60-69
- F:  0-59
```

### 5. الدين الأمني

```
الدين = Σ(وقت_الإصلاح × معدل_الساعة × مضاعف_العمر)

حيث:
- وقت_الإصلاح: الساعات المقدرة على أساس الخطورة
- مضاعف_العمر: 1 + (أيام_القدم / 365)
```

## 🎨 مضاعفات مخاطر CWE

يتضمن المحرك مضاعفات خاصة للثغرات الأمنية الشائعة:

| معرف CWE | نوع الثغرة | المضاعف |
|---------|-----------|---------|
| CWE-89 | حقن SQL | 2.0x |
| CWE-79 | البرمجة النصية عبر المواقع (XSS) | 1.8x |
| CWE-798 | بيانات الاعتماد المشفرة | 2.5x |
| CWE-327 | التشفير المكسور | 1.5x |
| CWE-22 | اجتياز المسار | 1.7x |

## 🔍 أنماط عامل التعرض

### تعرض عالٍ (مضاعف 1.5x)
- `api/` - نقاط نهاية API
- `routes/` - معالجات المسار
- `views/` - وحدات تحكم العرض
- `controllers/` - وحدات التحكم
- `auth/` - المصادقة
- `login` - وظيفة تسجيل الدخول
- `admin/` - واجهات الإدارة

### تعرض منخفض (مضاعف 0.5x)
- `test_` - ملفات الاختبار
- `tests/` - دلائل الاختبار
- `migrations/` - ترحيلات قاعدة البيانات
- `scripts/` - البرامج النصية المساعدة

## 🧪 الاختبار

يتضمن المحرك 29 اختبارًا شاملاً تغطي:

- إنشاء نماذج البيانات والتحقق من صحتها
- جميع الخوارزميات الستة مع الحالات الحدية
- سير عمل التكامل
- كشف الشذوذات مع سيناريوهات مختلفة
- تسجيل المطورين مع درجات مختلفة
- حسابات الدين الأمني
- تحليل الاتجاهات مع البيانات التاريخية

تشغيل الاختبارات:
```bash
pytest tests/test_security_metrics_engine.py -v
```

## 🌟 أفضل الممارسات

1. **المراقبة المنتظمة**: قم بتشغيل التحليل يوميًا أو بعد كل commit
2. **التتبع التاريخي**: احتفظ بـ 30 يومًا على الأقل من المقاييس للاتجاهات
3. **ضبط العتبة**: اضبط عتبة كشف الشذوذات بناءً على حجم الفريق والنشاط
4. **مشاركة المطورين**: استخدم درجات اللعبنة لتشجيع الوعي الأمني
5. **إدارة الديون**: تتبع الدين الأمني إلى جانب الدين التقني
6. **تحديد الأولويات**: ركز على النتائج الحرجة والعالية أولاً
7. **إدارة الإيجابيات الكاذبة**: ضع علامة على الإيجابيات الكاذبة لتحسين الدقة

## 🚀 حالات الاستخدام المتقدمة

### 1. تكامل CI/CD
قم بالتكامل في خط أنابيب CI/CD الخاص بك لتتبع الأمان بمرور الوقت:
```bash
python -m app.services.security_metrics_engine > security_report.json
```

### 2. تصور لوحة المعلومات
قم بتغذية إخراج JSON إلى أدوات التصور مثل Grafana أو لوحات المعلومات المخصصة.

### 3. تنبيهات Slack/البريد الإلكتروني
قم بإعداد تنبيهات عند اكتشاف الشذوذات أو عندما تتجاوز درجات المخاطر العتبات.

### 4. لوحات المتصدرين للفريق
استخدم درجات المطورين لإنشاء منافسة ودية ووعي أمني.

### 5. تخطيط Sprint
استخدم حسابات الدين الأمني لتخطيط sprints المركزة على الأمان.

## 📚 المراجع

هذا التطبيق مستوحى من:
- مركز قيادة الأمان من Google
- منصة الأمان من Meta
- AWS GuardDuty ML
- كشف الشذوذات من DataDog
- الدين التقني من SonarQube
- الأمان المتقدم من GitHub

## 🤝 المساهمة

لتوسيع المحرك:
1. أضف مضاعفات CWE جديدة في `cwe_risk_multipliers`
2. أضف أنماط تعرض جديدة في `_calculate_exposure_factor`
3. قم بإنشاء قواعد توصية جديدة في `_generate_recommendations`
4. أضف اختبارات للوظائف الجديدة

## 📝 الترخيص

جزء من مشروع CogniForge.

---

**تم البناء بـ ❤️ لجعل الأمان قابلاً للقياس وقابلاً للتنفيذ**
