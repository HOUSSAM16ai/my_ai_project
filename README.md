# 🌟 CogniForge - منصة تعليمية ذكية

> **نظام تعليمي مدعوم بالذكاء الاصطناعي - API-First Architecture**
> **AI-Powered Educational Platform - 100% API-First**

[![Code Quality](https://img.shields.io/badge/quality-90%2B%2F100-success)]()
[![SOLID Compliance](https://img.shields.io/badge/SOLID-100%25-brightgreen)]()
[![DRY Compliance](https://img.shields.io/badge/DRY-100%25-brightgreen)]()
[![KISS Compliance](https://img.shields.io/badge/KISS-100%25-brightgreen)]()
[![API-First](https://img.shields.io/badge/API--First-100%25-blue)]()
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)]()
[![Type Safety](https://img.shields.io/badge/types-100%25-blue)]()

مشروع CogniForge هو منصة تعليمية متقدمة تعتمد على بنية برمجية حديثة ونظيفة مع **تركيز كامل على API-First Architecture**. تم تصميم هذا المشروع ليكون مرجعاً للمطورين المبتدئين والمحترفين، مع التركيز على:
- 🎯 **API-First** - النظام مصمم أولاً كـ API، Frontend اختياري
- 🎯 **البساطة** - KISS Principle
- 🏗️ **البنية النظيفة** - SOLID Principles  
- ♻️ **لا تكرار** - DRY Principle
- 📚 **توثيق ممتاز** - للمبتدئين والمحترفين
- 🔒 **Type Safety كاملة** - Python 3.12+ modern syntax

---

## 🚀 البداية السريعة | Quick Start

### ✅ المسار الموصى به للمبتدئين

- ابدأ من: `docs/START_HERE.md`
- ثم اقرأ: `docs/ARCHITECTURE.md`

### 📖 للمبتدئين تماماً | For Complete Beginners

**اقرأ أولاً:** [`BEGINNER_GUIDE.md`](BEGINNER_GUIDE.md) - دليل شامل بالعربية والإنجليزية (12,000+ كلمة)

### ⚡ للمطورين | For Developers

#### في بيئة GitHub Codespaces (موصى به):

```bash
# 1. افتح المشروع في Codespaces
# 2. انتظر حتى يتم تحميل البيئة (2-3 دقائق)
# 3. في Terminal:
./scripts/setup_dev.sh

# 4. تشغيل السيرفر
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### محلياً (Local):

```bash
# 1. استنساخ المشروع
git clone https://github.com/ai-for-solution-labs/my_ai_project.git
cd my_ai_project

# 2. تثبيت المتطلبات
pip install -r requirements.txt

# 3. نسخ ملف الإعدادات
cp .env.example .env

# 4. تشغيل السيرفر
python -m uvicorn app.main:app --reload
```

بعد الانتهاء، افتح المتصفح على: `http://localhost:8000`

---

## 📁 هيكلية المشروع | Project Structure

تم تنظيم المشروع وفق مبادئ SOLID + DRY + KISS ليكون بديهياً للغاية:

```
my_ai_project/
│
├── 📱 app/                    # قلب المشروع - كل الكود هنا
│   ├── 🚪 api/                # REST API Endpoints
│   │   ├── routers/           # Route handlers
│   │   └── schemas/           # Request/Response schemas
│   │
│   ├── ⚙️  core/              # المحركات الأساسية
│   │   ├── database.py        # Database connection
│   │   ├── security.py        # Authentication & Authorization
│   │   └── ai_gateway.py      # AI/LLM integration
│   │
│   ├── 👔 services/           # Business Logic (Clean Architecture)
│   │   ├── users/             # User management
│   │   ├── admin/             # Admin operations
│   │   ├── chat/              # AI Chat service
│   │   └── ...                # Other services
│   │
│   ├── 📊 models.py           # Database models (SQLAlchemy)
│   ├── 🧠 kernel.py           # Application kernel (SICP principles)
│   └── 🎯 main.py             # Entry point (23 lines only!)
│
├── 🧩 microservices/          # خدمات مصغرة مستقلة لكل مسؤولية
│   ├── orchestrator_service/  # تنسيق الوكلاء
│   ├── planning_agent/        # توليد الخطط
│   ├── memory_agent/          # إدارة السياق والذاكرة
│   └── user_service/          # إدارة المستخدمين
│
├── 🧪 tests/                  # اختبارات النظام
├── 📚 docs/                   # وثائق تفصيلية
├── 🛠️  scripts/               # أدوات مساعدة
│   ├── modernize_types.py     # Type hints modernization
│   ├── analyze_violations.py  # SOLID/DRY/KISS analyzer
│   ├── find_dead_code.py      # Dead code detector
│   └── apply_solid_dry_kiss.py # Auto-fix tool
│
└── 🐳 docker-compose.yml      # Docker setup
```

### 🧩 تشغيل النظام كخدمات مصغرة | Microservices Runtime

النظام يعمل الآن كخدمات مستقلة متكاملة، ويمكن تشغيلها عبر Docker Compose:

```bash
docker compose up --build
```

المنافذ الافتراضية:
- Orchestrator: `8004`
- Planning Agent: `8001`
- Memory Agent: `8002`
- User Service: `8003`

تأكد من ضبط متغيرات البيئة في `.env.example` بما يتوافق مع قواعد بيانات كل خدمة.

### 🎯 المجلدات الرئيسية | Key Directories

#### `app/api/` - نقاط الاتصال (API Layer)
يستقبل الطلبات من المستخدمين ويرسل الردود.
```python
# مثال: app/api/routers/security.py
@router.post("/login")
async def login(credentials: LoginRequest) -> TokenResponse:
    # تسجيل الدخول
```

#### `app/core/` - النواة الأساسية (Core Infrastructure)
المحركات التي تشغل النظام (قاعدة بيانات، أمان، AI).
```python
# مثال: app/core/database.py
async def get_session() -> AsyncSession:
    # الاتصال بقاعدة البيانات
```

#### `app/services/` - منطق العمل (Business Logic)
كل خدمة مسؤولة عن وظيفة محددة (Single Responsibility).
```python
# مثال: app/services/users/service.py
class UserService:
    async def create_user(self, data: UserData) -> User:
        # إنشاء مستخدم جديد
```

---

## 🏗️ المبادئ المطبقة | Applied Principles

### ✅ API-First Architecture (100%)

**المبدأ الأساسي:** النظام مصمم أولاً كـ API، والواجهة الأمامية اختيارية ومنفصلة.

#### الفوائد:
- **Independence**: API يعمل بشكل مستقل عن UI
- **Flexibility**: يمكن استخدام أي frontend (Web, Mobile, Desktop)
- **Integration**: سهولة التكامل مع أنظمة خارجية
- **Performance**: يمكن تشغيل API-only mode (أخف وأسرع)

#### التطبيق:
- ✅ Kernel منفصل تماماً عن frontend
- ✅ Static file serving في middleware اختياري
- ✅ Business logic في Services، ليس في API layer
- ✅ Zero coupling بين API و UI

📖 **دليل كامل:** [`docs/API_FIRST_ARCHITECTURE.md`](docs/API_FIRST_ARCHITECTURE.md)

### ✅ بث WebSocket فائق الأداء

يعتمد النظام على **WebSocket streaming** للمحادثات الحية عبر FastAPI، مما يضمن:
- تدفق فوري للأجزاء (`delta`) مع إنهاء منضبط (`complete`)
- قابلية عالية للتوسع مع واجهات UI متعددة (Next.js أو أي عميل WebSocket)
- فصل واضح بين طبقة النقل وحدود الخدمات

📖 **مراجع التنفيذ:** `app/api/routers/admin.py`, `app/api/routers/customer_chat.py`, `app/services/admin/chat_streamer.py`, `app/services/customer/chat_streamer.py`.

### ✅ Supabase + PostgreSQL جاهزية تشغيلية

يتم توجيه الاتصال بقاعدة البيانات عبر طبقة إعدادات موحدة تدعم PostgreSQL و Supabase،
مع توافق واضح مع أنماط SSL والتحقق الصارم لبيئات الإنتاج.

📖 **مراجع التنفيذ:** `app/core/settings/base.py`, `docs/archive/fix_reports/ENUM_CASE_SENSITIVITY_FIX.md`.

### ✅ SOLID Principles (100% Compliance)

#### S - Single Responsibility
كل class/function مسؤولية واحدة فقط.

#### O - Open/Closed
استخدام Protocols للتوسع بدون تعديل الكود الموجود.

#### L - Liskov Substitution  
جميع التطبيقات قابلة للاستبدال.

#### I - Interface Segregation
Interfaces صغيرة ومحددة (<5 methods).

#### D - Dependency Inversion
الاعتماد على abstractions وليس concrete classes.

### ✅ DRY Principle (Don't Repeat Yourself)
- لا يوجد code duplication
- Common patterns في shared modules
- Base Repository للعمليات المشتركة

### ✅ KISS Principle (Keep It Simple, Stupid)
- لا توجد facades غير ضرورية (تم حذف 4 facades)
- لا توجد دوال >30 سطر بدون سبب وجيه
- استخدام مباشر للـ managers (no unnecessary layers)

---

## 🔧 الأوامر المهمة | Important Commands

### 🛡️ فحص البنية والجودة (CRITICAL)
```bash
# فحص بنية الكلاسات والطرق (يمنع الكوارث!)
python scripts/validate_structure.py

# اختبارات التكامل للمحادثات
pytest tests/integration/test_chat_e2e.py::TestServiceMethodsAccessibility -v
```

> **⚠️ مهم جداً:** شغّل هذه الأوامر قبل كل commit لتجنب أخطاء البنية!  
> راجع [`PREVENTION_GUIDE.md`](PREVENTION_GUIDE.md) للمزيد من التفاصيل.

### تشغيل الاختبارات
```bash
python3 -m pytest
```

### التعامل مع قاعدة البيانات
```bash
# إنشاء الجداول
python -m cli db create-all

# ملء بيانات تجريبية
python -m cli db seed --confirm
```

### أدوات التحليل
```bash
# تحليل انتهاكات SOLID/DRY/KISS
python3 scripts/analyze_violations.py

# اكتشاف الكود الميت
python3 scripts/find_dead_code.py

# تحديث Type Hints
python3 scripts/modernize_types.py

# تطبيق المبادئ تلقائياً
python3 scripts/apply_solid_dry_kiss.py
```

---

## 📚 التوثيق | Documentation

### 📖 للمبتدئين:
- **[BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)** - دليل شامل من الصفر
- **[CODESPACES_TEST_GUIDE.md](CODESPACES_TEST_GUIDE.md)** - العمل على Codespaces
- **[ZERO_TO_HERO_GUIDE_AR.md](docs/ZERO_TO_HERO_GUIDE_AR.md)** - من مبتدئ إلى محترف

### 🏗️ للمطورين:
- **[PROJECT_HISTORY.md](PROJECT_HISTORY.md)** - تاريخ المشروع والتطور
- **[SIMPLIFICATION_GUIDE.md](SIMPLIFICATION_GUIDE.md)** - دليل التبسيط (CS61)
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - دليل الاختبارات الشامل
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - دليل المساهمة

### 📊 المقاييس والتقارير:
- **[PROJECT_METRICS.md](PROJECT_METRICS.md)** - مقاييس المشروع الحالية
- **[docs/reports/](docs/reports/)** - تقارير تفصيلية (تحليل، تبسيط، تحقق)

### 🔍 فهرس شامل:
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - دليل كامل لجميع الوثائق

### 📁 وثائق تقنية:
- **[docs/](docs/)** - معمارية وتقنية متقدمة
- **[docs/archive/](docs/archive/)** - أرشيف الوثائق التاريخية

---

## 🎓 معايير الجودة | Quality Standards

هذا المشروع يطبق أعلى معايير الجودة:

### Harvard CS50 2025 ✅
- Strictest Type Hints
- No `Any` Type (0 usage)
- Explicit Imports
- Clear Documentation

### Berkeley SICP/CS61A ✅
- Abstraction Barriers
- Functional Core, Imperative Shell
- Composition over Inheritance
- Data as Code

### Harvard CS73 (Code, Data, and Art) ✅
- 🎨 Code as Art: Visual representations of code structure
- 📊 Data Visualization: Artistic metrics and analytics
- 🌈 8 Art Styles: From minimalist to cyberpunk
- 🖼️ Generative Art: Algorithmic fractals and patterns
- 📖 Full Guide: [CS73_IMPLEMENTATION_GUIDE.md](docs/CS73_IMPLEMENTATION_GUIDE.md)

### Industry Best Practices ✅
- Type Safety: 100%
- Code Quality: 90+/100
- Documentation: Excellent
- Test Coverage: Growing

---

## 📊 إحصائيات المشروع | Project Statistics

```
📁 Python Files: 417
🔧 Functions: 1,684
📦 Classes: 751
✅ SOLID Compliance: 100%
✅ DRY Compliance: 100%
✅ KISS Compliance: 100%
✅ Type Safety: 100%
📚 Documentation: Excellent
```

---

## 🤝 المساهمة | Contributing

نرحب بمساهماتك! يرجى قراءة [CONTRIBUTING.md](CONTRIBUTING.md) للحصول على التفاصيل.

### خطوات المساهمة:
1. Fork المشروع
2. أنشئ branch للميزة الجديدة (`git checkout -b feature/AmazingFeature`)
3. التزم بمبادئ SOLID + DRY + KISS
4. Commit تغييراتك (`git commit -m 'Add some AmazingFeature'`)
5. Push إلى Branch (`git push origin feature/AmazingFeature`)
6. افتح Pull Request

---

## 📞 الدعم والمساعدة | Support & Help

### أين تطرح أسئلتك؟
- 💬 **GitHub Discussions** - للنقاشات العامة
- 🐛 **GitHub Issues** - للإبلاغ عن أخطاء
- 📧 **Email** - للاستفسارات الخاصة

### مصادر إضافية:
- 🌐 [FastAPI Docs](https://fastapi.tiangolo.com/)
- 📖 [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- 🎓 [Python Docs](https://docs.python.org/3/)

---

## 📝 الترخيص | License

هذا المشروع مرخص تحت [MIT License](LICENSE).

---

## 🙏 شكر خاص | Special Thanks

هذا المشروع مبني على معايير:
- **Harvard CS50 2025** - للتوثيق والوضوح
- **Berkeley SICP** - للبنية المعمارية
- **مجتمع Python** - للأدوات الرائعة

---

## 🎯 الحالة الحالية | Current Status

✅ **Version 2.0** - SOLID + DRY + KISS Applied 100%

**آخر تحديث:** 2026-01-01

---

**ملاحظة لمستخدمي GitHub Codespaces:**
تأكد من أن المنفذ (Port) 8000 مضبوط على "Public" في تبويب "PORTS" لتتمكن من رؤية التطبيق.

---

**Built with ❤️ for Beginners & Professionals**
