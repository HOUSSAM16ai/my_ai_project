# 📖 دليل المطور الشامل - CogniForge

## 🎯 مرحباً بك في CogniForge!

هذا الدليل سيساعدك على فهم المشروع بشكل كامل وبسيط.

---

## 🗂️ البنية العامة للمشروع

```
CogniForge/
│
├── app/                      # الكود الأساسي للتطبيق
│   ├── main.py              # نقطة الدخول الرئيسية
│   ├── kernel.py            # قلب النظام
│   ├── models.py            # نماذج قاعدة البيانات
│   │
│   ├── api/                 # واجهات برمجة التطبيقات (API)
│   │   ├── routers/         # المسارات (Endpoints)
│   │   └── dependencies.py  # الاعتماديات المشتركة
│   │
│   ├── config/              # الإعدادات
│   │   ├── settings.py      # إعدادات التطبيق
│   │   └── ai_models.py     # إعدادات نماذج الذكاء الاصطناعي
│   │
│   ├── core/                # الوظائف الأساسية
│   │   ├── database.py      # إدارة قاعدة البيانات
│   │   ├── security.py      # الأمان والمصادقة
│   │   └── gateway/         # بوابة الذكاء الاصطناعي
│   │
│   ├── middleware/          # الطبقات الوسيطة
│   │   └── security/        # الأمان
│   │
│   ├── schemas/             # مخططات البيانات (Pydantic)
│   │
│   ├── security/            # خدمات الأمان
│   │
│   └── services/            # الخدمات الأساسية
│       ├── user_service.py      # إدارة المستخدمين
│       ├── system_service.py    # صحة النظام
│       ├── database_service.py  # قاعدة البيانات
│       └── history_service.py   # السجل
│
├── tests/                   # الاختبارات
│
├── docs/                    # التوثيق
│
└── requirements.txt         # المكتبات المطلوبة
```

---

## 🚀 البداية السريعة

### 1. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 2. تشغيل التطبيق
```bash
python3 -m uvicorn app.main:app --reload
```

### 3. فتح المتصفح
```
http://localhost:8000
```

---

## 📚 فهم الملفات الأساسية

### 1. app/main.py - نقطة الدخول

```python
"""
نقطة الدخول الرئيسية للتطبيق

الدور:
- إنشاء تطبيق FastAPI
- تحميل الإعدادات
- تهيئة النظام
"""

from app.kernel import RealityKernel

# إنشاء التطبيق
app = create_app()
```

**ما يحدث هنا:**
1. يتم استيراد `RealityKernel` (قلب النظام)
2. يتم إنشاء التطبيق باستخدام `create_app()`
3. التطبيق جاهز للعمل!

---

### 2. app/kernel.py - قلب النظام

```python
"""
قلب النظام - يربط كل شيء معاً

الدور:
- إنشاء تطبيق FastAPI
- إضافة الطبقات الوسيطة (Middleware)
- ربط المسارات (Routes)
"""

class RealityKernel:
    def __init__(self, settings):
        # تهيئة النظام
        self.app = self._create_pristine_app()
        self._weave_routes()
    
    def _weave_routes(self):
        # ربط المسارات
        self.app.include_router(system.router)
```

**ما يحدث هنا:**
1. يتم إنشاء تطبيق FastAPI نظيف
2. يتم إضافة الطبقات الوسيطة (الأمان، CORS، إلخ)
3. يتم ربط جميع المسارات

---

### 3. app/models.py - نماذج قاعدة البيانات

```python
"""
نماذج قاعدة البيانات

الدور:
- تعريف جداول قاعدة البيانات
- تعريف العلاقات بين الجداول
"""

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
```

**ما يحدث هنا:**
1. يتم تعريف جدول `User` في قاعدة البيانات
2. كل مستخدم له `id` و `email` و `password`

---

### 4. app/services/ - الخدمات

