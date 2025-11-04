# app/services/system_service.py
#
# =====================================================================================
# ==                        NEURAL SUBSTRATE OMNISCIENT SYSTEM                      ==
# ==                   “Akasha+” – The Sentient Nervous Lattice (v11.0.0)            ==
# =====================================================================================
#
# PRIME DIRECTIVE:
#   This module is the sanctified membrane through which the Agent perceives
#   (filesystem + git) and inscribes memory (database + vectors). It is PURE:
#   - No business logic
#   - No LLM prompting
#   - Only perception, hashing, indexing, context retrieval, and truth.
#
# DESIGN PILLARS:
#   1. Deterministic Contracts: All public functions return ToolResult
#   2. Path Sanctity: Hardened resolution + anti-traversal + symlink validation
#   3. Incremental Vector Memory: Hash-based delta indexing + chunk-level granularity
#   4. Architectural Prioritization: app/services/* boosted during similarity retrieval
#   5. Observability: meta fields (elapsed_ms, cache_hit, chunk_count, error_code)
#   6. Safety: Size caps, binary detection, controlled extensions
#   7. Extensibility: Clear TODO anchors for future modularization
#
# NOTE:
#   Epic commentary is removable with zero functional impact.
#
from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
import subprocess
import threading
import time
from collections import OrderedDict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app import db


# ---------------------------------------------------------------------------
# ToolResult (يفضل نقله لاحقاً إلى shared/contracts.py لتفادي التبعيات الدائرية)
# ---------------------------------------------------------------------------
@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None
    meta: dict[str, Any] | None = None

    def to_dict(self):
        return asdict(self)


__version__ = "11.0.0"

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONFIG (قابلة للتهيئة عبر متغيرات بيئة)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path.cwd())).resolve()
ALLOWED_EXTENSIONS = set(
    filter(
        None,
        os.getenv(
            "SYSTEM_SERVICE_ALLOWED_EXT", ".py,.md,.txt,.json,.yml,.yaml,.js,.ts,.html,.css,.sh"
        ).split(","),
    )
)
IGNORED_DIRS = {
    "__pycache__",
    ".git",
    ".idea",
    "venv",
    ".vscode",
    "migrations",
    "instance",
    "tmp",
    "node_modules",
}
MAX_FILE_BYTES = int(os.getenv("SYSTEM_SERVICE_MAX_FILE_BYTES", "1500000"))  # 1.5MB
CHUNK_SIZE = int(os.getenv("SYSTEM_SERVICE_CHUNK_SIZE", "6000"))
CHUNK_OVERLAP = int(os.getenv("SYSTEM_SERVICE_CHUNK_OVERLAP", "500"))
EMBED_BATCH = int(os.getenv("SYSTEM_SERVICE_EMBED_BATCH", "32"))
ENABLE_FILE_LRU = os.getenv("SYSTEM_SERVICE_FILE_CACHE", "1") == "1"
FILE_LRU_CAPACITY = int(os.getenv("SYSTEM_SERVICE_FILE_CACHE_CAP", "64"))
PRIORITY_PATH_PREFIX = "app/services/"
VECTOR_DIM = 384  # all-MiniLM-L6-v2
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

# ---------------------------------------------------------------------------
# INTERNAL STATE
# ---------------------------------------------------------------------------
_embedding_model = None
_embedding_lock = threading.Lock()

# LRU Cache for small files (path -> dict)
_file_lru: OrderedDict[str, dict[str, Any]] = OrderedDict()


# ---------------------------------------------------------------------------
# UTILITIES
# ---------------------------------------------------------------------------
def _now_ms() -> float:
    return time.perf_counter() * 1000.0


