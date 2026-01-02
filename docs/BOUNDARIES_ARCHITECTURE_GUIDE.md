# دليل بنية Boundaries | Boundaries Architecture Guide

**التاريخ:** 2026-01-02  
**النسخة:** 1.0  
**الحالة:** ✅ موثق

---

## 🎯 الهدف | Purpose

توضيح الفرق بين **الأنماط المعمارية العامة** في `app/boundaries/` و**التطبيقات المحددة** في `app/services/boundaries/`.

---

## 📊 نظرة عامة | Overview

المشروع يحتوي على مستويين من Boundaries:

```
app/
├── boundaries/                    # 🎨 Abstract Patterns (Generic)
│   ├── service_boundaries.py      # Circuit Breaker, Events
│   ├── data_boundaries.py         # Repository, UnitOfWork
│   └── policy_boundaries.py       # Access Control, Policies
│
└── services/
    └── boundaries/                # 🔧 Concrete Services (Specific)
        ├── admin_chat_boundary_service.py
        ├── auth_boundary_service.py
        ├── crud_boundary_service.py
        └── observability_boundary_service.py
```

### التشبيه | Analogy

فكر في الأمر كـ:
- **`app/boundaries/`**: مثل المكتبة القياسية (stdlib) - أدوات عامة قابلة لإعادة الاستخدام
- **`app/services/boundaries/`**: مثل application code - تطبيقات محددة لمشاكل محددة

---

## 🎨 app/boundaries/ - Abstract Patterns

### الغرض | Purpose

**أنماط معمارية عامة** (Design Patterns) قابلة لإعادة الاستخدام في أي مشروع.

### الخصائص | Characteristics

- ✅ **Generic**: لا تعرف شيئاً عن domain محدد
- ✅ **Reusable**: يمكن استخدامها في أي مشروع
- ✅ **Abstract**: توفر interfaces وأنماط عامة
- ✅ **Framework-like**: مثل building blocks

### المكونات | Components

#### 1. ServiceBoundary (service_boundaries.py)

**الغرض:** Circuit Breaker pattern + Domain Events

```python
from app.boundaries import ServiceBoundary, get_service_boundary

# Create generic service boundary
service = ServiceBoundary("payment_service")

# Circuit breaker - automatic failure handling
@service.circuit_breaker(max_failures=3)
async def process_payment(amount: float):
    # If this fails 3 times, circuit opens
    ...

# Domain events
@service.on_event(EventType.PAYMENT_COMPLETED)
async def handle_payment(event: DomainEvent):
    # React to events
    ...
```

**الاستخدامات:**
- ✅ Tests: `tests/test_separation_of_concerns.py`
- ✅ Scripts: `scripts/cs61_simplify.py`
- 🔄 Future: يمكن استخدامها لخدمات جديدة

#### 2. DataBoundary (data_boundaries.py)

**الغرض:** Repository pattern + Unit of Work

```python
from app.boundaries import RepositoryBoundary, UnitOfWork

# Generic repository
class UserRepository(RepositoryBoundary[User]):
    async def find_by_email(self, email: str) -> User | None:
        ...

# Unit of Work pattern
async with UnitOfWork() as uow:
    user = await uow.users.create(...)
    await uow.orders.create(...)
    await uow.commit()  # Atomic operation
```

**الاستخدامات:**
- ✅ Pattern definition للاستخدام المستقبلي
- 🔄 يمكن تطبيقها على repositories جديدة

#### 3. PolicyBoundary (policy_boundaries.py)

**الغرض:** Access Control + Policy Enforcement

```python
from app.boundaries import PolicyBoundary, PolicyDecision

# Generic policy
policy = PolicyBoundary("admin_access")

# Check access
decision = await policy.evaluate(
    subject="user:123",
    action="delete",
    resource="post:456"
)

if decision == PolicyDecision.ALLOW:
    # Proceed
    ...
```

**الاستخدامات:**
- ✅ Pattern definition للاستخدام المستقبلي
- 🔄 يمكن تطبيقها على features جديدة

### متى تستخدم app/boundaries/ | When to Use

استخدم `app/boundaries/` عندما:
- ✅ تريد تطبيق pattern معماري عام
- ✅ تحتاج circuit breaker أو retry logic
- ✅ تريد domain events system
- ✅ تحتاج repository pattern
- ✅ تريد policy-based access control

**مثال:**
```python
# إضافة خدمة جديدة مع circuit breaker
from app.boundaries import ServiceBoundary

notification_service = ServiceBoundary("notification")

@notification_service.circuit_breaker(max_failures=5)
async def send_email(to: str, subject: str, body: str):
    # إذا فشل 5 مرات، يتوقف تلقائياً
    ...
```

---

## 🔧 app/services/boundaries/ - Concrete Services

### الغرض | Purpose

**Facade Services** محددة تنسق business logic معقد للـ API layer.

### الخصائص | Characteristics

