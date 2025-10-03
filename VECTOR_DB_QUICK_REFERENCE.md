# 🚀 دليل سريع لقاعدة البيانات الشعاعية | Vector Database Quick Reference

> دليل مرجعي سريع باللغتين العربية والإنجليزية
> Quick reference guide in both Arabic and English

---

## 🎯 الإجابة السريعة | Quick Answer

### العربية
**نعم! ✅** يوجد نظام قاعدة بيانات شعاعية (Vector Database) كامل ومتكامل في المشروع.

**الموقع:** `app/services/system_service.py`

**التقنيات:**
- PostgreSQL 15.1 + pgvector extension
- SentenceTransformers (all-MiniLM-L6-v2)
- 384-dimensional vectors
- IVFFlat index for fast search

### English
**Yes! ✅** There is a complete and integrated Vector Database system in the project.

**Location:** `app/services/system_service.py`

**Technologies:**
- PostgreSQL 15.1 + pgvector extension
- SentenceTransformers (all-MiniLM-L6-v2)
- 384-dimensional vectors
- IVFFlat index for fast search

---

## 📋 الأوامر السريعة | Quick Commands

### فهرسة المشروع | Index Project

```python
from app.services.system_service import index_project

# فهرسة كاملة | Full indexing
result = index_project(force=True, chunking=True)

# فهرسة تدريجية (الملفات المعدلة فقط) | Incremental (modified files only)
result = index_project(force=False, chunking=True)
```

### البحث الدلالي | Semantic Search

```python
from app.services.system_service import find_related_context

# البحث | Search
query = "authentication functions"
result = find_related_context(query, limit=6)

# عرض النتائج | Display results
for item in result.data['results']:
    print(f"{item['file_path']}: {item['raw_distance']:.4f}")
```

### معلومات النظام | System Info

```python
from app.services.system_service import diagnostics

result = diagnostics()
print(result.data)
```

---

## 🏗️ هيكل الجدول | Table Structure

```sql
-- الجدول الرئيسي | Main table
code_documents (
    id,              -- معرف فريد | Unique ID
    file_path,       -- مسار الملف | File path
    chunk_index,     -- رقم الجزء | Chunk number
    content,         -- المحتوى | Content
    file_hash,       -- هاش الملف | File hash
    chunk_hash,      -- هاش الجزء | Chunk hash
    source,          -- المصدر | Source
    embedding,       -- المتجه (384 بُعد) | Vector (384-dim)
    updated_at       -- التحديث | Updated timestamp
)
```

---

## ⚙️ الإعدادات | Configuration

### ملف البيئة | Environment File (`.env`)

```bash
# قاعدة البيانات | Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres

# نموذج التضمين | Embedding Model
EMBED_MODEL_NAME=all-MiniLM-L6-v2

# إعدادات الفهرسة | Indexing Settings
SYSTEM_SERVICE_CHUNK_SIZE=6000           # حجم الجزء | Chunk size
SYSTEM_SERVICE_CHUNK_OVERLAP=500         # التداخل | Overlap
SYSTEM_SERVICE_EMBED_BATCH=32            # حجم الدفعة | Batch size
SYSTEM_SERVICE_MAX_FILE_BYTES=1500000    # حد الحجم | Size limit

# الذاكرة المؤقتة | Cache
SYSTEM_SERVICE_FILE_CACHE=1              # تفعيل | Enable
SYSTEM_SERVICE_FILE_CACHE_CAP=64         # السعة | Capacity

# الامتدادات المسموحة | Allowed Extensions
SYSTEM_SERVICE_ALLOWED_EXT=.py,.md,.txt,.json,.yml,.yaml,.js,.ts,.html,.css,.sh
```

---

## 🔍 أمثلة الاستخدام | Usage Examples

### مثال 1: فهرسة وبحث | Example 1: Index & Search

```python
from app.services.system_service import index_project, find_related_context

# الخطوة 1: فهرسة المشروع | Step 1: Index project
index_result = index_project(force=True, chunking=True)
print(f"✅ Indexed {index_result.data['indexed_new']} files")

# الخطوة 2: البحث | Step 2: Search
search_result = find_related_context("user authentication", limit=5)
for item in search_result.data['results']:
    print(f"📄 {item['file_path']}")
    print(f"   Distance: {item['raw_distance']:.4f}")
    print(f"   {item['preview'][:100]}...")
```

### مثال 2: مساعد الكود | Example 2: Code Assistant

```python
from app.services.system_service import find_related_context

def get_code_context(user_question: str) -> str:
    """
    الحصول على سياق الكود للسؤال
    Get code context for a question
    """
    result = find_related_context(user_question, limit=3)
    
    if result.ok:
        context_parts = []
        for item in result.data['results']:
            context_parts.append(f"File: {item['file_path']}\n{item['preview']}")
        return "\n\n---\n\n".join(context_parts)
    return ""

# الاستخدام | Usage
question = "How does the system handle errors?"
context = get_code_context(question)
print(f"Context for '{question}':\n{context}")
```

### مثال 3: تحديث تدريجي | Example 3: Incremental Update

```python
from app.services.system_service import index_project
import time

def auto_update_index():
    """
    تحديث الفهرس تلقائياً كل ساعة
    Auto-update index every hour
    """
    while True:
        result = index_project(force=False, chunking=True)
        
        if result.ok:
            new_count = result.data['indexed_new']
            if new_count > 0:
                print(f"✅ Updated {new_count} files at {time.ctime()}")
            else:
                print(f"ℹ️ No changes at {time.ctime()}")
        
        time.sleep(3600)  # انتظر ساعة | Wait 1 hour
```