def _hash_text(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8", errors="ignore")).hexdigest()


def _is_binary_maybe(path: Path) -> bool:
    # Heuristic: use mimetype or raw sniff
    mime, _ = mimetypes.guess_type(str(path))
    if mime and not mime.startswith("text"):
        return True
    try:
        with path.open("rb") as f:
            block = f.read(512)
        return b"\0" in block
    except Exception:
        return True


def _path_within_project(p: Path) -> bool:
    try:
        p = p.resolve()
        return p == PROJECT_ROOT or PROJECT_ROOT in p.parents
    except Exception:
        return False


def _normalize_rel_path(rel_path: str) -> Path:
    if not rel_path or ".." in rel_path or rel_path.startswith("~"):
        raise ValueError("PATH_TRAVERSAL_DETECTED")
    p = (PROJECT_ROOT / rel_path).resolve()
    if not _path_within_project(p):
        raise ValueError("OUT_OF_PROJECT_BOUNDARY")
    return p


def _format_vector_literal(vec) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


# ---------------------------------------------------------------------------
# EMBEDDING MODEL (Lazy load)
# ---------------------------------------------------------------------------
def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        with _embedding_lock:
            if _embedding_model is None:
                from sentence_transformers import SentenceTransformer

                current_app.logger.info(
                    f"[embeddings] Loading model '{EMBED_MODEL_NAME}' (one-time)..."
                )
                _embedding_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embedding_model


# ---------------------------------------------------------------------------
# DB STRUCTURE
# code_documents:
#   id (TEXT PK) -> file_path::chunk_index
#   file_path (TEXT)
#   chunk_index (INT)
#   content (TEXT)
#   file_hash (TEXT)  # entire file hash for chunk 0 duplication
#   chunk_hash (TEXT) # hash of this chunk’s text
#   source (TEXT)
#   embedding (vector(VECTOR_DIM))
#   updated_at (TIMESTAMP)
# ---------------------------------------------------------------------------
def _ensure_code_documents():
    db.session.execute(
        text(
            f"""
        CREATE TABLE IF NOT EXISTS code_documents (
            id TEXT PRIMARY KEY,
            file_path TEXT,
            chunk_index INT,
            content TEXT,
            file_hash TEXT,
            chunk_hash TEXT,
            source TEXT,
            embedding vector({VECTOR_DIM}),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
        )
    )
    db.session.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_code_documents_file_path
            ON code_documents(file_path);
    """
        )
    )
    db.session.execute(
        text(
            """
        CREATE INDEX IF NOT EXISTS idx_code_documents_embedding
            ON code_documents USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
    """
        )
    )


# ---------------------------------------------------------------------------
# CHUNKING
# ---------------------------------------------------------------------------
def _chunk_text(content: str) -> list[tuple[str, int]]:
    if len(content) <= CHUNK_SIZE:
        return [(content, 0)]
    chunks = []
    start = 0
    idx = 0
    while start < len(content):
        end = start + CHUNK_SIZE
        segment = content[start:end]
        chunks.append((segment, idx))
        idx += 1
        start = max(end - CHUNK_OVERLAP, end)
    return chunks


# ---------------------------------------------------------------------------
# FILE LRU
# ---------------------------------------------------------------------------
def _file_cache_get(key: str) -> dict[str, Any] | None:
    if not ENABLE_FILE_LRU:
        return None
    val = _file_lru.get(key)
    if val is not None:
        _file_lru.move_to_end(key)
    return val


def _file_cache_put(key: str, value: dict[str, Any]):
    if not ENABLE_FILE_LRU:
        return
    _file_lru[key] = value
    _file_lru.move_to_end(key)
    if len(_file_lru) > FILE_LRU_CAPACITY:
        _file_lru.popitem(last=False)


# ---------------------------------------------------------------------------
# PUBLIC: get_project_tree
# ---------------------------------------------------------------------------
def get_project_tree() -> ToolResult:
    start = _now_ms()
    try:
        ignored_str = "|".join(IGNORED_DIRS)
        try:
            proc = subprocess.run(
                ["tree", "-a", "-I", ignored_str],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                check=True,
                timeout=12,
            )
            tree_txt = proc.stdout
            meta_src = "tree_command"
        except Exception as e:
            # fallback python walker
            lines = []
            for root, dirs, files in os.walk(PROJECT_ROOT):
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
                rel_root = os.path.relpath(root, PROJECT_ROOT)
                depth = 0 if rel_root == "." else rel_root.count(os.sep)
                indent = "  " * depth
                lines.append(f"{indent}{os.path.basename(root) if rel_root != '.' else '.'}/")
                for f in files:
                    lines.append(f"{indent}  {f}")
            tree_txt = "\n".join(lines)
            meta_src = f"python_fallback:{type(e).__name__}"
        return ToolResult(
            ok=True,
            data={"tree": tree_txt},
            meta={
                "source": meta_src,
                "elapsed_ms": round(_now_ms() - start, 2),
                "error_code": None,
            },
        )
    except Exception as e:
        return ToolResult(
            ok=False,
            error="PROJECT_TREE_FAILED",
            meta={
                "exception": str(e),
                "elapsed_ms": round(_now_ms() - start, 2),
                "error_code": "PROJECT_TREE_FAILED",
            },
        )


# ---------------------------------------------------------------------------
# PUBLIC: get_git_status
# ---------------------------------------------------------------------------
def get_git_status(porcelain: bool = True) -> ToolResult:
    start = _now_ms()
    cmd = ["git", "status"]
    if porcelain:
        cmd = ["git", "status", "--porcelain=v1"]
    try:
        proc = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=8, check=True
        )
        raw = proc.stdout.strip()
        parsed = []
        if porcelain and raw:
            for line in raw.splitlines():
                # Format: XY <path>
                if len(line) >= 3:
                    x = line[0]
                    y = line[1]
                    path = line[3:]
                    parsed.append({"index_status": x, "worktree_status": y, "path": path})
        return ToolResult(
            ok=True,
            data={"raw": raw, "parsed": parsed, "clean": len(parsed) == 0},
            meta={"source": "git", "elapsed_ms": round(_now_ms() - start, 2)},
        )
    except subprocess.TimeoutExpired as e:
        return ToolResult(
            ok=False, error="GIT_TIMEOUT", meta={"exception": str(e), "error_code": "GIT_TIMEOUT"}
        )
    except subprocess.CalledProcessError as e:
        return ToolResult(
            ok=False, error="GIT_FAILED", meta={"exception": str(e), "error_code": "GIT_FAILED"}
        )
    except FileNotFoundError:
        return ToolResult(
            ok=False, error="GIT_NOT_INSTALLED", meta={"error_code": "GIT_NOT_INSTALLED"}
        )
    except Exception as e:
        return ToolResult(
            ok=False,
            error="GIT_UNKNOWN_ERROR",
            meta={"exception": str(e), "error_code": "GIT_UNKNOWN_ERROR"},
        )