- ✅ **Specific**: تعرف domain details (users, conversations, etc.)
- ✅ **Concrete**: تطبيقات فعلية لمشاكل محددة
- ✅ **Business-focused**: تحتوي على business rules
- ✅ **API-facing**: تستخدم مباشرة من API routers

### المكونات | Components

#### 1. AdminChatBoundaryService

**المسؤوليات:**
- تنسيق محادثات المسؤول
- إدارة sessions ورسائل
- Streaming responses
- Authentication validation

```python
from app.services.boundaries import AdminChatBoundaryService

service = AdminChatBoundaryService(db)

# Specific business logic
async for chunk in service.orchestrate_chat_stream(
    user_id=123,
    question="What is the status?",
    conversation_id=456,
    ai_client=client,
    session_factory=factory,
):
    yield chunk
```

**المُستخدم في:**
- ✅ `app/api/routers/admin.py`

#### 2. AuthBoundaryService

**المسؤوليات:**
- User registration
- Authentication (login)
- Token generation/verification
- Password hashing

```python
from app.services.boundaries import AuthBoundaryService

service = AuthBoundaryService(db)

# Specific business logic
result = await service.authenticate_user(
    email="user@example.com",
    password="secret",
    request=request,
)
```

**المُستخدم في:**
- ✅ `app/api/routers/security.py`

#### 3. CrudBoundaryService

**المسؤوليات:**
- Generic CRUD operations
- Pagination
- Filtering
- Sorting

```python
from app.services.boundaries import CrudBoundaryService

service = CrudBoundaryService(db)

# Generic CRUD
result = await service.list_items(
    resource_type="users",
    page=1,
    per_page=20,
)
```

**المُستخدم في:**
- ✅ `app/api/routers/crud.py`

#### 4. ObservabilityBoundaryService

**المسؤوليات:**
- System health monitoring
- Metrics collection
- Performance tracking
- AIOps integration

```python
from app.services.boundaries import ObservabilityBoundaryService

service = ObservabilityBoundaryService()

# System metrics
health = await service.get_system_health()
metrics = await service.get_golden_signals()
```

**المُستخدم في:**
- ✅ `app/api/routers/observability.py`

### متى تستخدم app/services/boundaries/ | When to Use

استخدم `app/services/boundaries/` عندما:
- ✅ تريد facade للـ API routers
- ✅ تحتاج تنسيق متعدد الخدمات
- ✅ تريد فصل API layer عن business logic
- ✅ تحتاج data transformation بين layers

**مثال:**
```python
# إضافة boundary service جديد
class ProductBoundaryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_service = ProductService(db)
        self.inventory_service = InventoryService(db)
    
    async def create_product_with_inventory(
        self,
        product_data: dict,
        initial_stock: int,
    ) -> dict:
        # Coordinate multiple services
        product = await self.product_service.create(product_data)
        await self.inventory_service.set_stock(product.id, initial_stock)
        return {
            "product": product.to_dict(),
            "stock": initial_stock,
        }
```

---

## 🔄 التفاعل بينهما | Interaction

### يمكن استخدامهما معاً | Can Be Combined

```python
# Concrete service using abstract pattern
from app.boundaries import ServiceBoundary
from sqlalchemy.ext.asyncio import AsyncSession

class PaymentBoundaryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Use abstract pattern for reliability
        self.boundary = ServiceBoundary("payment")
    
    async def process_payment(self, amount: float) -> dict:
        # Use circuit breaker from abstract pattern
        @self.boundary.circuit_breaker(max_failures=3)
        async def _process():
            # Specific business logic
            ...
        
        return await _process()
```

### لكن في الممارسة | But In Practice

**حالياً في CogniForge:**
- `app/boundaries/`: Patterns محددة للاستخدام المستقبلي ✨
- `app/services/boundaries/`: Services فعلية تستخدم الآن ✅

**السبب:** التبسيط - نستخدم ما نحتاج فقط.

---

## 📋 جدول مقارنة | Comparison Table

| الجانب | app/boundaries/ | app/services/boundaries/ |
|--------|----------------|-------------------------|
| **النوع** | Abstract Patterns | Concrete Services |
| **الاستخدام** | Generic, reusable | Specific to CogniForge |
| **Domain Knowledge** | ❌ لا | ✅ نعم |
| **يستخدم من** | Tests, Scripts, Future | API Routers (الآن) |
| **التعقيد** | بسيط (patterns) | معقد (business logic) |
| **التبعيات** | قليلة | كثيرة (services, models) |
| **التغيير** | نادر | متكرر |
| **الهدف** | Framework/Library | Application Code |

---

## 🎓 Best Practices

### ✅ Do

1. **استخدم app/services/boundaries/ للـ API routers**
   ```python
   # ✅ Good
   from app.services.boundaries import AdminChatBoundaryService
   service = AdminChatBoundaryService(db)
   ```