---

## 📊 بنية الإرجاع | Return Structure

### ToolResult للفهرسة | ToolResult for Indexing

```python
{
    "ok": True,
    "data": {
        "indexed_new": 45,        # ملفات جديدة | New files
        "total_in_store": 230,    # الإجمالي | Total
        "force": False,
        "chunking": True
    },
    "meta": {
        "elapsed_ms": 1234.56     # الوقت | Time
    }
}
```

### ToolResult للبحث | ToolResult for Search

```python
{
    "ok": True,
    "data": {
        "results": [
            {
                "id": "app/services/user_service.py::0",
                "file_path": "app/services/user_service.py",
                "priority_tier": 0,      # 0=عالي | 0=high, 1=عادي | 1=normal
                "raw_distance": 0.234,   # المسافة | Distance
                "hybrid_score": 0.245,   # النتيجة | Score
                "preview": "def auth..."  # المعاينة | Preview
            }
        ],
        "count": 6
    },
    "meta": {
        "elapsed_ms": 45.67
    }
}
```

---

## 🎯 الوظائف الرئيسية | Main Functions

| الوظيفة<br>Function | الوصف<br>Description | المعاملات<br>Parameters |
|---------------------|---------------------|-------------------------|
| `index_project()` | فهرسة الملفات<br>Index files | `force`, `chunking` |
| `find_related_context()` | البحث الدلالي<br>Semantic search | `prompt_text`, `limit` |
| `get_embedding_model()` | تحميل النموذج<br>Load model | - |
| `diagnostics()` | معلومات النظام<br>System info | - |

---

## 🚀 الأداء | Performance

### الفهرسة التدريجية | Incremental Indexing
- ✅ فهرسة الملفات المعدلة فقط | Only modified files
- ✅ استخدام hash للتحقق | Hash-based verification
- ✅ سرعة عالية | High speed

### الذاكرة المؤقتة | Cache
- ✅ LRU Cache للملفات الصغيرة | For small files
- ✅ تقليل عمليات القراءة | Reduce reads
- ✅ سعة قابلة للتكوين | Configurable capacity

### البحث السريع | Fast Search
- ✅ فهرس IVFFlat | IVFFlat index
- ✅ Cosine similarity
- ✅ أولوية `app/services/*` | Priority for `app/services/*`

---

## 📂 الملفات المهمة | Important Files

| الملف<br>File | الوصف<br>Description |
|--------------|---------------------|
| `app/services/system_service.py` | الكود الرئيسي<br>Main code |
| `VECTOR_DATABASE_GUIDE_AR.md` | الدليل الكامل بالعربية<br>Full guide in Arabic |
| `VECTOR_DATABASE_GUIDE.md` | الدليل الكامل بالإنجليزية<br>Full guide in English |
| `docker-compose.yml` | إعدادات PostgreSQL<br>PostgreSQL config |
| `requirements.txt` | المكتبات المطلوبة<br>Required libraries |

---

## 🐛 استكشاف الأخطاء | Troubleshooting

### المشكلة: "Model not loaded"
```python
# الحل | Solution
from app.services.system_service import get_embedding_model
model = get_embedding_model()  # تحميل النموذج | Load model
```

### المشكلة: "Database connection failed"
```bash
# تحقق من إعدادات قاعدة البيانات | Check database settings
echo $DATABASE_URL

# تحقق من تشغيل PostgreSQL | Check PostgreSQL is running
docker ps | grep postgres
```

### المشكلة: "No results found"
```python
# تأكد من فهرسة المشروع أولاً | Make sure to index first
from app.services.system_service import index_project
result = index_project(force=True, chunking=True)
```

---

## 📚 مصادر إضافية | Additional Resources

### التوثيق | Documentation
- 📄 [VECTOR_DATABASE_GUIDE_AR.md](VECTOR_DATABASE_GUIDE_AR.md) - الدليل الكامل بالعربية
- 📄 [VECTOR_DATABASE_GUIDE.md](VECTOR_DATABASE_GUIDE.md) - Full guide in English
- 📄 [houssam.md](houssam.md) - تقرير تحليل المشروع

### الكود المصدري | Source Code
- 📄 `app/services/system_service.py` - Implementation
- 📄 `app/cli/indexer.py` - CLI indexer
- 📄 `app/cli/search.py` - CLI search

---

## ✅ قائمة التحقق | Checklist

### للبدء | Getting Started
- [ ] تثبيت المتطلبات | Install requirements: `pip install -r requirements.txt`
- [ ] تشغيل PostgreSQL | Start PostgreSQL: `docker-compose up -d db`
- [ ] فهرسة المشروع | Index project: `index_project(force=True)`
- [ ] اختبار البحث | Test search: `find_related_context("test")`

### للصيانة | Maintenance
- [ ] تحديث الفهرس دورياً | Update index regularly
- [ ] مراقبة حجم قاعدة البيانات | Monitor database size
- [ ] تنظيف السجلات القديمة | Clean old records
- [ ] نسخ احتياطي للبيانات | Backup data

---

## 🎉 الخلاصة | Summary

### العربية
نظام قاعدة البيانات الشعاعية في CogniForge هو نظام **متطور وكامل** يوفر:
- بحث دلالي ذكي بدقة عالية
- فهرسة تلقائية للكود
- أداء عالي وسرعة في الاستجابة
- سهولة في الاستخدام والتكوين

### English
The Vector Database system in CogniForge is an **advanced and complete** system that provides:
- High-accuracy semantic search
- Automatic code indexing
- High performance and fast response
- Easy to use and configure

---

**🚀 Happy Coding! | برمجة سعيدة!**