# ---------------------------------------------------------------------------
# PUBLIC: query_file
# ---------------------------------------------------------------------------
def query_file(rel_path: str) -> ToolResult:
    """
    Returns content (maybe truncated) with hashing & optional caching.
    """
    start = _now_ms()
    try:
        file_path = _normalize_rel_path(rel_path)
    except Exception as e:
        return ToolResult(
            ok=False, error="PATH_INVALID", meta={"detail": str(e), "error_code": "PATH_INVALID"}
        )

    if not file_path.exists():
        return ToolResult(
            ok=False,
            error="FILE_NOT_FOUND",
            meta={"path": rel_path, "error_code": "FILE_NOT_FOUND"},
        )
    if not file_path.is_file():
        return ToolResult(
            ok=False, error="NOT_A_FILE", meta={"path": rel_path, "error_code": "NOT_A_FILE"}
        )

    ext = file_path.suffix.lower()
    if ext and ALLOWED_EXTENSIONS and ext not in ALLOWED_EXTENSIONS:
        # Optionally raise or just mark unsupported
        return ToolResult(
            ok=False,
            error="EXTENSION_NOT_ALLOWED",
            meta={"ext": ext, "error_code": "EXTENSION_NOT_ALLOWED"},
        )

    if _is_binary_maybe(file_path):
        return ToolResult(
            ok=False,
            error="BINARY_FILE_REJECTED",
            meta={"path": rel_path, "error_code": "BINARY_FILE_REJECTED"},
        )

    # LRU check
    cache_hit = False
    if ENABLE_FILE_LRU:
        cached = _file_cache_get(rel_path)
        if cached and cached.get("mtime") == file_path.stat().st_mtime:
            cache_hit = True
            content = cached["content"]
        else:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            _file_cache_put(rel_path, {"content": content, "mtime": file_path.stat().st_mtime})
    else:
        content = file_path.read_text(encoding="utf-8", errors="ignore")

    total_bytes = len(content.encode("utf-8", errors="ignore"))
    truncated = False
    presented = content
    if total_bytes > MAX_FILE_BYTES:
        presented = content[: min(len(content), 8000)]
        truncated = True

    file_hash = _hash_text(content)

    # Attempt DB bootstrap (store chunk 0 only for quick retrieval)
    try:
        with db.session.begin():
            _ensure_code_documents()
            doc_id = f"{rel_path}::0"
            existed = db.session.execute(
                text("SELECT file_hash FROM code_documents WHERE id = :id"), {"id": doc_id}
            ).scalar_one_or_none()
            if existed != file_hash:
                db.session.execute(
                    text(
                        """
                        INSERT INTO code_documents
                        (id, file_path, chunk_index, content, file_hash, chunk_hash, source, embedding)
                        VALUES (:id, :fp, :ci, :ct, :fh, :ch, :src, NULL)
                        ON CONFLICT (id) DO UPDATE
                        SET content=:ct, file_hash=:fh, chunk_hash=:ch, updated_at=CURRENT_TIMESTAMP;
                    """
                    ),
                    {
                        "id": doc_id,
                        "fp": rel_path,
                        "ci": 0,
                        "ct": presented,
                        "fh": file_hash,
                        "ch": file_hash,
                        "src": rel_path,
                    },
                )
    except Exception as e:
        current_app.logger.warning("DB bootstrap for %s failed: %s", rel_path, e)

    return ToolResult(
        ok=True,
        data={
            "path": rel_path,
            "content": presented,
            "bytes": total_bytes,
            "hash": file_hash,
            "truncated": truncated,
        },
        meta={
            "cache_hit": cache_hit,
            "elapsed_ms": round(_now_ms() - start, 2),
            "error_code": None,
        },
    )


