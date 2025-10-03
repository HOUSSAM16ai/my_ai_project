# 🧠 دليل قاعدة البيانات الشعاعية (Vector Database) - مشروع CogniForge

## نعم، يوجد نظام قاعدة بيانات شعاعية متكامل في المشروع! ✅

---

## 📋 جدول المحتويات

1. [نظرة عامة](#نظرة-عامة)
2. [التقنيات المستخدمة](#التقنيات-المستخدمة)
3. [البنية المعمارية](#البنية-المعمارية)
4. [كيف يعمل النظام](#كيف-يعمل-النظام)
5. [الاستخدام والأمثلة](#الاستخدام-والأمثلة)
6. [التكوين والإعدادات](#التكوين-والإعدادات)
7. [الوظائف الرئيسية](#الوظائف-الرئيسية)

---

## 🎯 نظرة عامة

يحتوي مشروع **CogniForge** على نظام قاعدة بيانات شعاعية (Vector Database) متطور ومتكامل يستخدم لـ:

- 🔍 **البحث الدلالي الذكي** (Semantic Search)
- 📚 **تخزين واسترجاع السياق** (Context Retrieval)
- 🧩 **الفهرسة الذكية للكود** (Code Indexing)
- 🤖 **تحسين استجابات الذكاء الاصطناعي** (AI Response Enhancement)

### ✨ المميزات الرئيسية

- ✅ **قاعدة بيانات PostgreSQL** مع امتداد **pgvector**
- ✅ **نموذج تضمين متقدم** (SentenceTransformers - all-MiniLM-L6-v2)
- ✅ **فهرسة تدريجية ذكية** (Incremental Indexing)
- ✅ **بحث بالتشابه الدلالي** (Cosine Similarity Search)
- ✅ **تجزئة النصوص الطويلة** (Text Chunking)
- ✅ **ذاكرة تخزين مؤقت** (LRU Cache)

---

## 🛠️ التقنيات المستخدمة

### 1. قاعدة البيانات
```yaml
Database: PostgreSQL 15.1.0.118
Extension: pgvector (vector similarity search)
Image: supabase/postgres:15.1.0.118
Port: 5432
```

### 2. نموذج التضمين (Embedding Model)
```yaml
Model: all-MiniLM-L6-v2
Library: sentence-transformers >= 2.6.1
Vector Dimension: 384
Performance: سريع وخفيف (80MB فقط)
```

### 3. المكتبات الأساسية
```python
- sentence-transformers >= 2.6.1  # للتضمين
- SQLAlchemy                       # للتفاعل مع قاعدة البيانات
- pgvector                         # امتداد PostgreSQL
```

---

## 🏗️ البنية المعمارية

### هيكل جدول `code_documents`

```sql
CREATE TABLE code_documents (
    id TEXT PRIMARY KEY,              -- معرف فريد (file_path::chunk_index)
    file_path TEXT,                   -- مسار الملف
    chunk_index INT,                  -- رقم الجزء
    content TEXT,                     -- محتوى النص
    file_hash TEXT,                   -- هاش الملف الكامل
    chunk_hash TEXT,                  -- هاش الجزء
    source TEXT,                      -- مصدر المحتوى
    embedding vector(384),            -- المتجه الشعاعي (384 بُعد)
    updated_at TIMESTAMP              -- تاريخ التحديث
);

-- فهارس للأداء العالي
CREATE INDEX idx_code_documents_file_path 
    ON code_documents(file_path);

CREATE INDEX idx_code_documents_embedding 
    ON code_documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

### 📊 معمارية النظام

```
┌─────────────────────────────────────────────────────────────┐
│              Vector Database Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │  ملفات       │ ───▶ │  Text        │                    │
│  │  المشروع     │      │  Chunking    │                    │
│  └──────────────┘      └──────┬───────┘                    │
│                               │                             │
│                               ▼                             │
│                      ┌──────────────┐                       │
│                      │  Embedding   │                       │
│                      │  Model       │                       │
│                      │  (MiniLM)    │                       │
│                      └──────┬───────┘                       │
│                               │                             │
│                               ▼                             │
│                      ┌──────────────┐                       │
│                      │  PostgreSQL  │                       │
│                      │  + pgvector  │                       │
│                      │  (384-dim)   │                       │
│                      └──────┬───────┘                       │
│                               │                             │
│                               ▼                             │
│                      ┌──────────────┐                       │
│  ┌──────────────┐   │  Similarity  │   ┌──────────────┐   │
│  │  استعلام     │──▶│  Search      │──▶│  النتائج     │   │
│  │  المستخدم    │   │  (Cosine)    │   │  الأكثر تشابه │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ كيف يعمل النظام

### 1️⃣ الفهرسة (Indexing)

عملية تحويل ملفات المشروع إلى متجهات شعاعية:

```python
# الخطوات:
1. قراءة ملفات المشروع (.py, .md, .txt, .json, إلخ)
2. تقسيم النصوص الطويلة إلى أجزاء (chunks) بحجم 6000 حرف
3. حساب hash لكل جزء للتحقق من التغييرات
4. تحويل كل جزء إلى متجه شعاعي (384 بُعد)
5. تخزين المتجهات في PostgreSQL
6. بناء فهرس IVFFlat للبحث السريع
```

**مثال على الكود:**
```python
from app.services.system_service import index_project

# فهرسة المشروع
result = index_project(force=False, chunking=True)
print(f"تم فهرسة {result.data['indexed_new']} ملف جديد")
print(f"إجمالي الملفات: {result.data['total_in_store']}")
```

### 2️⃣ البحث الدلالي (Semantic Search)

البحث عن محتوى مشابه باستخدام التشابه الدلالي:

```python
# الخطوات:
1. استقبال نص الاستعلام من المستخدم
2. تحويل الاستعلام إلى متجه شعاعي
3. حساب التشابه (cosine similarity) مع جميع المتجهات المخزنة
4. إرجاع النتائج الأكثر تشابهاً
5. ترتيب النتائج حسب الأولوية (app/services/ لها أولوية)
```

**مثال على الكود:**
```python
from app.services.system_service import find_related_context

# البحث عن سياق مرتبط
query = "كيف يتم معالجة البيانات في النظام؟"
result = find_related_context(query, limit=6)

for item in result.data['results']:
    print(f"📄 {item['file_path']}")
    print(f"📊 Distance: {item['raw_distance']:.4f}")
    print(f"💬 {item['preview'][:100]}...")
    print("-" * 60)
```

### 3️⃣ التجزئة الذكية (Smart Chunking)

```python
# إعدادات التجزئة
CHUNK_SIZE = 6000        # حجم كل جزء (6000 حرف)
CHUNK_OVERLAP = 500      # التداخل بين الأجزاء (500 حرف)

# يضمن التداخل عدم فقدان السياق عند الحدود بين الأجزاء
```

---

## 💻 الاستخدام والأمثلة

### مثال 1: فهرسة المشروع لأول مرة

```python
from app.services.system_service import index_project

# فهرسة كاملة للمشروع
result = index_project(force=True, chunking=True)

if result.ok:
    print("✅ تمت الفهرسة بنجاح!")
    print(f"📊 ملفات جديدة: {result.data['indexed_new']}")
    print(f"📁 إجمالي الملفات: {result.data['total_in_store']}")
    print(f"⏱️ الوقت المستغرق: {result.meta['elapsed_ms']} ms")
else:
    print(f"❌ خطأ: {result.error}")
```

### مثال 2: البحث عن كود متعلق بموضوع معين

```python
from app.services.system_service import find_related_context

# البحث عن وظائف متعلقة بالمستخدمين
query = "user authentication and login functions"
result = find_related_context(query, limit=5)

if result.ok:
    print(f"🔍 وجدنا {result.data['count']} نتائج:")
    for idx, item in enumerate(result.data['results'], 1):
        print(f"\n{idx}. {item['file_path']}")
        print(f"   Distance: {item['raw_distance']:.4f}")
        print(f"   Priority: {'⭐ High' if item['priority_tier'] == 0 else 'Normal'}")
        print(f"   Preview: {item['preview'][:150]}...")
```

### مثال 3: تحديث الفهرس بعد تعديل الملفات

```python
from app.services.system_service import index_project

# فهرسة تدريجية (فقط الملفات المعدلة)
result = index_project(force=False, chunking=True)

if result.ok:
    if result.data['indexed_new'] > 0:
        print(f"✅ تم تحديث {result.data['indexed_new']} ملف")
    else:
        print("ℹ️ لا توجد تغييرات جديدة")
```

### مثال 4: الحصول على معلومات النظام

```python
from app.services.system_service import diagnostics

# معلومات عن حالة النظام
result = diagnostics()

if result.ok:
    print("📊 معلومات النظام:")
    print(f"   Version: {result.data['version']}")
    print(f"   Project Root: {result.data['project_root']}")
    print(f"   Embedding Model Loaded: {result.data['embedding_model_loaded']}")
    print(f"   Cache Enabled: {result.data['cache_enabled']}")
    print(f"   Cache Size: {result.data['cache_size']}")
```

---

## 🔧 التكوين والإعدادات

يمكن تخصيص النظام عبر متغيرات البيئة (Environment Variables):

### إعدادات ملف `.env`

```bash
# === إعدادات قاعدة البيانات ===
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres

# === إعدادات نموذج التضمين ===
EMBED_MODEL_NAME=all-MiniLM-L6-v2
# بدائل متاحة:
# - sentence-transformers/all-MiniLM-L12-v2 (أكبر، أدق)
# - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (متعدد اللغات)

# === إعدادات الفهرسة ===
SYSTEM_SERVICE_CHUNK_SIZE=6000         # حجم الجزء الواحد
SYSTEM_SERVICE_CHUNK_OVERLAP=500       # التداخل بين الأجزاء
SYSTEM_SERVICE_EMBED_BATCH=32          # عدد الأجزاء في الدفعة الواحدة
SYSTEM_SERVICE_MAX_FILE_BYTES=1500000  # الحد الأقصى لحجم الملف (1.5MB)

# === إعدادات الذاكرة المؤقتة ===
SYSTEM_SERVICE_FILE_CACHE=1            # تفعيل الذاكرة المؤقتة
SYSTEM_SERVICE_FILE_CACHE_CAP=64       # سعة الذاكرة المؤقتة

# === امتدادات الملفات المسموحة ===
SYSTEM_SERVICE_ALLOWED_EXT=.py,.md,.txt,.json,.yml,.yaml,.js,.ts,.html,.css,.sh
```

### الملفات والمجلدات المستبعدة

```python
IGNORED_DIRS = {
    "__pycache__",  # ملفات Python المؤقتة
    ".git",         # مجلد Git
    ".idea",        # إعدادات IDE
    "venv",         # البيئة الافتراضية
    ".vscode",      # إعدادات VS Code
    "migrations",   # ملفات الهجرة
    "instance",     # ملفات المثيل
    "tmp",          # ملفات مؤقتة
    "node_modules"  # مكتبات Node.js
}
```

---

## 🚀 الوظائف الرئيسية

### الوظائف العامة (Public API)

#### 1. `index_project(force, chunking)`
فهرسة ملفات المشروع إلى قاعدة البيانات الشعاعية.

**المعاملات:**
- `force` (bool): إعادة فهرسة كل الملفات حتى لو لم تتغير (افتراضي: False)
- `chunking` (bool): تقسيم الملفات الكبيرة إلى أجزاء (افتراضي: True)

**الإرجاع:**
```python
ToolResult(
    ok=True,
    data={
        "indexed_new": 45,      # عدد الملفات/الأجزاء الجديدة
        "total_in_store": 230,  # إجمالي الملفات في القاعدة
        "force": False,
        "chunking": True
    },
    meta={"elapsed_ms": 1234.56}
)
```

#### 2. `find_related_context(prompt_text, limit)`
البحث عن محتوى مشابه دلالياً.

**المعاملات:**
- `prompt_text` (str): نص الاستعلام
- `limit` (int): عدد النتائج المطلوبة (افتراضي: 6)

**الإرجاع:**
```python
ToolResult(
    ok=True,
    data={
        "results": [
            {
                "id": "app/services/user_service.py::0",
                "file_path": "app/services/user_service.py",
                "priority_tier": 0,  # 0 = high priority, 1 = normal
                "raw_distance": 0.234,
                "hybrid_score": 0.245,
                "preview": "def authenticate_user(...)..."
            },
            # ... المزيد من النتائج
        ],
        "count": 6
    },
    meta={"elapsed_ms": 45.67}
)
```

#### 3. `get_embedding_model()`
تحميل نموذج التضمين (singleton pattern).

**الإرجاع:**
- `SentenceTransformer`: نموذج التضمين الجاهز للاستخدام

#### 4. `diagnostics()`
الحصول على معلومات عن حالة النظام.

**الإرجاع:**
```python
ToolResult(
    ok=True,
    data={
        "version": "11.0.0",
        "project_root": "/app",
        "embedding_model_loaded": True,
        "cache_enabled": True,
        "cache_size": 42,
        "allowed_ext_count": 11
    }
)
```

---

## 📈 الأداء والتحسينات

### 1. الفهرسة التدريجية (Incremental Indexing)
- ✅ يتم فهرسة الملفات الجديدة أو المعدلة فقط
- ✅ استخدام hash للتحقق من التغييرات
- ✅ تجنب إعادة فهرسة الملفات غير المعدلة

### 2. الذاكرة المؤقتة (LRU Cache)
- ✅ تخزين الملفات الصغيرة في الذاكرة
- ✅ تقليل عمليات القراءة من القرص
- ✅ سعة قابلة للتكوين (افتراضي: 64 ملف)

### 3. الأولوية المعمارية (Architectural Priority)
- ✅ ملفات `app/services/*` لها أولوية عالية في النتائج
- ✅ ترتيب ذكي للنتائج حسب الأهمية

### 4. فهرس IVFFlat
- ✅ بحث سريع في ملايين المتجهات
- ✅ استهلاك ذاكرة منخفض
- ✅ دقة عالية

---

## 🔍 حالات الاستخدام

### 1. مساعد الكود الذكي (Code Assistant)
```python
# عندما يسأل المستخدم سؤالاً
user_question = "كيف يتم التعامل مع المصادقة؟"

# البحث عن الكود المرتبط
context = find_related_context(user_question, limit=3)

# استخدام السياق لتحسين إجابة الذكاء الاصطناعي
relevant_code = "\n\n".join([r['preview'] for r in context.data['results']])
ai_prompt = f"Based on this code:\n{relevant_code}\n\nAnswer: {user_question}"
```

### 2. تحليل الكود (Code Analysis)
```python
# البحث عن أنماط معينة في الكود
patterns = [
    "database queries",
    "error handling",
    "API endpoints"
]

for pattern in patterns:
    results = find_related_context(pattern, limit=5)
    print(f"\n🔍 {pattern}:")
    for r in results.data['results']:
        print(f"   - {r['file_path']}")
```

### 3. التوثيق التلقائي (Auto Documentation)
```python
# البحث عن كل الوظائف المتعلقة بموضوع معين
topic = "user management functions"
results = find_related_context(topic, limit=10)

# إنشاء توثيق تلقائي
for r in results.data['results']:
    # تحليل الكود وإنشاء التوثيق
    pass
```

---

## 🎓 الخلاصة

مشروع **CogniForge** يحتوي على نظام قاعدة بيانات شعاعية **متطور وكامل المواصفات**:

### ✅ ما يوفره النظام:
- 🔍 بحث دلالي ذكي بدقة عالية
- 📚 فهرسة تلقائية لكود المشروع
- 🚀 أداء عالي مع PostgreSQL + pgvector
- 🧠 نموذج تضمين خفيف وسريع
- 💾 تخزين فعال للمتجهات
- 🔄 تحديثات تدريجية ذكية

### 🛠️ التقنيات:
- **PostgreSQL 15.1** + **pgvector extension**
- **SentenceTransformers** (all-MiniLM-L6-v2)
- **IVFFlat Index** للبحث السريع
- **Cosine Similarity** لقياس التشابه

### 📂 الموقع في الكود:
- الملف الرئيسي: `app/services/system_service.py`
- الوظائف: `index_project()`, `find_related_context()`
- التكوين: عبر متغيرات البيئة في `.env`

---

## 📞 الدعم والمساعدة

إذا كنت بحاجة إلى مساعدة إضافية، راجع:
- 📄 `app/services/system_service.py` - الكود المصدري
- 📄 `houssam.md` - تقرير تحليل المشروع
- 📄 `docker-compose.yml` - إعدادات قاعدة البيانات

---

**🎉 نظام قاعدة البيانات الشعاعية جاهز ويعمل بكفاءة عالية!**
