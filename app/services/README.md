# Business Services Layer | طبقة خدمات الأعمال

> **الغرض:** منطق الأعمال وخدمات Domain  
> **Purpose:** Business logic and domain services

---

## 📋 Overview | نظرة عامة

هذا المجلد يحتوي على **خدمات الأعمال** (Business Services) التي تحتوي على منطق الأعمال الأساسي للنظام.  
كل خدمة مسؤولة عن domain محدد وتطبق مبدأ Single Responsibility.

This directory contains the **business services layer** that implements the core business logic.  
Each service is responsible for a specific domain and follows the Single Responsibility Principle.

---

## 🏗️ Architecture Principles | المبادئ المعمارية

### Clean Architecture Layers | طبقات البنية النظيفة

```
┌─────────────────────────────────────┐
│   API Layer (Presentation)         │ ← FastAPI routers
│   app/api/routers/                 │
└─────────────────────────────────────┘
            ↓ Uses
┌─────────────────────────────────────┐
│   Boundary Services (Facades)      │ ← Interface adapters
│   app/services/boundaries/         │
└─────────────────────────────────────┘
            ↓ Delegates to
┌─────────────────────────────────────┐
│   Business Services (Logic)        │ ← THIS LAYER
│   app/services/                    │
└─────────────────────────────────────┘
            ↓ Uses
┌─────────────────────────────────────┐
│   Core Infrastructure              │ ← Database, AI, etc.
│   app/core/                        │
└─────────────────────────────────────┘
```

### Key Principles | المبادئ الرئيسية

1. **Single Responsibility** - كل service مسؤول عن domain واحد فقط
2. **Dependency Inversion** - Services تعتمد على abstractions
3. **Open/Closed** - مفتوحة للتوسع، مغلقة للتعديل
4. **Interface Segregation** - Interfaces صغيرة ومحددة
5. **Liskov Substitution** - يمكن استبدال implementations

---

## 📦 Services Directory Structure | هيكل مجلد الخدمات

```
app/services/
│
├── boundaries/              # Facade services (API adapters)
│   ├── admin_chat_boundary_service.py
│   ├── auth_boundary_service.py
│   ├── crud_boundary_service.py
│   └── observability_boundary_service.py
│
├── admin/                   # Admin-specific services
│   ├── service.py           # Admin business logic
│   └── streaming/           # Streaming services
│
├── chat/                    # Chat services
│   ├── service.py           # Chat orchestration
│   └── handlers/            # Message handlers
│
├── users/                   # User management
│   ├── service.py           # User CRUD operations
│   └── repository.py        # User data access
│
├── overmind/                # AI/Overmind services
│   ├── orchestrator.py      # Task orchestration
│   ├── executor.py          # Task execution
│   ├── capabilities.py      # AI capabilities
│   ├── knowledge.py         # Knowledge management
│   └── database_tools/      # Database manipulation
│
├── agent_tools/             # Agent tool services
│   ├── core.py              # Tool registry
│   ├── fs_tools.py          # File system tools
│   └── search_tools.py      # Search tools
│
├── observability/           # Observability services
│   ├── metrics/             # Metrics collection
│   ├── tracing/             # Distributed tracing
│   └── aiops/               # AI-powered operations
│
├── data_mesh/               # Data mesh services
│   ├── domain/              # Data domain models
│   └── application/         # Data applications
│
└── system/                  # System-level services
    ├── health.py            # Health checks
    └── monitoring.py        # System monitoring
```

---

## 🎯 Service Categories | تصنيفات الخدمات

### 1. Boundary Services | خدمات الحدود
**المجلد:** `boundaries/`  
**الغرض:** Facade pattern - واجهة موحدة للـ API layer

**الخصائص:**
- ✅ تجميع operations من عدة services
- ✅ تحويل البيانات للـ API schemas
- ✅ معالجة الأخطاء والـ validation
- ✅ لا business logic معقد

**مثال:**
```python
class AdminChatBoundaryService:
    """Facade for admin chat operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chat_service = ChatService(db)
        self.history_service = HistoryService(db)
    
    async def orchestrate_chat_stream(
        self, user_id: int, question: str, ...
    ):
        """Orchestrate chat streaming - delegates to services."""
        # Coordinate multiple services
        history = await self.history_service.get_history(user_id)
        response = await self.chat_service.stream_response(question, history)
        await self.history_service.save_message(user_id, question, response)
        return response
```