#### UserService - خدمة المستخدمين
```python
"""
خدمة إدارة المستخدمين

الدور:
- إنشاء مستخدمين جدد
- جلب معلومات المستخدمين
- تحديث بيانات المستخدمين
"""

class UserService:
    async def get_all_users(self):
        # جلب جميع المستخدمين من قاعدة البيانات
        return await self.db.execute(select(User))
```

#### SystemService - خدمة النظام
```python
"""
خدمة صحة النظام

الدور:
- فحص صحة النظام
- التحقق من الاتصال بقاعدة البيانات
"""

class SystemService:
    async def verify_system_integrity(self):
        # فحص صحة النظام
        return {"status": "healthy"}
```

---

## 🔧 كيف تضيف ميزة جديدة؟

### مثال: إضافة خدمة جديدة

#### الخطوة 1: إنشاء الخدمة
```python
# app/services/product_service.py

"""
خدمة إدارة المنتجات

الدور:
- إدارة المنتجات في النظام
"""

class ProductService:
    def __init__(self, db):
        self.db = db
    
    async def get_all_products(self):
        """جلب جميع المنتجات"""
        return await self.db.execute(select(Product))
    
    async def create_product(self, name: str, price: float):
        """إنشاء منتج جديد"""
        product = Product(name=name, price=price)
        self.db.add(product)
        await self.db.commit()
        return product
```

#### الخطوة 2: إنشاء المسار (Router)
```python
# app/api/routers/products.py

from fastapi import APIRouter, Depends
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/")
async def get_products(service: ProductService = Depends()):
    """جلب جميع المنتجات"""
    return await service.get_all_products()

@router.post("/")
async def create_product(
    name: str, 
    price: float,
    service: ProductService = Depends()
):
    """إنشاء منتج جديد"""
    return await service.create_product(name, price)
```

#### الخطوة 3: ربط المسار في kernel.py
```python
# في app/kernel.py

from app.api.routers import products

def _weave_routes(self):
    self.app.include_router(products.router)
```

---

## 🧪 كيف تكتب اختبار؟

```python
# tests/test_product_service.py

import pytest
from app.services.product_service import ProductService

@pytest.mark.asyncio
async def test_create_product(db_session):
    """اختبار إنشاء منتج"""
    service = ProductService(db=db_session)
    
    # إنشاء منتج
    product = await service.create_product(
        name="كتاب",
        price=50.0
    )
    
    # التحقق
    assert product.name == "كتاب"
    assert product.price == 50.0
```

---

## 📖 المفاهيم الأساسية

### 1. FastAPI
- إطار عمل حديث لبناء APIs
- سريع جداً
- سهل الاستخدام

### 2. SQLModel
- مكتبة لإدارة قاعدة البيانات
- تجمع بين SQLAlchemy و Pydantic

### 3. Pydantic
- مكتبة للتحقق من البيانات
- تستخدم في تعريف المخططات (Schemas)

### 4. Async/Await
- برمجة غير متزامنة
- تسمح بتنفيذ عدة عمليات في نفس الوقت

---

## 🎯 نصائح للمطورين الجدد

### 1. ابدأ بالأساسيات
- افهم `main.py` أولاً
- ثم `kernel.py`
- ثم `models.py`

### 2. اقرأ الكود
- كل ملف موثق بالعربية
- اقرأ التعليقات بعناية

### 3. جرب الأمثلة
- شغل التطبيق
- جرب الـ APIs
- اكتب اختبارات

### 4. لا تخف من الأخطاء
- الأخطاء طبيعية
- تعلم منها
- اسأل عند الحاجة

---

## 🔗 روابط مفيدة

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

## ✅ الخلاصة

المشروع الآن:
- ✅ بسيط ومنظم
- ✅ موثق بالكامل
- ✅ سهل الفهم
- ✅ جاهز للتطوير

**مبروك! أنت الآن جاهز للبدء في التطوير! 🎉**

---

**آخر تحديث**: 2024-12-20  
**الحالة**: ✅ مكتمل  
**الجودة**: ممتازة
