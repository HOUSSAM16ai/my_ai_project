# 🧠 Vector Database Guide - CogniForge Project

## Yes, there is a complete Vector Database system in the project! ✅

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Technologies Used](#technologies-used)
3. [Architecture](#architecture)
4. [How It Works](#how-it-works)
5. [Usage Examples](#usage-examples)
6. [Configuration](#configuration)
7. [Main Functions](#main-functions)

---

## 🎯 Overview

The **CogniForge** project includes an advanced and complete Vector Database system used for:

- 🔍 **Semantic Search**
- 📚 **Context Storage and Retrieval**
- 🧩 **Intelligent Code Indexing**
- 🤖 **AI Response Enhancement**

### ✨ Key Features

- ✅ **PostgreSQL Database** with **pgvector** extension
- ✅ **Advanced Embedding Model** (SentenceTransformers - all-MiniLM-L6-v2)
- ✅ **Incremental Indexing**
- ✅ **Cosine Similarity Search**
- ✅ **Text Chunking**
- ✅ **LRU Cache**

---

## 🛠️ Technologies Used

### 1. Database
```yaml
Database: PostgreSQL 15.1.0.118
Extension: pgvector (vector similarity search)
Image: supabase/postgres:15.1.0.118
Port: 5432
```

### 2. Embedding Model
```yaml
Model: all-MiniLM-L6-v2
Library: sentence-transformers >= 2.6.1
Vector Dimension: 384
Performance: Fast and lightweight (only 80MB)
```

### 3. Core Libraries
```python
- sentence-transformers >= 2.6.1  # For embeddings
- SQLAlchemy                       # Database interaction
- pgvector                         # PostgreSQL extension
```

---

## 🏗️ Architecture

### `code_documents` Table Structure

```sql
CREATE TABLE code_documents (
    id TEXT PRIMARY KEY,              -- Unique ID (file_path::chunk_index)
    file_path TEXT,                   -- File path
    chunk_index INT,                  -- Chunk number
    content TEXT,                     -- Text content
    file_hash TEXT,                   -- Complete file hash
    chunk_hash TEXT,                  -- Chunk hash
    source TEXT,                      -- Content source
    embedding vector(384),            -- Vector embedding (384 dimensions)
    updated_at TIMESTAMP              -- Update timestamp
);

-- High-performance indexes
CREATE INDEX idx_code_documents_file_path 
    ON code_documents(file_path);

CREATE INDEX idx_code_documents_embedding 
    ON code_documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

### 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Vector Database Architecture                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │  Project     │ ───▶ │  Text        │                    │
│  │  Files       │      │  Chunking    │                    │
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
│  │  User        │──▶│  Search      │──▶│  Most        │   │
│  │  Query       │   │  (Cosine)    │   │  Similar     │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ How It Works

### 1️⃣ Indexing

Converting project files into vector embeddings:

```python
# Steps:
1. Read project files (.py, .md, .txt, .json, etc.)
2. Split long texts into chunks (6000 characters each)
3. Calculate hash for each chunk to detect changes
4. Convert each chunk to a vector embedding (384 dimensions)
5. Store vectors in PostgreSQL
6. Build IVFFlat index for fast search
```

**Code Example:**
```python
from app.services.system_service import index_project

# Index the project
result = index_project(force=False, chunking=True)
print(f"Indexed {result.data['indexed_new']} new files")
print(f"Total files: {result.data['total_in_store']}")
```

### 2️⃣ Semantic Search

Search for similar content using semantic similarity:

```python
# Steps:
1. Receive query text from user
2. Convert query to vector embedding
3. Calculate cosine similarity with all stored vectors
4. Return most similar results
5. Prioritize results (app/services/* has priority)
```

**Code Example:**
```python
from app.services.system_service import find_related_context

# Search for related context
query = "How is data processed in the system?"
result = find_related_context(query, limit=6)

for item in result.data['results']:
    print(f"📄 {item['file_path']}")
    print(f"📊 Distance: {item['raw_distance']:.4f}")
    print(f"💬 {item['preview'][:100]}...")
    print("-" * 60)
```

### 3️⃣ Smart Chunking

```python
# Chunking settings
CHUNK_SIZE = 6000        # Size of each chunk (6000 characters)
CHUNK_OVERLAP = 500      # Overlap between chunks (500 characters)

# Overlap ensures no context is lost at chunk boundaries
```

---

## 💻 Usage Examples

### Example 1: Index Project for First Time

```python
from app.services.system_service import index_project

# Full project indexing
result = index_project(force=True, chunking=True)

if result.ok:
    print("✅ Indexing successful!")
    print(f"📊 New files: {result.data['indexed_new']}")
    print(f"📁 Total files: {result.data['total_in_store']}")
    print(f"⏱️ Time taken: {result.meta['elapsed_ms']} ms")
else:
    print(f"❌ Error: {result.error}")
```

### Example 2: Search for Related Code

```python
from app.services.system_service import find_related_context

# Search for user-related functions
query = "user authentication and login functions"
result = find_related_context(query, limit=5)

if result.ok:
    print(f"🔍 Found {result.data['count']} results:")
    for idx, item in enumerate(result.data['results'], 1):
        print(f"\n{idx}. {item['file_path']}")
        print(f"   Distance: {item['raw_distance']:.4f}")
        print(f"   Priority: {'⭐ High' if item['priority_tier'] == 0 else 'Normal'}")
        print(f"   Preview: {item['preview'][:150]}...")
```

### Example 3: Update Index After File Changes

```python
from app.services.system_service import index_project

# Incremental indexing (only modified files)
result = index_project(force=False, chunking=True)

if result.ok:
    if result.data['indexed_new'] > 0:
        print(f"✅ Updated {result.data['indexed_new']} files")
    else:
        print("ℹ️ No new changes")
```

### Example 4: Get System Information

```python
from app.services.system_service import diagnostics

# System status information
result = diagnostics()

if result.ok:
    print("📊 System Information:")
    print(f"   Version: {result.data['version']}")
    print(f"   Project Root: {result.data['project_root']}")
    print(f"   Embedding Model Loaded: {result.data['embedding_model_loaded']}")
    print(f"   Cache Enabled: {result.data['cache_enabled']}")
    print(f"   Cache Size: {result.data['cache_size']}")
```

---

## 🔧 Configuration

Customize the system via environment variables:

### `.env` File Settings

```bash
# === Database Settings ===
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres

# === Embedding Model Settings ===
EMBED_MODEL_NAME=all-MiniLM-L6-v2
# Available alternatives:
# - sentence-transformers/all-MiniLM-L12-v2 (larger, more accurate)
# - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (multilingual)

# === Indexing Settings ===
SYSTEM_SERVICE_CHUNK_SIZE=6000         # Chunk size
SYSTEM_SERVICE_CHUNK_OVERLAP=500       # Overlap between chunks
SYSTEM_SERVICE_EMBED_BATCH=32          # Chunks per batch
SYSTEM_SERVICE_MAX_FILE_BYTES=1500000  # Max file size (1.5MB)

# === Cache Settings ===
SYSTEM_SERVICE_FILE_CACHE=1            # Enable cache
SYSTEM_SERVICE_FILE_CACHE_CAP=64       # Cache capacity

# === Allowed File Extensions ===
SYSTEM_SERVICE_ALLOWED_EXT=.py,.md,.txt,.json,.yml,.yaml,.js,.ts,.html,.css,.sh
```

### Excluded Files and Directories

```python
IGNORED_DIRS = {
    "__pycache__",  # Python temporary files
    ".git",         # Git folder
    ".idea",        # IDE settings
    "venv",         # Virtual environment
    ".vscode",      # VS Code settings
    "migrations",   # Migration files
    "instance",     # Instance files
    "tmp",          # Temporary files
    "node_modules"  # Node.js libraries
}
```

---

## 🚀 Main Functions

### Public API

#### 1. `index_project(force, chunking)`
Index project files into the vector database.

**Parameters:**
- `force` (bool): Re-index all files even if unchanged (default: False)
- `chunking` (bool): Split large files into chunks (default: True)

**Returns:**
```python
ToolResult(
    ok=True,
    data={
        "indexed_new": 45,      # Number of new files/chunks
        "total_in_store": 230,  # Total files in database
        "force": False,
        "chunking": True
    },
    meta={"elapsed_ms": 1234.56}
)
```

#### 2. `find_related_context(prompt_text, limit)`
Search for semantically similar content.

**Parameters:**
- `prompt_text` (str): Query text
- `limit` (int): Number of results to return (default: 6)

**Returns:**
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
            # ... more results
        ],
        "count": 6
    },
    meta={"elapsed_ms": 45.67}
)
```

#### 3. `get_embedding_model()`
Load the embedding model (singleton pattern).

**Returns:**
- `SentenceTransformer`: Ready-to-use embedding model

#### 4. `diagnostics()`
Get system status information.

**Returns:**
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

## 📈 Performance & Optimizations

### 1. Incremental Indexing
- ✅ Only index new or modified files
- ✅ Use hash to detect changes
- ✅ Avoid re-indexing unchanged files

### 2. LRU Cache
- ✅ Store small files in memory
- ✅ Reduce disk read operations
- ✅ Configurable capacity (default: 64 files)

### 3. Architectural Priority
- ✅ Files in `app/services/*` have high priority in results
- ✅ Smart ranking by importance

### 4. IVFFlat Index
- ✅ Fast search across millions of vectors
- ✅ Low memory consumption
- ✅ High accuracy

---

## 🔍 Use Cases

### 1. Intelligent Code Assistant
```python
# When user asks a question
user_question = "How is authentication handled?"

# Search for related code
context = find_related_context(user_question, limit=3)

# Use context to enhance AI response
relevant_code = "\n\n".join([r['preview'] for r in context.data['results']])
ai_prompt = f"Based on this code:\n{relevant_code}\n\nAnswer: {user_question}"
```

### 2. Code Analysis
```python
# Search for specific patterns in code
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

### 3. Auto Documentation
```python
# Search for all functions related to a topic
topic = "user management functions"
results = find_related_context(topic, limit=10)

# Generate automatic documentation
for r in results.data['results']:
    # Analyze code and generate documentation
    pass
```

---

## 🎓 Summary

The **CogniForge** project contains an **advanced and fully-featured** Vector Database system:

### ✅ What the System Provides:
- 🔍 High-accuracy semantic search
- 📚 Automatic code indexing
- 🚀 High performance with PostgreSQL + pgvector
- 🧠 Lightweight and fast embedding model
- 💾 Efficient vector storage
- 🔄 Smart incremental updates

### 🛠️ Technologies:
- **PostgreSQL 15.1** + **pgvector extension**
- **SentenceTransformers** (all-MiniLM-L6-v2)
- **IVFFlat Index** for fast search
- **Cosine Similarity** for similarity measurement

### 📂 Code Location:
- Main file: `app/services/system_service.py`
- Functions: `index_project()`, `find_related_context()`
- Configuration: Via environment variables in `.env`

---

## 📞 Support

For additional help, refer to:
- 📄 `app/services/system_service.py` - Source code
- 📄 `houssam.md` - Project analysis report
- 📄 `docker-compose.yml` - Database configuration

---

**🎉 The Vector Database system is ready and running at high efficiency!**