# ---------------------------------------------------------------------------
# PUBLIC: index_project
# ---------------------------------------------------------------------------
def index_project(force: bool = False, chunking: bool = True) -> ToolResult:
    """
    Incrementally index textual files into vector memory.
    - Skips unchanged chunk hashes (unless force)
    - Splits by CHUNK_SIZE w/ overlap
    """
    start = _now_ms()
    try:
        model = get_embedding_model()
        # Stage 1: gather candidate files
        file_records: list[tuple[str, str]] = []
        for path_obj in PROJECT_ROOT.rglob("*"):
            if any(ignored in path_obj.parts for ignored in IGNORED_DIRS):
                continue
            if not path_obj.is_file():
                continue
            ext = path_obj.suffix.lower()
            if ALLOWED_EXTENSIONS and ext not in ALLOWED_EXTENSIONS:
                continue
            if path_obj.stat().st_size > MAX_FILE_BYTES:
                continue
            if _is_binary_maybe(path_obj):
                continue
            rel = path_obj.relative_to(PROJECT_ROOT).as_posix()
            try:
                text_content = path_obj.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if not text_content.strip():
                continue
            file_records.append((rel, text_content))

        with db.session.begin():
            _ensure_code_documents()
            existing_rows = db.session.execute(
                text("SELECT id, file_hash, chunk_hash FROM code_documents;")
            ).fetchall()
        existing_hash_map = {row[0]: (row[1], row[2]) for row in existing_rows}

        to_insert = []
        total_chunks = 0
        for rel, full_content in file_records:
            file_hash = _hash_text(full_content)
            chunks = [(full_content, 0)] if not chunking else _chunk_text(full_content)
            for chunk_text, cidx in chunks:
                chunk_hash = _hash_text(chunk_text)
                doc_id = f"{rel}::{cidx}"
                if not force and doc_id in existing_hash_map:
                    old_fh, old_ch = existing_hash_map[doc_id]
                    # Skip if identical chunk hash & file hash matches (reduces re-embedding)
                    if old_fh == file_hash and old_ch == chunk_hash:
                        continue
                to_insert.append((doc_id, rel, cidx, chunk_text, file_hash, chunk_hash))
            total_chunks += len(chunks)

        if not to_insert:
            return ToolResult(
                ok=True,
                data={
                    "indexed_new": 0,
                    "message": "No new or changed content.",
                    "total_chunks_seen": total_chunks,
                },
                meta={"elapsed_ms": round(_now_ms() - start, 2)},
            )

        # Embed in batches
        texts = [r[3] for r in to_insert]
        embeddings = []
        for i in range(0, len(texts), EMBED_BATCH):
            batch = texts[i : i + EMBED_BATCH]
            emb = model.encode(batch, show_progress_bar=False)
            embeddings.extend(emb)

        # Insert
        with db.session.begin():
            for (doc_id, rel, cidx, chunk_text, file_hash, chunk_hash), emb_vec in zip(
                to_insert, embeddings, strict=False
            ):
                db.session.execute(
                    text(
                        """
                        INSERT INTO code_documents
                        (id, file_path, chunk_index, content, file_hash, chunk_hash, source, embedding)
                        VALUES (:id, :fp, :ci, :ct, :fh, :ch, :src, :emb)
                        ON CONFLICT (id) DO UPDATE
                        SET content=:ct, file_hash=:fh, chunk_hash=:ch, embedding=:emb, updated_at=CURRENT_TIMESTAMP;
                    """
                    ),
                    {
                        "id": doc_id,
                        "fp": rel,
                        "ci": cidx,
                        "ct": chunk_text,
                        "fh": file_hash,
                        "ch": chunk_hash,
                        "src": rel,
                        "emb": _format_vector_literal(emb_vec),
                    },
                )
            total_count = db.session.execute(text("SELECT COUNT(*) FROM code_documents;")).scalar()

        return ToolResult(
            ok=True,
            data={
                "indexed_new": len(to_insert),
                "total_in_store": total_count,
                "force": force,
                "chunking": chunking,
            },
            meta={"elapsed_ms": round(_now_ms() - start, 2)},
        )
    except OperationalError as e:
        return ToolResult(
            ok=False,
            error="DB_OPERATIONAL_ERROR",
            meta={"exception": str(e), "error_code": "DB_OPERATIONAL_ERROR"},
        )
    except SQLAlchemyError as e:
        return ToolResult(
            ok=False,
            error="DB_EXECUTION_ERROR",
            meta={"exception": str(e), "error_code": "DB_EXECUTION_ERROR"},
        )
    except Exception as e:
        return ToolResult(
            ok=False,
            error="INDEXING_UNKNOWN_ERROR",
            meta={"exception": str(e), "error_code": "INDEXING_UNKNOWN_ERROR"},
        )


