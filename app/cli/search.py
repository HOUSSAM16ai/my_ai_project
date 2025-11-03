# app/cli/search.py - The Local Memory Search Engine

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

INDEX_DIR = Path(".cogni")
EMB_FILE = INDEX_DIR / "embeddings.npy"
META_FILE = INDEX_DIR / "meta.json"
CHUNKS_FILE = INDEX_DIR / "index.jsonl"


def _load_index() -> tuple[np.ndarray, list[dict[str, Any]], dict[str, Any]]:
    if not (EMB_FILE.exists() and CHUNKS_FILE.exists() and META_FILE.exists()):
        raise RuntimeError("Index does not exist. Please run: python -m app.cli.main index")
    embs = np.load(EMB_FILE).astype("float32")
    metas: list[dict[str, Any]] = []
    with CHUNKS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            metas.append(json.loads(line))
    meta = json.loads(META_FILE.read_text(encoding="utf-8"))
    norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-12
    embs = embs / norms
    return embs, metas, meta


def embed_query(text: str, model_name: str) -> np.ndarray:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    # Convert to numpy array first, then cast to float32
    q = np.asarray(model.encode(text, normalize_embeddings=True), dtype="float32")
    return q


def search(text: str, k: int = 8) -> list[dict[str, Any]]:
    embs, metas, meta = _load_index()
    q = embed_query(text, meta["model"])
    sims = (embs @ q.reshape(-1, 1)).ravel()
    idx = np.argsort(-sims)[:k]
    out = []
    for i in idx:
        m = metas[int(i)]
        out.append({"score": float(sims[i]), **m})
    return out