2. **استخدم app/boundaries/ للـ patterns جديدة**
   ```python
   # ✅ Good - إضافة circuit breaker لخدمة جديدة
   from app.boundaries import ServiceBoundary
   service = ServiceBoundary("new_service")
   ```

3. **احفظ app/boundaries/ بسيط وعام**
   - لا domain-specific logic
   - فقط patterns قابلة لإعادة الاستخدام

4. **احفظ app/services/boundaries/ محدد**
   - business logic واضح
   - domain models محددة

### ❌ Don't

1. **لا تخلط بينهما**
   ```python
   # ❌ Bad - استيراد من كليهما بدون سبب
   from app.boundaries import ServiceBoundary
   from app.services.boundaries import AdminChatBoundaryService
   ```

2. **لا تضع domain logic في app/boundaries/**
   ```python
   # ❌ Bad - domain-specific في abstract pattern
   class ServiceBoundary:
       async def send_admin_notification(self):  # ❌ Too specific
           ...
   ```

3. **لا تضع generic patterns في app/services/boundaries/**
   ```python
   # ❌ Bad - generic في concrete service
   class AdminChatBoundaryService:
       def create_circuit_breaker(self):  # ❌ Should be in app/boundaries/
           ...
   ```

---

## 🔮 المستقبل | Future

### خطط محتملة | Potential Plans

#### الخيار 1: الإبقاء على الانفصال ✅ (موصى به)
- `app/boundaries/`: library من patterns عامة
- `app/services/boundaries/`: application services محددة
- **الفوائد:** واضح، منظم، قابل للتوسع

#### الخيار 2: الدمج (غير موصى به)
- دمج الكل في `app/services/boundaries/`
- **المشاكل:** فقدان التنظيم، خلط بين abstract و concrete

#### الخيار 3: نقل إلى Package منفصل
- نقل `app/boundaries/` إلى package خارجي (مثل `cogniforge-patterns`)
- **الفوائد:** reusability عبر projects
- **المتطلبات:** نضج أكثر في patterns

---

## 📚 أمثلة عملية | Practical Examples

### مثال 1: إضافة خدمة جديدة

**السيناريو:** تريد إضافة Product Management API

```python
# 1. إنشاء Boundary Service في app/services/boundaries/
# File: app/services/boundaries/product_boundary_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.products import ProductService
from app.services.inventory import InventoryService

class ProductBoundaryService:
    """Facade for Product Management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.products = ProductService(db)
        self.inventory = InventoryService(db)
    
    async def create_product_with_stock(
        self,
        name: str,
        price: float,
        initial_stock: int,
    ) -> dict:
        """Create product and set initial inventory."""
        # Coordinate multiple services
        product = await self.products.create(name=name, price=price)
        await self.inventory.set_stock(product.id, initial_stock)
        
        return {
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": initial_stock,
        }

# 2. استخدامها في API Router
# File: app/api/routers/products.py

from fastapi import APIRouter, Depends
from app.services.boundaries.product_boundary_service import ProductBoundaryService

router = APIRouter(prefix="/api/products", tags=["Products"])

def get_product_service(db: AsyncSession = Depends(get_db)):
    return ProductBoundaryService(db)

@router.post("/")
async def create_product(
    data: ProductCreate,
    service: ProductBoundaryService = Depends(get_product_service),
):
    result = await service.create_product_with_stock(
        name=data.name,
        price=data.price,
        initial_stock=data.stock,
    )
    return result
```

### مثال 2: استخدام Abstract Pattern

**السيناريو:** تريد إضافة Circuit Breaker لـ external API

```python
# استخدام app/boundaries/ للـ reliability pattern
from app.boundaries import ServiceBoundary

# Create service boundary with circuit breaker
weather_api = ServiceBoundary("weather_api")

@weather_api.circuit_breaker(
    max_failures=5,
    timeout_seconds=30,
    recovery_timeout=60
)
async def get_weather(city: str) -> dict:
    """Fetch weather with automatic failure handling."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{city}")
        return response.json()

# الآن إذا فشل 5 مرات، يتوقف لمدة 60 ثانية
weather = await get_weather("Cairo")  # Protected automatically
```

---

## 🎯 الخلاصة | Conclusion

### القاعدة الذهبية | Golden Rule

```
app/boundaries/           → "What can be done?" (Patterns)
app/services/boundaries/  → "What we actually do" (Business)
```

### التذكير | Remember

- **app/boundaries/**: مكتبة من patterns - استخدمها عند الحاجة
- **app/services/boundaries/**: application code - استخدمها دائماً للـ API

### الحالة الحالية | Current State

✅ **كلاهما مستقل ولا تداخل**  
✅ **التوثيق واضح لكل منهما**  
✅ **الاستخدام متسق عبر المشروع**  

---

**Last Updated:** 2026-01-02  
**Reviewed By:** CogniForge Team  
**Status:** ✅ Documented