# ---------------------------------------------------------------------------
# PUBLIC: find_related_context
# ---------------------------------------------------------------------------
def find_related_context(prompt_text: str, limit: int = 6) -> ToolResult:
    start = _now_ms()
    try:
        model = get_embedding_model()
        qvec = model.encode([prompt_text], show_progress_bar=False)[0]
        qlit = _format_vector_literal(qvec)

        with db.session.begin():
            _ensure_code_documents()
            sql = text(
                """
                WITH candidate AS (
                    SELECT id, file_path, content, source, embedding,
                           CASE WHEN file_path LIKE :prio THEN 0 ELSE 1 END AS priority_tier
                    FROM code_documents
                )
                SELECT id, file_path, content, source, priority_tier,
                       (embedding <=> :q) AS distance
                FROM candidate
                ORDER BY priority_tier ASC, distance ASC
                LIMIT :lim;
            """
            )
            rows = db.session.execute(
                sql, {"q": qlit, "lim": limit * 2, "prio": f"{PRIORITY_PATH_PREFIX}%"}
            ).fetchall()

        # Optional re-ranking (distance + small boost if short content)
        scored = []
        for r in rows:
            snippet = r.content[:600] + ("..." if len(r.content) > 600 else "")
            len_penalty = min(len(r.content) / 20000.0, 1.0)  # penalize extremely large
            hybrid_score = (
                float(r.distance) + 0.05 * len_penalty + (0 if r.priority_tier == 0 else 0.1)
            )
            scored.append(
                {
                    "id": r.id,
                    "file_path": r.file_path,
                    "priority_tier": r.priority_tier,
                    "raw_distance": float(r.distance),
                    "hybrid_score": hybrid_score,
                    "preview": snippet,
                }
            )
        scored.sort(key=lambda x: x["hybrid_score"])
        final = scored[:limit]

        return ToolResult(
            ok=True,
            data={"results": final, "count": len(final)},
            meta={"elapsed_ms": round(_now_ms() - start, 2)},
        )
    except Exception as e:
        return ToolResult(
            ok=False,
            error="CONTEXT_RETRIEVAL_FAILED",
            meta={"exception": str(e), "error_code": "CONTEXT_RETRIEVAL_FAILED"},
        )


