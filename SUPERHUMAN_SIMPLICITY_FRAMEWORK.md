# 🎯 إطار البساطة الخارقة: دليل التطبيق الفوري

> **تطبيق عملي لمبادئ البساطة الخارقة في 72 ساعة**

---

## 📋 جدول المحتويات

1. [البوصلة العقلية](#1-البوصلة-العقلية)
2. [مبادئ التصميم الحاكمة](#2-مبادئ-التصميم-الحاكمة)
3. [الأنماط البنيوية](#3-أنماط-بنيوية-skeleton-بسيطة)
4. [القرارات التقنية](#4-قرارات-تقنية-بطيئة-تنفيذ-سريع)
5. [حدود الدومين](#5-حدود-الدومين-domain-boundaries)
6. [البساطة في البيانات](#6-البساطة-في-البيانات)
7. [البساطة في التدفق](#7-البساطة-في-التدفق)
8. [الاختبارات](#8-اختبارات-بساطتها-في-معناها)
9. [الرصد والعمليات](#9-الرصد-والعمليات)
10. [سجل القرارات](#10-خريطة-قرارات-decision-record)
11. [مكافحة التعقيد](#11-مكافحة-التعقيد-الشائع)
12. [إيقاع العمل](#12-إيقاع-العمل-cadence)
13. [دليل القرارات اليومي](#13-دليل-قرارات-يومي)
14. [متى تقبل التعقيد](#14-متى-تقبل-التعقيد)
15. [خطة 72 ساعة](#15-تطبيق-فوري-خطوات-72-ساعة)

---

## 1) البوصلة العقلية

### 🎯 السؤال الجوهري

> **"هل هذا أبسط حل يحافظ على الجودة والمتانة وقابلية التوسع؟"**

### القواعد الأربع

#### 1. اقتل التعقيد مبكراً

```python
# ❌ تعقيد مبكر - نظام plugins قبل الحاجة
class PluginManager:
    def __init__(self):
        self.plugins = {}
        self.hooks = {}
        self.middleware = []
        
    def register_plugin(self, name, plugin):
        self.plugins[name] = plugin
        
    def execute_hooks(self, hook_name, *args):
        for plugin in self.plugins.values():
            if hasattr(plugin, hook_name):
                getattr(plugin, hook_name)(*args)

# ✅ بساطة - حل المشكلة الحالية فقط
class EmailNotifier:
    def send(self, user, message):
        # إرسال مباشر
        pass
```

#### 2. ابدأ بالمشكلة، لا بالأدوات

```
❌ الطريقة الخاطئة:
"نحتاج Kafka لأنه يستخدمه الجميع"

✅ الطريقة الصحيحة:
"لدينا 1000 طلب/ثانية، هل نحتاج message queue؟"
→ لا، قاعدة البيانات الحالية تكفي
→ سنراقب ونضيف عند 10k طلب/ثانية
```

#### 3. التحيز للأفعال الصغيرة

```
📦 وحدات صغيرة قابلة للاستبدال:

user_service.py      (50 خط)   ← يمكن إعادة كتابته في ساعة
email_sender.py      (30 خط)   ← يمكن استبداله بسهولة
validator.py         (40 خط)   ← اختباره بسيط

❌ تجنب:
mega_service.py      (3000 خط) ← رعب الصيانة
```

#### 4. قابلية الحذف كميزة

```python
# ✅ كل وحدة قابلة للحذف
class CacheService:
    """يمكن حذف هذه الخدمة والعودة للـ DB مباشرة"""
    pass

class AnalyticsTracker:
    """يمكن حذفه دون تأثير على الوظائف الأساسية"""
    pass

# ❌ خطر - مرتبط بكل شيء
class CoreEngine:
    """حذفه يكسر النظام بالكامل"""
    pass
```

---

## 2) مبادئ التصميم الحاكمة

### MLF - الحد الأدنى القابل للعمل

```
❌ بناء كل شيء مرة واحدة:
┌─────────────────────────────────────────┐
│ User Auth + Profiles + Settings +       │
│ Notifications + Analytics + Reports     │
└─────────────────────────────────────────┘
6 أسابيع، بلا قيمة حتى النهاية

✅ MLF - قيمة متدرجة:
Week 1: ┌──────────┐ Auth ← قيمة فورية
        └──────────┘

Week 2: ┌──────────┐ + Profiles
        └──────────┘

Week 3: ┌──────────┐ + Settings
        └──────────┘
```

### التماسك العالي / الاقتران المنخفض

```python
# ✅ تماسك عالي - كل شيء متعلق بـ User
class UserService:
    def create_user(self): ...
    def update_user(self): ...
    def delete_user(self): ...

# ✅ اقتران منخفض - واجهات ضيقة
class UserService:
    def __init__(self, repo: UserRepository):  # فقط ما نحتاجه
        self.repo = repo

# ❌ اقتران عالي - تبعيات كثيرة
class UserService:
    def __init__(self, db, cache, logger, metrics, emailer, sms, ...):
        # تبعيات كثيرة جداً
        pass
```

### واجهات ضيقة، عقود واضحة

```python
# ✅ واجهة ضيقة
class UserRepository(Protocol):
    def get(self, user_id: int) -> User: ...
    def save(self, user: User) -> None: ...
    # فقط العمليات الأساسية

# ❌ واجهة واسعة
class UserRepository(Protocol):
    def get(self, user_id): ...
    def save(self, user): ...
    def find_by_email(self, email): ...
    def find_by_name(self, name): ...
    def search(self, query): ...
    def advanced_search(self, filters): ...
    # كثير جداً!
```

### تسطيح الطبقات

```
❌ طبقات زائدة بلا فائدة:
API → Controller → Service → Manager → Handler → Repository → DAO → DB
    (7 طبقات!)

✅ طبقات مبررة:
API → Service → Repository → DB
    (3 طبقات، كل منها يضيف قيمة)
```

### إزالة الحيل الغامضة

```python
# ❌ ماكرو غامض
@magic_decorator_that_does_many_things
class User:
    pass

# ✅ واضح وصريح
class User:
    def __init__(self, email: str, name: str):
        self.email = email
        self.name = name
```

### ممر بيانات صريح

```python
# ✅ تدفق واضح
def process_order(order_data):
    # 1. التحقق
    validated = validate_order(order_data)
    
    # 2. المعالجة
    processed = process_payment(validated)
    
    # 3. الحفظ
    saved = save_order(processed)
    
    return saved

# ❌ تدفق غامض - side effects خفية
def process_order(order_data):
    validate_order(order_data)  # يعدل global state
    process_payment()           # يستخدم thread local
    # تدفق غير واضح
```

### خيارات قليلة، رأي قوي

```python
# ✅ إعدادات افتراضية جيدة
class DatabaseConfig:
    pool_size: int = 10          # قيمة جيدة للأغلبية
    timeout: int = 30            # قيمة معقولة
    retry_count: int = 3         # توازن جيد

# ❌ كل شيء قابل للتخصيص
class DatabaseConfig:
    pool_size: int
    pool_timeout: int
    pool_recycle: int
    connection_timeout: int
    command_timeout: int
    # 50 خيار آخر...
```

---

## 3) أنماط بنيوية (Skeleton) بسيطة

### البنية المقترحة لـ CogniForge

```
app/
│
├── 🧠 core/                    ← النواة النقية
│   ├── domain/                 ← كيانات المجال
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── mission.py
│   │
│   ├── protocols.py            ← العقود/Interfaces
│   ├── errors.py               ← أخطاء مخصصة
│   └── types.py                ← أنواع أساسية
│
├── 🔌 edges/                   ← الحواف (I/O)
│   ├── api/                    ← HTTP endpoints
│   │   └── routers/
│   │
│   ├── database/               ← قاعدة البيانات
│   │   └── repositories/
│   │
│   ├── external/               ← خدمات خارجية
│   │   ├── openrouter.py
│   │   └── supabase.py
│   │
│   └── storage/                ← تخزين الملفات
│
├── ⚙️ application/             ← طبقة التطبيق
│   ├── use_cases/              ← حالات الاستخدام
│   │   ├── create_user.py
│   │   ├── chat.py
│   │   └── create_mission.py
│   │
│   └── orchestrators/          ← تنسيق العمليات
│
├── 🔧 composition_root.py      ← Dependency Injection
│
└── 📊 observability/           ← المراقبة
    ├── logging.py
    └── metrics.py
```

### النواة النقية (Pure Core)

```python
# app/core/domain/user.py

"""
كيان المستخدم النقي
✅ بدون تبعيات على Infrastructure
✅ منطق المجال فقط
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """كيان المستخدم"""
    
    id: Optional[int]
    email: str
    name: str
    created_at: datetime
    is_active: bool = True
    
    def validate_email(self) -> bool:
        """التحقق من صحة البريد الإلكتروني"""
        return "@" in self.email and "." in self.email
    
    def deactivate(self) -> None:
        """إلغاء تفعيل المستخدم"""
        self.is_active = False
    
    def activate(self) -> None:
        """تفعيل المستخدم"""
        self.is_active = True
```

### العقود (Protocols)

```python
# app/core/protocols.py

"""
العقود الأساسية للنظام
واجهات بدون تطبيقات
"""

from typing import Protocol, Optional
from app.core.domain.user import User

class UserRepository(Protocol):
    """عقد مستودع المستخدمين"""
    
    async def get(self, user_id: int) -> Optional[User]:
        """جلب مستخدم"""
        ...
    
    async def save(self, user: User) -> User:
        """حفظ مستخدم"""
        ...
    
    async def delete(self, user_id: int) -> None:
        """حذف مستخدم"""
        ...

class AIClient(Protocol):
    """عقد عميل الذكاء الاصطناعي"""
    
    async def chat(self, messages: list, model: str) -> str:
        """إرسال رسالة"""
        ...
```

### حالة الاستخدام (Use Case)

```python
# app/application/use_cases/create_user.py

"""
حالة استخدام: إنشاء مستخدم جديد
"""

from app.core.domain.user import User
from app.core.protocols import UserRepository
from app.core.errors import ValidationError

class CreateUserUseCase:
    """
    إنشاء مستخدم جديد
    
    مسؤوليات:
    1. التحقق من البيانات
    2. إنشاء كيان المستخدم
    3. حفظه عبر المستودع
    """
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def execute(self, email: str, name: str) -> User:
        """تنفيذ حالة الاستخدام"""
        
        # 1. إنشاء الكيان
        user = User(
            id=None,
            email=email,
            name=name,
            created_at=datetime.now()
        )
        
        # 2. التحقق
        if not user.validate_email():
            raise ValidationError("Invalid email format")
        
        # 3. الحفظ
        saved_user = await self.user_repo.save(user)
        
        return saved_user
```

### Composition Root

```python
# app/composition_root.py

"""
نقطة تجميع الاعتماديات
مكان واحد للـ wiring
"""

from app.edges.database.repositories.user_repository_impl import UserRepositoryImpl
from app.edges.external.openrouter_client import OpenRouterClient
from app.application.use_cases.create_user import CreateUserUseCase
from app.application.use_cases.chat import ChatUseCase

class Container:
    """حاوية الاعتماديات"""
    
    def __init__(self, db_session, settings):
        self.db_session = db_session
        self.settings = settings
        
        # Repositories
        self.user_repo = UserRepositoryImpl(db_session)
        
        # External Services
        self.ai_client = OpenRouterClient(settings.openrouter_api_key)
        
        # Use Cases
        self.create_user = CreateUserUseCase(self.user_repo)
        self.chat = ChatUseCase(self.ai_client)

# استخدام
container = Container(db_session, settings)
user = await container.create_user.execute("user@example.com", "John")
```

---

## 4) قرارات تقنية بطيئة، تنفيذ سريع

### القرارات البطيئة (Slow Decisions)

```
✅ قرارات يجب أن تكون بطيئة:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. نموذج البيانات الأساسي
2. حدود الخدمات (Service Boundaries)
3. العقود بين الطبقات (Contracts)
4. سياسة معالجة الأخطاء
5. استراتيجية التخزين (Storage Strategy)

⏸️ خذ وقتك - هذه قرارات صعبة التغيير
```

### التنفيذ السريع (Fast Implementation)

```
✅ تنفيذ يجب أن يكون سريع:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. إضافة ميزة جديدة
2. تغيير واجهة المستخدم
3. إضافة endpoint جديد
4. تحسين أداء
5. إصلاح bug

🚀 دورات قصيرة (1-2 يوم) مع قابلية الحذف
```

### مثال: متى نضيف Message Queue؟

```
المرحلة 1: (الآن - 100 user/sec)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API → Service → Database
قرار: لا حاجة لـ queue الآن

المرحلة 2: (المستقبل - 1000 user/sec)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نراقب: latency, error rate
إذا > 500ms → نقيّم الحاجة

المرحلة 3: (عند الحاجة - 10k user/sec)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API → Queue → Workers → Database
قرار: نضيف queue بناءً على بيانات حقيقية
```

---

## 5) حدود الدومين (Domain Boundaries)

### تسمية الحدود

```
✅ أسماء من اللغة المشتركة (Ubiquitous Language):

app/
├── domains/
│   ├── user_management/      ← "إدارة المستخدمين"
│   ├── conversations/         ← "المحادثات"
│   ├── missions/              ← "المهام"
│   └── analytics/             ← "التحليلات"

❌ أسماء تقنية غامضة:
├── module_a/
├── service_xyz/
└── handler_123/
```

### عبور الحدود بعقود صريحة

```python
# ✅ عبور صحيح بـ DTO

# Domain: User Management
class UserDTO:
    """Data Transfer Object"""
    id: int
    email: str
    name: str

class UserService:
    def get_user(self, user_id: int) -> UserDTO:
        user = self.repo.get(user_id)
        return UserDTO(
            id=user.id,
            email=user.email,
            name=user.name
        )

# Domain: Conversations
class ConversationService:
    def create_conversation(self, user_dto: UserDTO):
        # يستقبل DTO، لا يصل لـ User domain مباشرة
        conversation = Conversation(user_id=user_dto.id)
        ...

# ❌ عبور خاطئ - تبعية مباشرة
class ConversationService:
    def create_conversation(self, user: User):
        # تبعية مباشرة على User domain
        ...
```

### Pure Domain - بدون Infrastructure

```python
# ✅ Domain نقي

# app/core/domain/mission.py
class Mission:
    """كيان المهمة - بدون تبعيات خارجية"""
    
    def __init__(self, title: str, objective: str):
        self.title = title
        self.objective = objective
        self.status = "pending"
    
    def start(self):
        """منطق المجال فقط"""
        if self.status != "pending":
            raise InvalidStateError()
        self.status = "in_progress"
    
    def complete(self):
        """منطق المجال فقط"""
        if self.status != "in_progress":
            raise InvalidStateError()
        self.status = "completed"

# ❌ Domain ملوث بـ Infrastructure
class Mission(Base):  # ❌ SQLAlchemy Base
    __tablename__ = "missions"  # ❌ تفاصيل DB
    
    id = Column(Integer, primary_key=True)  # ❌ تفاصيل DB
```

---

## 6) البساطة في البيانات

### نموذج بيانات مسطح

```python
# ✅ مسطح وبسيط
class User:
    id: int
    email: str
    name: str
    created_at: datetime

class Profile:
    user_id: int
    bio: str
    avatar_url: str

# ❌ تطبيع زائد
class User:
    id: int
    email_id: int  # foreign key إلى جدول emails
    
class Email:
    id: int
    address: str
    
class EmailDomain:
    id: int
    domain: str
    
# تعقيد غير ضروري للحصول على email المستخدم!
```

### State Machine خفيفة

```python
# ✅ حالات واضحة ومحددة

class MissionStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Mission:
    status: MissionStatus
    
    def start(self):
        """انتقال: pending → in_progress"""
        if self.status != MissionStatus.PENDING:
            raise InvalidTransition(
                f"Cannot start mission in {self.status} state"
            )
        self.status = MissionStatus.IN_PROGRESS
    
    def complete(self):
        """انتقال: in_progress → completed"""
        if self.status != MissionStatus.IN_PROGRESS:
            raise InvalidTransition(
                f"Cannot complete mission in {self.status} state"
            )
        self.status = MissionStatus.COMPLETED
```

### القيود في أقرب نقطة

```python
# ✅ قيود في DB + Validation في الحواف

# 1. قيود قاعدة البيانات
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,  -- ✅ قيد فريد
    name VARCHAR(100) NOT NULL,          -- ✅ قيد not null
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')  -- ✅ قيد التنسيق
);

# 2. Validation في الحواف (API)
class UserCreateRequest(BaseModel):
    email: EmailStr  # ✅ Pydantic validation
    name: constr(min_length=1, max_length=100)  # ✅ قيود الطول
```

### سياسة التزامن الواضحة

```python
# ✅ Optimistic Locking - بسيط ومناسب للأغلبية

class Mission(Base):
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    version = Column(Integer, default=0)  # ✅ version للتزامن
    
    def update(self, new_title: str):
        """التحديث مع التحقق من الإصدار"""
        self.title = new_title
        self.version += 1

# في الـ repository
async def save(self, mission: Mission):
    # محاولة الحفظ
    try:
        await self.session.flush()
    except OptimisticLockError:
        raise ConcurrencyError("Mission was modified by another user")
```

---

## 7) البساطة في التدفق

### أهم 3 مسارات في CogniForge

```
═══════════════════════════════════════════════════════════
المسار 1: إنشاء محادثة جديدة
═══════════════════════════════════════════════════════════

User → API → ChatOrchestrator → [AIClient, ConversationRepo]
                                       ↓
                                  AI Response
                                       ↓
                                  Save to DB
                                       ↓
                                Return to User

نقاط الدخول: POST /api/conversations
العقود: ConversationCreate, AIClientProtocol, ConversationRepository
الأخطاء: ValidationError, AIServiceError, DatabaseError
السجلات: request_id, user_id, model, latency, tokens

═══════════════════════════════════════════════════════════
المسار 2: إنشاء مهمة (Mission)
═══════════════════════════════════════════════════════════

User → API → MissionOrchestrator → [Planner, MissionRepo]
                                         ↓
                                    Plan Tasks
                                         ↓
                                     Save Mission
                                         ↓
                                  Return to User

نقاط الدخول: POST /api/missions
العقود: MissionCreate, PlannerProtocol, MissionRepository
الأخطاء: ValidationError, PlanningError, DatabaseError
السجلات: request_id, user_id, objective, tasks_count

═══════════════════════════════════════════════════════════
المسار 3: تسجيل دخول المستخدم
═══════════════════════════════════════════════════════════

User → API → AuthService → [UserRepo, TokenService]
                                 ↓
                            Verify Password
                                 ↓
                            Generate Token
                                 ↓
                           Return to User

نقاط الدخول: POST /api/auth/login
العقود: LoginRequest, UserRepository, TokenService
الأخطاء: InvalidCredentials, UserNotFound
السجلات: user_id, login_time, ip_address
```

### حذف الخطوات غير الضرورية

```python
# ❌ خطوات زائدة

async def create_conversation(data):
    # 1. Log start
    logger.info("Starting conversation creation")
    
    # 2. Track metrics
    metrics.increment("conversation.create.started")
    
    # 3. Validate request
    validate_request(data)
    
    # 4. Check rate limit
    check_rate_limit(user)
    
    # 5. Check permissions
    check_permissions(user)
    
    # 6. Pre-process data
    data = preprocess(data)
    
    # 7. Call AI
    response = await ai_client.chat(data)
    
    # 8. Post-process response
    response = postprocess(response)
    
    # 9. Save to cache
    await cache.set(key, response)
    
    # 10. Save to DB
    await repo.save(conversation)
    
    # 11. Track metrics
    metrics.increment("conversation.create.completed")
    
    # 12. Log end
    logger.info("Conversation created")
    
    return response

# ✅ فقط ما يضيف قيمة حقيقية

async def create_conversation(data):
    # 1. Validate
    if not data.message:
        raise ValidationError("Message is required")
    
    # 2. Call AI
    response = await ai_client.chat(data.message)
    
    # 3. Save
    conversation = await repo.save(Conversation(
        user_id=data.user_id,
        message=data.message,
        response=response
    ))
    
    return conversation
```

---

## 8) اختبارات بساطتها في معناها

### اختبارات الوحدة للدومين

```python
# tests/unit/domain/test_mission.py

"""
اختبارات نقية للدومين
✅ بدون I/O
✅ سريعة (< 1ms)
✅ تغطي القواعد والسياسات
"""

def test_mission_can_be_started_when_pending():
    """يمكن بدء المهمة عندما تكون pending"""
    mission = Mission(title="Test", objective="Test obj")
    
    mission.start()
    
    assert mission.status == MissionStatus.IN_PROGRESS

def test_mission_cannot_be_started_when_in_progress():
    """لا يمكن بدء مهمة قيد التنفيذ"""
    mission = Mission(title="Test", objective="Test obj")
    mission.start()  # الآن in_progress
    
    with pytest.raises(InvalidStateError):
        mission.start()  # محاولة بدء مجدداً

def test_mission_cannot_be_completed_when_pending():
    """لا يمكن إكمال مهمة لم تبدأ"""
    mission = Mission(title="Test", objective="Test obj")
    
    with pytest.raises(InvalidStateError):
        mission.complete()
```

### اختبارات عقود الحواف

```python
# tests/contracts/test_user_repository_contract.py

"""
اختبارات العقود للمستودعات
تضمن أن أي تطبيق يلتزم بالعقد
"""

@pytest.mark.parametrize("repository_impl", [
    SqlAlchemyUserRepository,
    InMemoryUserRepository,
    # يمكن إضافة تطبيقات جديدة هنا
])
async def test_repository_can_save_and_retrieve_user(repository_impl):
    """كل تطبيق يجب أن يحفظ ويسترجع المستخدم"""
    repo = repository_impl()
    
    user = User(id=None, email="test@example.com", name="Test")
    saved = await repo.save(user)
    
    retrieved = await repo.get(saved.id)
    
    assert retrieved.email == "test@example.com"
    assert retrieved.name == "Test"
```

### اختبارات المسارات الحرجة

```python
# tests/e2e/test_create_conversation_flow.py

"""
اختبارات end-to-end لأهم مسارين
"""

@pytest.mark.e2e
async def test_create_conversation_flow():
    """المسار الكامل: API → Service → AI → DB → Response"""
    
    # Setup
    client = TestClient(app)
    
    # Execute
    response = client.post("/api/conversations", json={
        "message": "Hello, AI!",
        "user_id": 1
    })
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["message"] == "Hello, AI!"
```

---

## 9) الرصد والعمليات

### سجلات بنيوية

```python
# app/observability/logging.py

"""
سجلات بنيوية موحدة
"""

import structlog

logger = structlog.get_logger()

# ✅ استخدام بحقول معيارية
logger.info(
    "conversation_created",
    request_id="req_123",
    user_id=42,
    operation="create_conversation",
    latency_ms=250,
    status="success",
    model="gpt-4",
    tokens=150
)

# سيظهر كـ JSON:
{
    "event": "conversation_created",
    "request_id": "req_123",
    "user_id": 42,
    "operation": "create_conversation",
    "latency_ms": 250,
    "status": "success",
    "model": "gpt-4",
    "tokens": 150,
    "timestamp": "2025-01-10T10:30:00Z"
}
```

### ثلاث مقاييس أولية

```python
# app/observability/metrics.py

"""
مقاييس بسيطة وواضحة
"""

class Metrics:
    """
    المقاييس الأساسية الثلاث:
    1. معدل النجاح/الفشل
    2. زمن الاستجابة (latency)
    3. عدد الطلبات (throughput)
    """
    
    def __init__(self):
        # Counters
        self.requests_total = Counter("requests_total", ["endpoint", "status"])
        
        # Histograms
        self.request_latency = Histogram("request_latency_seconds", ["endpoint"])
        
        # Gauges
        self.active_requests = Gauge("active_requests")
    
    def track_request(self, endpoint: str, duration: float, status: str):
        """تتبع طلب واحد"""
        self.requests_total.labels(endpoint=endpoint, status=status).inc()
        self.request_latency.labels(endpoint=endpoint).observe(duration)

# استخدام
metrics = Metrics()

@app.post("/api/conversations")
async def create_conversation(data: ConversationCreate):
    start = time.time()
    
    try:
        result = await service.create(data)
        metrics.track_request("/api/conversations", time.time() - start, "success")
        return result
    except Exception as e:
        metrics.track_request("/api/conversations", time.time() - start, "error")
        raise
```

### تنبيهات حادة وقليلة

```yaml
# alerts.yaml

alerts:
  - name: HighErrorRate
    condition: error_rate > 5%
    duration: 5m
    severity: critical
    action: |
      1. تحقق من logs للأخطاء الأخيرة
      2. تحقق من صحة الخدمات الخارجية (AI, DB)
      3. في حالة فشل AI: فعّل fallback mode
      4. في حالة فشل DB: تحقق من الاتصال
  
  - name: HighLatency
    condition: p95_latency > 2s
    duration: 5m
    severity: warning
    action: |
      1. تحقق من load على الخادم
      2. تحقق من زمن استجابة AI
      3. فكر في تفعيل caching
```

---

## 10) خريطة قرارات (Decision Record)

### نموذج ADR خفيف

```markdown
# ADR-001: استخدام PostgreSQL عبر Supabase

## التاريخ
2025-01-10

## الحالة
✅ مقبول

## السياق
نحتاج قاعدة بيانات علائقية للتطبيق. الخيارات:
1. PostgreSQL مدار ذاتياً
2. Supabase (PostgreSQL مُدار)
3. MongoDB

## القرار
استخدام **Supabase** (PostgreSQL مُدار)

## الأسباب

### لماذا Supabase؟
- ✅ PostgreSQL كامل الميزات
- ✅ Authentication مدمج
- ✅ Real-time subscriptions
- ✅ إدارة أقل (managed service)
- ✅ Free tier سخي

### لماذا رفضنا البدائل؟
- ❌ PostgreSQL مدار ذاتياً: يتطلب إدارة وصيانة
- ❌ MongoDB: نموذج البيانات لدينا علائقي بطبيعته

## العواقب

### إيجابية
- سرعة التطوير
- تكلفة منخفضة في البداية
- أدوات مدمجة (Auth, Storage)

### سلبية
- Vendor lock-in جزئي
- قيود على Free tier

## تاريخ المراجعة
2025-07-10 (بعد 6 أشهر)

---

# ADR-002: استخدام OpenRouter للذكاء الاصطناعي

## التاريخ
2025-01-10

## الحالة
✅ مقبول

## السياق
نحتاج الوصول لنماذج AI متعددة (GPT-4, Claude, etc.)

## القرار
استخدام **OpenRouter** كبوابة موحدة

## الأسباب
- ✅ API موحد لجميع النماذج
- ✅ دفع حسب الاستخدام
- ✅ سهولة التبديل بين النماذج
- ✅ لا حاجة لمفاتيح API متعددة

## العواقب
- إيجابية: مرونة عالية
- سلبية: طبقة إضافية (latency قليل)

## تاريخ المراجعة
2025-04-10 (بعد 3 أشهر)
```

---

## 11) مكافحة التعقيد الشائع

### انجراف المتطلبات

```
✅ الحماية:

1. وثّق العقد:
   """
   POST /api/conversations
   Input: {message: string, user_id: int}
   Output: {id: int, response: string}
   """

2. اختبر العقد:
   test_conversation_contract()

3. أي تغيير يمر عبر قرار:
   "لماذا نحتاج هذا التغيير الآن؟"
```

### التجريد المبكر

```python
# ❌ تجريد مبكر - استخدام واحد فقط

class PaymentStrategy(ABC):
    @abstractmethod
    def process(self, amount): pass

class StripePayment(PaymentStrategy):
    def process(self, amount): 
        # تطبيق واحد فقط!
        pass

# ✅ بدون تجريد - انتظر حتى التكرار الثاني

def process_stripe_payment(amount):
    # تطبيق مباشر
    pass

# عند إضافة PayPal (التكرار الثاني)، نستخرج التجريد
```

### المرونة الزائفة

```python
# ❌ نظام plugins قبل الحاجة

class PluginSystem:
    def load_plugin(self, path): ...
    def register_hook(self, name, callback): ...
    def execute_hooks(self, name): ...

# ✅ استبدال مباشر عند الحاجة

# المرحلة 1: تطبيق مباشر
class EmailSender:
    def send(self, email): 
        # SMTP مباشر
        pass

# المرحلة 2: (عند الحاجة) استبدال
class EmailSender:
    def send(self, email):
        # SendGrid الآن
        pass
```

### الحلول الشاملة

```
❌ استخدام Kubernetes لتطبيق بسيط
❌ استخدام Kafka لـ 10 رسائل/دقيقة
❌ استخدام Elasticsearch لـ 1000 سجل

✅ ابدأ بسيط:
- Docker Compose بدلاً من K8s
- Database queue بدلاً من Kafka
- PostgreSQL full-text search بدلاً من Elasticsearch

✅ توسع عند الحاجة المثبتة بالأرقام
```

---

## 12) إيقاع العمل (Cadence)

### دورات قصيرة (1-2 أسبوع)

```
الأسبوع 1: Authentication
━━━━━━━━━━━━━━━━━━━━━━━━
الهدف: يمكن للمستخدم تسجيل الدخول
المخرج: POST /api/auth/login يعمل

الأسبوع 2: Conversations
━━━━━━━━━━━━━━━━━━━━━━━━
الهدف: يمكن للمستخدم إنشاء محادثة
المخرج: POST /api/conversations يعمل

الأسبوع 3: Missions
━━━━━━━━━━━━━━━━━━━━━━━━
الهدف: يمكن للمستخدم إنشاء مهمة
المخرج: POST /api/missions يعمل
```

### مراجعة في نهاية كل دورة

```
أسئلة المراجعة:
━━━━━━━━━━━━━━━━━━━━━━━━
1. ما الذي يمكن حذفه؟
2. ما الذي لم يُستخدم؟
3. هل الحدود لا تزال ضيقة؟
4. هل العقود لا تزال واضحة؟
5. هل يمكن تبسيط شيء؟
```

---

## 13) دليل قرارات يومي

```
☐ 1. هل هناك طريق أبسط يحقق نفس القيمة؟
      "يمكنني استخدام dict بسيط بدلاً من class معقد"

☐ 2. هل يمكن حذف هذه الوحدة دون كسر القيمة الأساسية؟
      "نعم، هذا caching يمكن حذفه والعودة للـ DB مباشرة"

☐ 3. هل الواجهة ضيقة وواضحة؟
      "3 methods فقط، أسماء واضحة، أخطاء محددة"

☐ 4. هل التدفق مفهوم في مخطط واحد؟
      "نعم: API → Service → Repo → DB"

☐ 5. هل يمكن اختبار هذا الجزء دون شبكة/قرص؟
      "نعم، منطق الدومين نقي"

☐ 6. هل أضفت تبعية جديدة؟ هل هي ضرورية؟
      "أضفت `requests`، بديل: استخدام httpx الموجود"

☐ 7. هل سجلت القرار ولماذا الآن وليس لاحقًا؟
      "نعم، ADR-003 يشرح لماذا نحتاج Redis الآن"
```

---

## 14) متى تقبل التعقيد؟

### المكاسب الجوهرية

```
✅ يمكن قبول التعقيد لـ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. الأمان (Security)
   مثال: تشفير البيانات الحساسة

2. الامتثال (Compliance)
   مثال: GDPR, SOC2

3. الموثوقية العالية (High Reliability)
   مثال: Circuit breakers, retries

4. الأداء الحرج (Critical Performance)
   مثال: Caching لـ hot path
```

### إثبات الحاجة بالأرقام

```
❌ "قد نحتاج scale في المستقبل"
✅ "لدينا 10k req/sec ونحتاج scale الآن"

❌ "Kafka أفضل من database queue"
✅ "Database queue تعطينا 100ms latency، نحتاج < 10ms"

❌ "نحتاج microservices للمرونة"
✅ "Monolith يأخذ 5 دقائق للـ deploy، نحتاج < 1 دقيقة"
```

### التعقيد في الحواف، لا النواة

```
✅ تعقيد مقبول:

app/edges/external/complex_ai_client.py
  ← تعقيد التعامل مع API خارجي
  ← محصور في edge layer

app/core/domain/mission.py
  ← بسيط ونقي
  ← لا تعقيد هنا
```

---

## 15) تطبيق فوري: خطوات 72 ساعة

### اليوم 1: التدفقات الأساسية

```
الصباح (4 ساعات):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ حصر أهم 3 مسارات استخدام
☐ رسم كل مسار (sequence diagram بسيط)
☐ تحديد العقود بين الطبقات
☐ إزالة أي خطوة غير ضرورية

المساء (4 ساعات):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ مراجعة الكود الحالي للمسارات الثلاث
☐ تحديد ما يمكن حذفه/تبسيطه
☐ كتابة قائمة بالتحسينات المقترحة
```

### اليوم 2: الفصل والاختبار

```
الصباح (4 ساعات):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ فصل النواة عن الحواف
   - استخراج domain entities
   - تعريف protocols/interfaces
   - إنشاء composition root بسيط

المساء (4 ساعات):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ كتابة 3-5 اختبارات وحدة للدومين
☐ إضافة سجلات بنيوية أساسية
   - request_id
   - user_id
   - operation
   - latency
   - status
```

### اليوم 3: التوثيق والمراقبة

```
الصباح (4 ساعات):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ كتابة ADR لأهم قرارين:
   - ADR-001: Database choice
   - ADR-002: AI provider choice

☐ توثيق العقود الأساسية:
   - API contracts
   - Domain boundaries

المساء (4 ساعات):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
☐ إضافة تنبيهين فقط:
   - High error rate (> 5%)
   - High latency (p95 > 2s)

☐ مراجعة نهائية:
   - هل الطبقات مسطحة؟
   - هل التبعيات مبررة؟
   - هل يمكن فهم النظام بسرعة؟
```

---

## 📋 Checklist النهائي

```
☐ النواة نقية (بدون تبعيات خارجية ثقيلة)
☐ الحواف قابلة للاستبدال
☐ العقود واضحة وموثقة
☐ المسارات الحرجة مرسومة ومفهومة
☐ الاختبارات تغطي الدومين
☐ السجلات بنيوية وموحدة
☐ المقاييس الثلاث الأساسية موجودة
☐ التنبيهات قليلة وحادة
☐ ADRs موجودة لأهم القرارات
☐ الدورات قصيرة (1-2 أسبوع)
☐ المراجعة الدورية مطبقة
```

---

## 🎓 الخلاصة

**البساطة الخارقة ليست عن كتابة كود أقل، بل عن:**

1. ✅ **قتل التعقيد مبكراً** - سؤال واحد لكل قرار
2. ✅ **البدء بالمشكلة** - لا بالأدوات
3. ✅ **نواة نقية** - بدون تبعيات
4. ✅ **حواف قابلة للاستبدال** - I/O معزول
5. ✅ **عقود واضحة** - واجهات ضيقة
6. ✅ **تدفق مفهوم** - يمكن رسمه على ورقة
7. ✅ **اختبارات ذات معنى** - تغطي القواعد
8. ✅ **مراقبة بسيطة** - 3 مقاييس فقط
9. ✅ **قرارات موثقة** - ADRs خفيفة
10. ✅ **دورات قصيرة** - قيمة كل أسبوع

---

**"البساطة هي أعلى درجات الأناقة"** - ليوناردو دا فينشي

**Built with ❤️ by applying superhuman simplicity principles**

*Houssam Benmerah - 2025*
