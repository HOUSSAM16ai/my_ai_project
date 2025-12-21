"""
Hyper-Search Tools
==================
Lexical, semantic, and index-based code search capabilities.
"""

import os
import re
import time

from .core import tool
from .definitions import (
    CODE_INDEX_EXCLUDE_DIRS,
    CODE_INDEX_INCLUDE_EXTS,
    CODE_INDEX_MAX_FILE_BYTES,
    CODE_INDEX_MAX_FILES,
    CODE_SEARCH_CONTEXT_RADIUS,
    CODE_SEARCH_FILE_MAX_BYTES,
    CODE_SEARCH_MAX_RESULTS,
    SEMANTIC_SEARCH_ENABLED,
    SEMANTIC_SEARCH_FAKE_LATENCY_MS,
    ToolResult,
)
from .utils import _safe_path


@tool(
    name="code_index_project",
    description="Lightweight lexical project index: collects file metadata, size, line counts, simple complexity heuristic.",
    category="index",
    capabilities=["index", "scan"],
    parameters={
        "type": "object",
        "properties": {
            "root": {"type": "string", "default": "."},
            "max_files": {"type": "integer", "default": CODE_INDEX_MAX_FILES},
            "include_exts": {"type": "string", "default": ",".join(CODE_INDEX_INCLUDE_EXTS)},
        },
    },
)
def code_index_project(
    root: str = ".",
    max_files: int = CODE_INDEX_MAX_FILES,
    include_exts: str = ",".join(CODE_INDEX_INCLUDE_EXTS),
) -> ToolResult:
    try:
        root_abs = _safe_path(root)
        if not os.path.isdir(root_abs):
            return ToolResult(ok=False, error="NOT_A_DIRECTORY")
        exts = {e.strip().lower() for e in include_exts.split(",") if e.strip().startswith(".")}
        files_meta = []
        count = 0
        start = time.perf_counter()
        for base, _dirs, files in os.walk(root_abs):
            # prune excluded dirs
            parts = base.replace("\\", "/").split("/")
            if any(seg in CODE_INDEX_EXCLUDE_DIRS for seg in parts):
                continue
            for fname in files:
                if count >= max_files:
                    break
                ext = os.path.splitext(fname)[1].lower()
                if exts and ext not in exts:
                    continue
                fpath = os.path.join(base, fname)
                try:
                    st = os.stat(fpath)
                    if st.st_size > CODE_INDEX_MAX_FILE_BYTES:
                        continue
                    with open(fpath, encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    line_count = len(lines)
                    non_empty = sum(1 for line in lines if line.strip())
                    avg_len = sum(len(line) for line in lines) / line_count if line_count else 0
                    complexity_score = round(
                        (line_count * 0.4) + (non_empty * 0.6) + (avg_len * 0.05), 2
                    )
                    files_meta.append(
                        {
                            "path": os.path.relpath(fpath, root_abs),
                            "lines": line_count,
                            "non_empty": non_empty,
                            "avg_line_len": round(avg_len, 2),
                            "size": st.st_size,
                            "complexity_score": complexity_score,
                        }
                    )
                    count += 1
                except Exception:
                    continue
            if count >= max_files:
                break
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        files_meta.sort(key=lambda x: x["complexity_score"], reverse=True)
        top_hotspots = files_meta[: min(20, len(files_meta))]
        return ToolResult(
            ok=True,
            data={
                "root": root_abs,
                "indexed_files": len(files_meta),
                "hotspots_top20": top_hotspots,
                "elapsed_ms": elapsed_ms,
                "exts": sorted(exts),
                "limit_reached": count >= max_files,
            },
        )
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="code_search_lexical",
    description="Lexical scan for a query (substring or optional regex) returning contextual snippets.",
    category="search",
    capabilities=["search", "scan", "lexical"],
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "root": {"type": "string", "default": "."},
            "regex": {"type": "boolean", "default": False},
            "limit": {"type": "integer", "default": CODE_SEARCH_MAX_RESULTS},
            "context_radius": {"type": "integer", "default": CODE_SEARCH_CONTEXT_RADIUS},
        },
        "required": ["query"],
    },
)
def code_search_lexical(
    query: str,
    root: str = ".",
    regex: bool = False,
    limit: int = CODE_SEARCH_MAX_RESULTS,
    context_radius: int = CODE_SEARCH_CONTEXT_RADIUS,
) -> ToolResult:
    try:
        q = (query or "").strip()
        if not q:
            return ToolResult(ok=False, error="EMPTY_QUERY")
        root_abs = _safe_path(root)
        if not os.path.isdir(root_abs):
            return ToolResult(ok=False, error="NOT_A_DIRECTORY")
        pattern = None
        if regex:
            try:
                pattern = re.compile(q, re.IGNORECASE | re.MULTILINE)
            except Exception as e:
                return ToolResult(ok=False, error=f"REGEX_INVALID: {e}")
        results = []
        scanned = 0
        for base, _dirs, files in os.walk(root_abs):
            parts = base.replace("\\", "/").split("/")
            if any(seg in CODE_INDEX_EXCLUDE_DIRS for seg in parts):
                continue
            for fname in files:
                os.path.splitext(fname)[1].lower()
                fpath = os.path.join(base, fname)
                if os.path.getsize(fpath) > CODE_SEARCH_FILE_MAX_BYTES:
                    continue
                try:
                    with open(fpath, encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                except Exception:
                    continue
                scanned += 1
                for idx, line in enumerate(lines):
                    hit = False
                    if regex:
                        if pattern.search(line):
                            hit = True
                    else:
                        if q.lower() in line.lower():
                            hit = True
                    if hit:
                        start = max(0, idx - context_radius)
                        end = min(len(lines), idx + context_radius + 1)
                        snippet_lines = lines[start:end]
                        snippet = "".join(snippet_lines)[:1000]
                        rel = os.path.relpath(fpath, root_abs)
                        results.append(
                            {
                                "file": rel,
                                "line": idx + 1,
                                "snippet": snippet,
                                "match_line_excerpt": line.strip()[:300],
                            }
                        )
                        if len(results) >= limit:
                            return ToolResult(
                                ok=True,
                                data={
                                    "query": q,
                                    "regex": regex,
                                    "results": results,
                                    "scanned_files": scanned,
                                    "limit_reached": True,
                                },
                            )
        return ToolResult(
            ok=True,
            data={
                "query": q,
                "regex": regex,
                "results": results,
                "scanned_files": scanned,
                "limit_reached": False,
            },
        )
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="code_search_semantic",
    description="(Stub) Semantic search placeholder. Returns informative stub unless SEMANTIC_SEARCH_ENABLED=1.",
    category="search",
    capabilities=["search", "semantic", "stub"],
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "default": 5}},
        "required": ["query"],
    },
)
def code_search_semantic(query: str, top_k: int = 5) -> ToolResult:
    q = (query or "").strip()
    if not q:
        return ToolResult(ok=False, error="EMPTY_QUERY")
    if not SEMANTIC_SEARCH_ENABLED:
        return ToolResult(
            ok=True,
            data={
                "query": q,
                "enabled": False,
                "message": "Semantic search disabled (SEMANTIC_SEARCH_ENABLED=0). This is a stub.",
                "results": [],
            },
        )
    # Future real embedding logic
    if SEMANTIC_SEARCH_FAKE_LATENCY_MS > 0:
        time.sleep(SEMANTIC_SEARCH_FAKE_LATENCY_MS / 1000.0)
    # Dummy placeholder results
    dummy = [
        {
            "file": f"placeholder_{i}.py",
            "score": round(1.0 - (i * 0.07), 3),
            "excerpt": f"Simulated semantic match for '{q}' (rank {i + 1}).",
        }
        for i in range(min(top_k, 8))
    ]
    return ToolResult(ok=True, data={"query": q, "enabled": True, "results": dummy})
