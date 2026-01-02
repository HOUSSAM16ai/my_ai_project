# Architectural Boundaries | الحدود المعمارية

> **الغرض:** أنماط معمارية عامة لفصل الاهتمامات وفق Clean Architecture  
> **Purpose:** Generic architectural patterns for separation of concerns following Clean Architecture

---

## 📋 Overview | نظرة عامة

هذه الوحدة تحتوي على **أنماط معمارية عامة** (Abstract Patterns) لتطبيق مبدأ الحدود في البنية النظيفة.  
This module contains **generic architectural patterns** for implementing boundaries in Clean Architecture.

### ⚠️ Important Distinction | تمييز مهم

- **هذه الوحدة:** أنماط معمارية عامة وقابلة لإعادة الاستخدام
- **`app/services/boundaries/`**: تطبيقات محددة لخدمات الأعمال

- **This module:** Generic, reusable architectural patterns
- **`app/services/boundaries/`**: Specific business service implementations

---

## 📦 Components | المكونات

### 1. Service Boundaries | حدود الخدمات
**الملف:** `service_boundaries.py`

**الغرض:**
- تطبيق نمط Circuit Breaker
- إدارة Domain Events
- عزل الخدمات عن بعضها

**الاستخدام:**
```python
from app.boundaries import ServiceBoundary, get_service_boundary

# Create service boundary
service = ServiceBoundary("user_service")

# Register event handlers
@service.on_event(EventType.USER_CREATED)
async def handle_user_created(event: DomainEvent):
    # Handle event
    pass
```

**الحالات المستخدمة:**
- ✅ `tests/test_separation_of_concerns.py` - اختبارات شاملة
- 🔄 يمكن استخدامها في تطبيقات مستقبلية

---

### 2. Data Boundaries | حدود البيانات
**الملف:** `data_boundaries.py`

**الغرض:**
- عزل البيانات بين الخدمات
- تطبيق Event Sourcing
- إدارة التناسق في البيانات الموزعة

**الاستخدام:**
```python
from app.boundaries import DataBoundary, EventSourcedAggregate

# Create data boundary
data = DataBoundary("order_service")

# Use event sourcing
aggregate = EventSourcedAggregate("order_123", "order")
await aggregate.load_from_history(event_store)
```

**الحالات المستخدمة:**
- ✅ `tests/test_separation_of_concerns.py` - اختبارات Event Sourcing
- 🔄 مُعد للاستخدام المستقبلي في Microservices

---

### 3. Policy Boundaries | حدود السياسات
**الملف:** `policy_boundaries.py`

**الغرض:**
- تطبيق سياسات الأمان والصلاحيات
- فحص الامتثال (GDPR, HIPAA, إلخ)
- تصنيف البيانات وحمايتها

**الاستخدام:**
```python
from app.boundaries import PolicyBoundary, Policy, PolicyRule, Effect

# Create policy boundary
policy_boundary = PolicyBoundary()

# Add policy
policy = Policy(
    name="admin_only",
    description="Only admins can access",
    rules=[
        PolicyRule(
            effect=Effect.ALLOW,
            principals=["role:admin"],
            actions=["read", "write"],
            resources=["*"]
        )
    ]
)
policy_boundary.add_policy(policy)

# Evaluate permission
is_allowed = await policy_boundary.is_allowed(
    principal=Principal(id="user_123", type="user", roles={"admin"}),
    action="write",
    resource="document"
)
```

**الحالات المستخدمة:**
- ✅ `tests/test_separation_of_concerns.py` - اختبارات السياسات
- 🔄 مُعد للاستخدام في نظام الصلاحيات المستقبلي

---

## 🔄 Relationship with `app/services/boundaries/`

### الفرق الرئيسي | Key Difference

```
app/boundaries/                    →  Abstract Patterns (الأنماط المجردة)
    ├── ServiceBoundary            →  Generic service boundary
    ├── DataBoundary               →  Generic data boundary
    └── PolicyBoundary             →  Generic policy boundary

app/services/boundaries/           →  Concrete Implementations (التطبيقات المحددة)
    ├── AdminChatBoundaryService   →  Specific: Admin chat operations
    ├── AuthBoundaryService        →  Specific: Authentication operations
    ├── CrudBoundaryService        →  Specific: CRUD operations
    └── ObservabilityBoundaryService → Specific: Observability operations
```

### التكامل | Integration

**لا يوجد استيراد مباشر** بين المجلدين:
- `app/boundaries/` = Abstract patterns (مستقلة)
- `app/services/boundaries/` = Concrete services (تطبيقات فعلية)

**كلاهما يطبق نفس المبادئ:**
- Separation of Concerns (فصل الاهتمامات)
- Single Responsibility (مسؤولية واحدة)
- Dependency Inversion (عكس التبعيات)

---

## 🎯 Design Principles | المبادئ التصميمية

### 1. Clean Architecture
- **Boundaries**: فصل الطبقات وعدم اعتماد الداخلي على الخارجي
- **Use Cases**: منطق الأعمال معزول عن التفاصيل التقنية
- **Entities**: نماذج المجال نظيفة وخالية من التبعيات

### 2. Domain-Driven Design (DDD)
- **Domain Events**: التواصل بين Aggregates عبر الأحداث
- **Event Sourcing**: حفظ التاريخ الكامل للتغييرات
- **Bounded Contexts**: كل خدمة لها سياق محدد

### 3. SOLID Principles
- **S**ingle Responsibility: كل boundary له مسؤولية واحدة
- **O**pen/Closed: قابل للتوسع دون تعديل
- **L**iskov Substitution: القابلية للاستبدال
- **I**nterface Segregation: واجهات محددة
- **D**ependency Inversion: التبعية على التجريد

---

## 🧪 Testing | الاختبارات

### الاختبارات الشاملة
الملف: `tests/test_separation_of_concerns.py`

**التغطية:**
- ✅ Service Boundaries (Circuit Breaker, Events)
- ✅ Data Boundaries (Event Sourcing, Consistency)
- ✅ Policy Boundaries (Policies, Compliance)
- ✅ Integration Scenarios (End-to-End)

**تشغيل الاختبارات:**
```bash
pytest tests/test_separation_of_concerns.py -v
```

---

## 🚀 Future Plans | الخطط المستقبلية

### قصيرة المدى
- [ ] استخدام ServiceBoundary في خدمات جديدة
- [ ] تطبيق PolicyBoundary في نظام الصلاحيات
- [ ] توسيع DataBoundary للمعاملات الموزعة

### طويلة المدى
- [ ] دعم Microservices Architecture
- [ ] تكامل مع Saga Pattern للمعاملات الموزعة
- [ ] نظام Policy-as-Code كامل

---

## 📚 References | المراجع

### الوثائق الداخلية
- [SIMPLIFICATION_GUIDE.md](../../SIMPLIFICATION_GUIDE.md) - دليل التبسيط
- [PROJECT_HISTORY.md](../../PROJECT_HISTORY.md) - تاريخ المشروع
- [ARCHITECTURE.md](../../docs/architecture/) - الوثائق المعمارية

### الموارد الخارجية
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design by Eric Evans](https://domainlanguage.com/ddd/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

## 🤝 Contributing | المساهمة

للمساهمة في تطوير هذه الأنماط:
1. راجع الاختبارات الموجودة
2. أضف حالات استخدام جديدة
3. حافظ على البساطة والتجريد
4. وثّق التغييرات

---

**Last Updated:** 2026-01-02  
**Status:** Stable - Tested - Ready for use  
**Maintainer:** CogniForge Team

**Built with ❤️ following Clean Architecture principles**