---

### 2. Domain Services | خدمات Domain
**المجلدات:** `users/`, `chat/`, `admin/`, etc.  
**الغرض:** Business logic لـ domain محدد

**الخصائص:**
- ✅ منطق الأعمال الأساسي
- ✅ Domain models manipulation
- ✅ Business rules enforcement
- ✅ Transaction management

**مثال:**
```python
class UserService:
    """User domain service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)
    
    async def create_user(
        self, email: str, password: str, name: str
    ) -> User:
        """Create new user with business rules."""
        # Business rule: email must be unique
        if await self.repository.exists_by_email(email):
            raise ValueError("Email already exists")
        
        # Business rule: password must be strong
        if len(password) < 8:
            raise ValueError("Password too weak")
        
        # Create user
        hashed_password = hash_password(password)
        user = User(email=email, password=hashed_password, name=name)
        
        # Save and publish event
        user = await self.repository.save(user)
        await self.publish_event(UserCreatedEvent(user))
        
        return user
```

---

### 3. Infrastructure Services | خدمات البنية التحتية
**المجلدات:** `observability/`, `data_mesh/`, `system/`  
**الغرض:** خدمات تقنية للنظام

**الخصائص:**
- ✅ Metrics and monitoring
- ✅ Logging and tracing
- ✅ Health checks
- ✅ System utilities

**مثال:**
```python
class HealthService:
    """System health check service."""
    
    async def check_database(self) -> HealthStatus:
        """Check database connectivity."""
        try:
            async with get_db() as db:
                await db.execute(select(1))
            return HealthStatus.HEALTHY
        except Exception as e:
            logger.error(f"Database unhealthy: {e}")
            return HealthStatus.UNHEALTHY
```

---

### 4. Overmind Services | خدمات Overmind
**المجلد:** `overmind/`  
**الغرض:** AI orchestration and intelligent operations

**المكونات:**
- `orchestrator.py` - تنسيق المهام
- `executor.py` - تنفيذ المهام
- `capabilities.py` - قدرات الذكاء الاصطناعي
- `knowledge.py` - إدارة المعرفة
- `database_tools/` - أدوات قاعدة البيانات

**مثال:**
```python
class OvermindOrchestrator:
    """AI task orchestration service."""
    
    async def execute_mission(self, mission: Mission) -> MissionResult:
        """Execute AI mission with intelligent orchestration."""
        # Analyze mission requirements
        tasks = await self.plan_tasks(mission)
        
        # Execute tasks in parallel/sequential
        results = await self.execute_tasks(tasks)
        
        # Aggregate and analyze results
        return await self.aggregate_results(results)
```

---

## 🔧 Service Implementation Patterns | أنماط تطبيق الخدمات

### Pattern 1: Repository Pattern
**الاستخدام:** للوصول إلى البيانات

```python
class UserRepository:
    """User data access layer."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return await self.db.get(User, user_id)
    
    async def save(self, user: User) -> User:
        """Save user to database."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
```

### Pattern 2: Service Layer Pattern
**الاستخدام:** لمنطق الأعمال

```python
class OrderService:
    """Order business logic."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.inventory_service = InventoryService(db)
    
    async def place_order(self, order: Order) -> Order:
        """Place order with business rules."""
        # Check inventory
        if not await self.inventory_service.check_availability(order.items):
            raise InsufficientInventoryError()
        
        # Apply business rules
        order.total = self.calculate_total(order)
        
        # Save order
        order = await self.order_repo.save(order)
        
        # Update inventory
        await self.inventory_service.reserve(order.items)
        
        return order
```

### Pattern 3: Facade Pattern
**الاستخدام:** لتبسيط واجهة معقدة

```python
class PaymentFacade:
    """Simplified payment interface."""
    
    def __init__(self, db: AsyncSession):
        self.payment_service = PaymentService(db)
        self.billing_service = BillingService(db)
        self.notification_service = NotificationService(db)
    
    async def process_payment(
        self, order_id: int, payment_method: str
    ) -> PaymentResult:
        """Process payment with all related operations."""
        # Process payment
        payment = await self.payment_service.process(order_id, payment_method)
        
        # Generate invoice
        invoice = await self.billing_service.generate_invoice(order_id)
        
        # Send notification
        await self.notification_service.send_payment_confirmation(payment)
        
        return PaymentResult(payment, invoice)
```

