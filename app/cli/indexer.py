# app/cli/indexer.py - The Self-Healing, Robust Local Memory Architect (v2.1 - Final & Complete)

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable
from pathlib import Path

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

DEFAULT_MODEL = os.getenv("COGNI_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
INDEX_DIR = Path(".cogni")
EMB_FILE = INDEX_DIR / "embeddings.npy"
META_FILE = INDEX_DIR / "meta.json"
CHUNKS_FILE = INDEX_DIR / "index.jsonl"

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".cogni",
}
TEXT_EXTS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".toml",
    ".sql",
    ".sh",
    ".env",
    ".dockerfile",
    "dockerfile",
    ".gitignore",
}


def is_text_file(p: Path) -> bool:
    ext = p.suffix.lower()
    if ext in TEXT_EXTS:
        return True
    return bool(ext == "" and p.stat().st_size < 2000000)


def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_dir():
            if p.name in SKIP_DIRS or p.name.startswith("."):
                continue
            continue
        if any(part in SKIP_DIRS or part.startswith(".") for part in p.parts):
            continue
        try:
            if p.stat().st_size > 2_000_000:
                continue
        except Exception:
            continue
        if is_text_file(p):
            yield p


def read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None


def chunk_text(
    text: str, chunk_chars: int = 1200, overlap: int = 200
) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    n = len(text)
    i = 0
    while i < n:
        j = min(n, i + chunk_chars)
        chunk = text[i:j]
        out.append((i, j, chunk))
        if j >= n:
            break
        i = max(j - overlap, i + 1)
    return out


_model_instance = None


def load_model(model_name: str | None = None):
    """
    Loads the embedding model using a singleton pattern.
    It now intelligently falls back to the default model if none is provided.
    """
    global _model_instance
    if SentenceTransformer is None:
        raise RuntimeError(
            "sentence-transformers is not installed. Please add it to your requirements.txt"
        )

    name = (model_name or DEFAULT_MODEL).strip()

    # Check if we need to load or reload the model
    needs_reload = _model_instance is None
    if not needs_reload and hasattr(_model_instance, "_name_or_path"):
        needs_reload = getattr(_model_instance, "_name_or_path", "") != name
    
    if needs_reload:
        print(f"Loading embedding model '{name}'...")
        _model_instance = SentenceTransformer(name)

    return _model_instance


def ensure_index_dir():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def build_index(
    root: str = ".", model_name: str | None = None, chunk_chars: int = 1200, overlap: int = 200
) -> dict:
    ensure_index_dir()
    model = load_model(model_name)
    dim = model.get_sentence_embedding_dimension()

    all_chunks: list[dict] = []
    rid = 0
    root_path = Path(root).resolve()

    files_to_process = list(iter_files(root_path))
    print(f"Found {len(files_to_process)} text files to index.")

    for p in files_to_process:
        text = read_text(p)
        if not text:
            continue
        text = re.sub(r"[ \t]+\n", "\n", text)
        for start, end, chunk in chunk_text(text, chunk_chars=chunk_chars, overlap=overlap):
            rid += 1
            all_chunks.append(
                {
                    "id": rid,
                    "path": str(p.relative_to(root_path)),
                    "start": start,
                    "end": end,
                    "len": end - start,
                    "text": chunk,
                }
            )

    if not all_chunks:
        raise RuntimeError("No text chunks were generated. Nothing to index.")

    print(f"Encoding {len(all_chunks)} text chunks... (This may take a moment)")
    all_texts = [c["text"] for c in all_chunks]
    embeddings = model.encode(all_texts, normalize_embeddings=True, show_progress_bar=True)

    for _i, chunk_meta in enumerate(all_chunks):
        chunk_meta["preview"] = chunk_meta["text"][:200].strip()
        del chunk_meta["text"]

    np_emb = np.array(embeddings, dtype="float32")
    np.save(EMB_FILE, np_emb)

    with CHUNKS_FILE.open("w", encoding="utf-8") as f:
        for meta in all_chunks:
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")

    final_meta = {
        "root": str(root_path),
        "model": (model_name or DEFAULT_MODEL),
        "dim": int(dim),
        "count": int(len(all_chunks)),
        "chunk_chars": chunk_chars,
        "overlap": overlap,
    }
    META_FILE.write_text(json.dumps(final_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return final_meta
