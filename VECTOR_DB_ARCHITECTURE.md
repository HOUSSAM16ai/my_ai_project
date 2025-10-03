# 🎨 Vector Database Architecture Diagram

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CogniForge Vector Database System                     │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    1. INDEXING PHASE                             │   │
│  │                                                                   │   │
│  │  📁 Project Files (.py, .md, .txt, .json, etc.)                 │   │
│  │         │                                                         │   │
│  │         ├──▶ File Reader (UTF-8)                                │   │
│  │         │         │                                              │   │
│  │         │         ├──▶ Binary Detection ❌ Skip                 │   │
│  │         │         ├──▶ Size Check (> 1.5MB) ❌ Skip             │   │
│  │         │         └──▶ Extension Filter ✅ Process              │   │
│  │         │                                                         │   │
│  │         ▼                                                         │   │
│  │  ┌─────────────┐                                                 │   │
│  │  │   Text      │  CHUNK_SIZE = 6000 chars                       │   │
│  │  │   Chunking  │  CHUNK_OVERLAP = 500 chars                     │   │
│  │  └──────┬──────┘                                                 │   │
│  │         │                                                         │   │
│  │         ▼                                                         │   │
│  │  ┌─────────────┐                                                 │   │
│  │  │   Hash      │  file_hash = SHA256(full_text)                 │   │
│  │  │ Calculation │  chunk_hash = SHA256(chunk_text)               │   │
│  │  └──────┬──────┘                                                 │   │
│  │         │                                                         │   │
│  │         ├──▶ Compare with existing hashes                        │   │
│  │         │    (Incremental indexing - skip unchanged)             │   │
│  │         │                                                         │   │
│  │         ▼                                                         │   │
│  │  ┌─────────────────────────────────────┐                        │   │
│  │  │   Embedding Model (SentenceTransformers) │                   │   │
│  │  │   Model: all-MiniLM-L6-v2           │                        │   │
│  │  │   Input: Text chunks                │                        │   │
│  │  │   Output: 384-dim vectors           │                        │   │
│  │  │   Batch Size: 32 chunks             │                        │   │
│  │  └──────────┬──────────────────────────┘                        │   │
│  │             │                                                     │   │
│  │             ▼                                                     │   │
│  │  ┌─────────────────────────────────────┐                        │   │
│  │  │   PostgreSQL + pgvector             │                        │   │
│  │  │   Table: code_documents             │                        │   │
│  │  │   ┌──────────────────────────────┐  │                        │   │
│  │  │   │ id: text (PK)                │  │                        │   │
│  │  │   │ file_path: text              │  │                        │   │
│  │  │   │ chunk_index: int             │  │                        │   │
│  │  │   │ content: text                │  │                        │   │
│  │  │   │ file_hash: text              │  │                        │   │
│  │  │   │ chunk_hash: text             │  │                        │   │
│  │  │   │ source: text                 │  │                        │   │
│  │  │   │ embedding: vector(384) 🔍   │  │                        │   │
│  │  │   │ updated_at: timestamp        │  │                        │   │
│  │  │   └──────────────────────────────┘  │                        │   │
│  │  │                                      │                        │   │
│  │  │   Indexes:                           │                        │   │
│  │  │   - idx_file_path (B-tree)          │                        │   │
│  │  │   - idx_embedding (IVFFlat) 🚀      │                        │   │
│  │  └─────────────────────────────────────┘                        │   │
│  └───────────────────────────────────────────────────────────────────┘
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    2. SEARCH PHASE                               │   │
│  │                                                                   │   │
│  │  💬 User Query: "authentication functions"                      │   │
│  │         │                                                         │   │
│  │         ▼                                                         │   │
│  │  ┌─────────────────────────────────────┐                        │   │
│  │  │   Embedding Model                   │                        │   │
│  │  │   Convert query to 384-dim vector   │                        │   │
│  │  └──────────┬──────────────────────────┘                        │   │
│  │             │                                                     │   │
│  │             ▼                                                     │   │
│  │  ┌─────────────────────────────────────┐                        │   │
│  │  │   PostgreSQL Vector Search          │                        │   │
│  │  │   SELECT * FROM code_documents      │                        │   │
│  │  │   ORDER BY embedding <=> query      │                        │   │
│  │  │   (Cosine Distance Operator)        │                        │   │
│  │  └──────────┬──────────────────────────┘                        │   │
│  │             │                                                     │   │
│  │             ▼                                                     │   │
│  │  ┌─────────────────────────────────────┐                        │   │
│  │  │   Re-ranking & Prioritization       │                        │   │
│  │  │   - app/services/* → High priority  │                        │   │
│  │  │   - Hybrid scoring                  │                        │   │
│  │  │   - Length penalty                  │                        │   │
│  │  └──────────┬──────────────────────────┘                        │   │
│  │             │                                                     │   │
│  │             ▼                                                     │   │
│  │  📊 Ranked Results (Top K)                                      │   │
│  │     1. app/services/user_service.py - Distance: 0.23            │   │
│  │     2. app/services/auth_service.py - Distance: 0.31            │   │
│  │     3. app/models/user.py - Distance: 0.45                      │   │
│  │     ...                                                          │   │
│  └───────────────────────────────────────────────────────────────────┘
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. File Processing Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Read      │───▶│   Filter    │───▶│   Chunk     │───▶│   Hash      │
│   Files     │    │   & Skip    │    │   Text      │    │   Content   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
                                                                  ▼
                                                         ┌─────────────┐
                                                         │  Incremental│
                                                         │  Check      │
                                                         └──────┬──────┘
                                                                │
                    New/Modified Only ◀─────────────────────────┘
                           │
                           ▼
                  ┌─────────────┐
                  │  Embedding  │
                  │  Model      │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │  PostgreSQL │
                  │  Storage    │
                  └─────────────┘
```

### 2. Vector Search Flow

```
┌──────────────────┐
│  User Query      │
│  "find auth..."  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Encode to       │
│  Vector (384-D)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  PostgreSQL Vector Operations        │
│  ┌────────────────────────────────┐  │
│  │  IVFFlat Index Lookup          │  │
│  │  (Fast Approximate Search)     │  │
│  └────────┬───────────────────────┘  │
│           │                           │
│           ▼                           │
│  ┌────────────────────────────────┐  │
│  │  Cosine Distance Calculation   │  │
│  │  embedding <=> query_vector    │  │
│  └────────┬───────────────────────┘  │
│           │                           │
│           ▼                           │
│  ┌────────────────────────────────┐  │
│  │  Sort by Distance (ASC)        │  │
│  │  Return Top K Results          │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Re-ranking      │
│  & Prioritization│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Final Results   │
└──────────────────┘
```

### 3. Database Schema Visualization

```
code_documents Table
┌────────────────────────────────────────────────────────┐
│                                                        │
│  Primary Key: id (file_path::chunk_index)             │
│  ┌──────────────────────────────────────────────────┐ │
│  │ id                "app/services/user.py::0"      │ │
│  │ file_path         "app/services/user.py"         │ │
│  │ chunk_index       0                              │ │
│  │ content           "def authenticate_user..."     │ │
│  │ file_hash         "a1b2c3d4..."                  │ │
│  │ chunk_hash        "e5f6g7h8..."                  │ │
│  │ source            "app/services/user.py"         │ │
│  │ embedding         [0.123, -0.456, 0.789, ...]    │ │
│  │                   ↑                              │ │
│  │                   384 dimensions                 │ │
│  │ updated_at        2024-01-15 10:30:00            │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  Indexes:                                              │
│  ┌──────────────────────────────────────────────────┐ │
│  │ 🔍 idx_code_documents_file_path (B-tree)        │ │
│  │    - Fast file lookup                            │ │
│  │                                                  │ │
│  │ 🚀 idx_code_documents_embedding (IVFFlat)       │ │
│  │    - Vector similarity search                    │ │
│  │    - lists = 100                                 │ │
│  │    - Operator: vector_cosine_ops (<=>)          │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Indexing Performance
```
File Type       | Processing Speed | Notes
----------------|------------------|---------------------------
Small (<10KB)   | ~50-100 files/s  | Cached in LRU
Medium (10-100KB)| ~20-40 files/s  | Standard processing
Large (>100KB)  | ~5-10 files/s    | Chunked into multiple parts
```

### Search Performance
```
Database Size   | Search Latency  | Notes
----------------|-----------------|---------------------------
< 1K vectors    | ~10-20ms        | Direct search
1K-10K vectors  | ~20-50ms        | IVFFlat benefits
10K-100K vectors| ~30-80ms        | Optimal IVFFlat range
> 100K vectors  | ~50-150ms       | May need tuning
```

### Memory Usage
```
Component              | Memory Usage
-----------------------|-------------------
Embedding Model        | ~80 MB (one-time)
LRU Cache (64 files)   | ~5-10 MB
Database Connection    | ~10-20 MB
Per 1K vectors in DB   | ~1.5 MB
```

## Key Features Visualization

```
┌────────────────────────────────────────────────────────┐
│              Smart Features                            │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ✅ Incremental Indexing                              │
│     ┌─────────────────────────────────────┐           │
│     │ Only index changed files            │           │
│     │ Hash-based change detection         │           │
│     │ Saves time & compute resources      │           │
│     └─────────────────────────────────────┘           │
│                                                        │
│  ✅ Smart Chunking                                    │
│     ┌─────────────────────────────────────┐           │
│     │ 6000 chars per chunk                │           │
│     │ 500 chars overlap                   │           │
│     │ Prevents context loss at boundaries │           │
│     └─────────────────────────────────────┘           │
│                                                        │
│  ✅ Architectural Priority                            │
│     ┌─────────────────────────────────────┐           │
│     │ app/services/* gets priority boost  │           │
│     │ Core architecture comes first       │           │
│     │ Better context for AI responses     │           │
│     └─────────────────────────────────────┘           │
│                                                        │
│  ✅ LRU Cache                                         │
│     ┌─────────────────────────────────────┐           │
│     │ Recently used files in memory       │           │
│     │ Capacity: 64 files (configurable)   │           │
│     │ Reduces disk I/O                    │           │
│     └─────────────────────────────────────┘           │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## Technology Stack

```
┌──────────────────────────────────────────────────┐
│              Technology Layers                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  Application Layer                               │
│  ┌────────────────────────────────────────────┐ │
│  │  app/services/system_service.py            │ │
│  │  - index_project()                         │ │
│  │  - find_related_context()                  │ │
│  │  - get_embedding_model()                   │ │
│  └────────────────────────────────────────────┘ │
│                      ▼                           │
│  ML/AI Layer                                     │
│  ┌────────────────────────────────────────────┐ │
│  │  SentenceTransformers                      │ │
│  │  Model: all-MiniLM-L6-v2                   │ │
│  │  Dimensions: 384                           │ │
│  │  Size: ~80MB                               │ │
│  └────────────────────────────────────────────┘ │
│                      ▼                           │
│  Database Layer                                  │
│  ┌────────────────────────────────────────────┐ │
│  │  PostgreSQL 15.1.0.118                     │ │
│  │  + pgvector extension                      │ │
│  │  + IVFFlat index                           │ │
│  └────────────────────────────────────────────┘ │
│                      ▼                           │
│  Infrastructure Layer                            │
│  ┌────────────────────────────────────────────┐ │
│  │  Docker Container (supabase/postgres)      │ │
│  │  Volume: pgdata (persistent)               │ │
│  │  Port: 5432                                │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

**For more details, see:**
- [VECTOR_DATABASE_GUIDE_AR.md](VECTOR_DATABASE_GUIDE_AR.md) - Full guide in Arabic
- [VECTOR_DATABASE_GUIDE.md](VECTOR_DATABASE_GUIDE.md) - Full guide in English
- [VECTOR_DB_QUICK_REFERENCE.md](VECTOR_DB_QUICK_REFERENCE.md) - Quick reference
