# 📚 Vector Database Documentation Index

> **Answer to: "هل توجد قاعدة بيانات vector DB في المشروع"**
> 
> **نعم! ✅ Yes!** - The CogniForge project has a complete Vector Database system

---

## 📖 Available Documentation

This directory contains comprehensive documentation about the Vector Database implementation in the CogniForge project.

### 📄 Full Guides

1. **[VECTOR_DATABASE_GUIDE_AR.md](VECTOR_DATABASE_GUIDE_AR.md)** 🇸🇦
   - **دليل شامل بالعربية** - Complete guide in Arabic
   - Detailed architecture explanation
   - Usage examples and code snippets
   - Configuration and settings
   - Use cases and best practices

2. **[VECTOR_DATABASE_GUIDE.md](VECTOR_DATABASE_GUIDE.md)** 🇬🇧
   - **Complete guide in English**
   - Detailed architecture explanation
   - Usage examples and code snippets
   - Configuration and settings
   - Use cases and best practices

3. **[VECTOR_DB_QUICK_REFERENCE.md](VECTOR_DB_QUICK_REFERENCE.md)** 🚀
   - **Bilingual quick reference** (Arabic & English)
   - Quick commands and examples
   - Cheat sheet format
   - Troubleshooting guide

---

## 🎯 Quick Answer

### What is it?
The CogniForge project includes a **Vector Database** system that enables:
- 🔍 **Semantic Search** - Find code by meaning, not just keywords
- 📚 **Context Retrieval** - Get relevant code snippets for AI responses
- 🧩 **Code Indexing** - Automatically index project files
- 🤖 **AI Enhancement** - Improve AI assistant responses with relevant context

### Technologies Used
- **PostgreSQL 15.1** with **pgvector** extension
- **SentenceTransformers** (all-MiniLM-L6-v2)
- **384-dimensional vectors**
- **IVFFlat index** for fast similarity search
- **Cosine similarity** for semantic matching

### Where is it?
- **Main implementation**: `app/services/system_service.py`
- **Database table**: `code_documents`
- **Key functions**: `index_project()`, `find_related_context()`

---

## 🚀 Quick Start

### 1. Index Your Project
```python
from app.services.system_service import index_project

# Index all files
result = index_project(force=True, chunking=True)
print(f"Indexed {result.data['indexed_new']} files")
```

### 2. Search for Code
```python
from app.services.system_service import find_related_context

# Search semantically
result = find_related_context("authentication functions", limit=5)
for item in result.data['results']:
    print(f"📄 {item['file_path']}: {item['raw_distance']:.4f}")
```

### 3. Get System Info
```python
from app.services.system_service import diagnostics

info = diagnostics()
print(info.data)
```

---

## 📊 Architecture Overview

```
Project Files → Text Chunking → Embedding Model → PostgreSQL+pgvector
                                                          ↓
User Query → Embedding → Similarity Search → Ranked Results
```

**Table Structure:**
```sql
code_documents (
    id,              -- Unique identifier
    file_path,       -- Path to file
    chunk_index,     -- Chunk number
    content,         -- Text content
    file_hash,       -- File hash for change detection
    chunk_hash,      -- Chunk hash for deduplication
    source,          -- Source identifier
    embedding,       -- 384-dimensional vector
    updated_at       -- Last update timestamp
)
```

---

## 📚 Documentation Guide

### For Detailed Information
Read the full guides:
- [Arabic Guide](VECTOR_DATABASE_GUIDE_AR.md) for comprehensive Arabic documentation
- [English Guide](VECTOR_DATABASE_GUIDE.md) for comprehensive English documentation

### For Quick Reference
Check the quick reference:
- [Quick Reference](VECTOR_DB_QUICK_REFERENCE.md) for commands and examples in both languages

### Topics Covered

#### In the Full Guides:
- ✅ **Overview** - What is the Vector Database and why use it
- ✅ **Technologies** - PostgreSQL, pgvector, SentenceTransformers
- ✅ **Architecture** - Database schema, indexing strategy
- ✅ **How It Works** - Indexing, search, chunking processes
- ✅ **Usage Examples** - Code snippets for common tasks
- ✅ **Configuration** - Environment variables and settings
- ✅ **API Reference** - All functions and their parameters
- ✅ **Performance** - Optimization strategies
- ✅ **Use Cases** - Real-world applications

#### In the Quick Reference:
- ✅ **Quick Commands** - Copy-paste ready code
- ✅ **Configuration** - Essential settings
- ✅ **Examples** - Common usage patterns
- ✅ **Troubleshooting** - Common issues and solutions
- ✅ **Checklist** - Setup and maintenance tasks

---

## 🔧 Configuration

The Vector Database can be configured via environment variables in your `.env` file:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/postgres

# Embedding Model
EMBED_MODEL_NAME=all-MiniLM-L6-v2

# Indexing Settings
SYSTEM_SERVICE_CHUNK_SIZE=6000
SYSTEM_SERVICE_CHUNK_OVERLAP=500
SYSTEM_SERVICE_EMBED_BATCH=32
SYSTEM_SERVICE_MAX_FILE_BYTES=1500000

# Cache Settings
SYSTEM_SERVICE_FILE_CACHE=1
SYSTEM_SERVICE_FILE_CACHE_CAP=64

# Allowed Extensions
SYSTEM_SERVICE_ALLOWED_EXT=.py,.md,.txt,.json,.yml,.yaml,.js,.ts,.html,.css,.sh
```

---

## 🎓 Learning Path

### Beginner
1. Read the **Quick Answer** section above
2. Try the **Quick Start** examples
3. Check the **Quick Reference** for common commands

### Intermediate
1. Read the full guide in your preferred language
2. Understand the architecture and how it works
3. Experiment with different configurations
4. Try the usage examples

### Advanced
1. Study the source code in `app/services/system_service.py`
2. Customize the embedding model or chunking strategy
3. Optimize performance for your specific use case
4. Integrate with other services

---

## 📂 Related Files

### Source Code
- `app/services/system_service.py` - Main implementation
- `app/cli/indexer.py` - CLI indexer
- `app/cli/search.py` - CLI search

### Configuration
- `docker-compose.yml` - PostgreSQL configuration
- `requirements.txt` - Python dependencies
- `.env` - Environment variables

### Other Documentation
- `houssam.md` - Project analysis report (Arabic)
- `DATABASE_GUIDE_AR.md` - Database guide (Arabic)
- `SUPABASE_VERIFICATION_GUIDE_AR.md` - Database verification

---

## 🎉 Summary

The CogniForge project has a **complete, production-ready Vector Database system** that provides:

✅ **Semantic search** with high accuracy  
✅ **Automatic code indexing** for all project files  
✅ **High performance** using PostgreSQL + pgvector  
✅ **Smart chunking** for long documents  
✅ **Incremental updates** - only index what changed  
✅ **Easy configuration** via environment variables  
✅ **Simple API** - just a few functions to use  

**Choose your documentation:**
- 🇸🇦 [Arabic Guide](VECTOR_DATABASE_GUIDE_AR.md)
- 🇬🇧 [English Guide](VECTOR_DATABASE_GUIDE.md)
- 🚀 [Quick Reference](VECTOR_DB_QUICK_REFERENCE.md) (Bilingual)

---

**Happy coding! | برمجة سعيدة! 🚀**