# ---------------------------------------------------------------------------
# PUBLIC: find_similar_conversations
# ---------------------------------------------------------------------------
def find_similar_conversations(limit: int = 5) -> ToolResult:
    start = _now_ms()
    try:
        with db.session.begin():
            sql = text(
                """
                WITH convo_rating AS (
                    SELECT conversation_id,
                           MAX(CASE WHEN rating = 'good' THEN 1 ELSE 0 END) AS has_good
                    FROM messages GROUP BY conversation_id
                )
                SELECT m.role, m.content, m.rating
                FROM messages m
                JOIN convo_rating cr ON m.conversation_id = cr.conversation_id
                WHERE m.role IN ('user','assistant')
                ORDER BY cr.has_good DESC, m.timestamp DESC
                LIMIT :lim;
            """
            )
            rows = db.session.execute(sql, {"lim": limit * 2}).fetchall()
        examples = []
        for r in rows:
            preview = r.content[:200] + ("..." if len(r.content) > 200 else "")
            examples.append({"role": r.role, "rating": r.rating, "preview": preview})
        return ToolResult(
            ok=True,
            data={"examples": examples[:limit], "total_collected": len(examples)},
            meta={"elapsed_ms": round(_now_ms() - start, 2)},
        )
    except OperationalError:
        return ToolResult(
            ok=True, data={"examples": []}, meta={"warning": "conversation table missing"}
        )
    except Exception as e:
        return ToolResult(
            ok=False,
            error="CONVERSATION_RETRIEVAL_FAILED",
            meta={"exception": str(e), "error_code": "CONVERSATION_RETRIEVAL_FAILED"},
        )


# ---------------------------------------------------------------------------
# PUBLIC: diagnostics / health
# ---------------------------------------------------------------------------
def diagnostics() -> ToolResult:
    try:
        model_loaded = _embedding_model is not None
        return ToolResult(
            ok=True,
            data={
                "version": __version__,
                "project_root": str(PROJECT_ROOT),
                "embedding_model_loaded": model_loaded,
                "cache_enabled": ENABLE_FILE_LRU,
                "cache_size": len(_file_lru),
                "allowed_ext_count": len(ALLOWED_EXTENSIONS),
            },
        )
    except Exception as e:
        return ToolResult(
            ok=False,
            error="DIAGNOSTICS_FAILED",
            meta={"exception": str(e), "error_code": "DIAGNOSTICS_FAILED"},
        )