---

## 🧪 Testing Services | اختبار الخدمات

### Unit Testing
اختبار service بشكل معزول:

```python
async def test_user_service_create_user():
    """Test user creation."""
    # Arrange
    db = AsyncMock()
    service = UserService(db)
    
    # Act
    user = await service.create_user(
        email="test@example.com",
        password="secure123",
        name="Test User"
    )
    
    # Assert
    assert user.email == "test@example.com"
    assert user.name == "Test User"
```

### Integration Testing
اختبار service مع dependencies حقيقية:

```python
async def test_user_service_integration(db_session):
    """Test user service with real database."""
    service = UserService(db_session)
    
    # Create user
    user = await service.create_user(
        email="test@example.com",
        password="secure123",
        name="Test User"
    )
    
    # Verify in database
    saved_user = await service.get_user(user.id)
    assert saved_user.email == "test@example.com"
```

---

## 📚 Best Practices | أفضل الممارسات

### 1. Single Responsibility
كل service مسؤول عن domain واحد فقط:
```python
# Good ✅
class UserService:
    """User management only."""
    pass

class OrderService:
    """Order management only."""
    pass

# Bad ❌
class UserOrderService:
    """Handles both users and orders - too broad."""
    pass
```

### 2. Dependency Injection
استخدام DI بدلاً من hard-coded dependencies:
```python
# Good ✅
class Service:
    def __init__(self, db: AsyncSession, config: Settings):
        self.db = db
        self.config = config

# Bad ❌
class Service:
    def __init__(self):
        self.db = create_engine(...)  # Hard-coded
        self.config = load_config()   # Hard-coded
```

### 3. Interface Segregation
interfaces صغيرة ومحددة:
```python
# Good ✅
class IUserReader(Protocol):
    async def get_user(self, user_id: int) -> User: ...

class IUserWriter(Protocol):
    async def save_user(self, user: User) -> User: ...

# Bad ❌
class IUserService(Protocol):
    async def get_user(self, user_id: int) -> User: ...
    async def save_user(self, user: User) -> User: ...
    async def delete_user(self, user_id: int) -> None: ...
    # ... 20 more methods
```

### 4. Error Handling
معالجة الأخطاء بشكل صحيح:
```python
# Good ✅
async def get_user(self, user_id: int) -> User:
    try:
        user = await self.repository.get(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise ServiceError("Failed to retrieve user") from e

# Bad ❌
async def get_user(self, user_id: int):
    try:
        return await self.repository.get(user_id)
    except:  # Catching all exceptions
        return None  # Silent failure
```

---

## 📖 Related Documentation | الوثائق ذات الصلة

### Architecture
- [Clean Architecture Guide](../../docs/architecture/)
- [Service Layer Audit](../../docs/architecture/SERVICE_LAYER_AUDIT.md)
- [Domain Model](../../docs/architecture/01_domain_model.md)

### Patterns
- [Repository Pattern](../../docs/patterns/repository.md)
- [Service Layer Pattern](../../docs/patterns/service_layer.md)
- [Facade Pattern](../../docs/patterns/facade.md)

### Testing
- [Testing Guide](../../TESTING_GUIDE.md)
- [Service Testing](../../docs/testing/service_testing.md)

---

## 🤝 Contributing | المساهمة

### قبل إضافة service جديد:
1. ✅ تأكد أنه domain service (ليس infrastructure)
2. ✅ اتبع Single Responsibility
3. ✅ استخدم Dependency Injection
4. ✅ أضف type hints كاملة
5. ✅ اكتب unit tests
6. ✅ اكتب integration tests
7. ✅ وثّق في docstrings

### Code Review Checklist
- [ ] Service has single responsibility?
- [ ] Dependencies are injected?
- [ ] Type hints are complete?
- [ ] Error handling is proper?
- [ ] Tests are written?
- [ ] Documentation is clear?

---

**Last Updated:** 2026-01-03  
**Version:** 2.0  
**Maintainer:** CogniForge Team
