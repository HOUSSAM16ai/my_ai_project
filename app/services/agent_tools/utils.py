"""
Hyper-Utility Functions
=======================
Low-level helper functions for safety, hashing, and logging.
"""

import hashlib
import json
import logging
import os
import stat
import time
import uuid
from typing import Any

from .definitions import (
    MAX_WRITE_BYTES,
    PROJECT_ROOT,
    ToolResult,
)

# ======================================================================================
# Logging
# ======================================================================================
logger = logging.getLogger("agent_tools")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
else:
    logger.setLevel(os.getenv("AGENT_TOOLS_LOG_LEVEL", "INFO"))


def _dbg(msg: str):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(msg)


def _now() -> float:
    return time.time()


def _generate_trace_id() -> str:
    return uuid.uuid4().hex[:16]


def _coerce_to_tool_result(obj: Any) -> ToolResult:
    if isinstance(obj, ToolResult):
        return obj
    if isinstance(obj, tuple) and len(obj) == 2 and isinstance(obj[0], bool):
        ok, payload = obj
        return ToolResult(ok=ok, data=payload if ok else None, error=None if ok else str(payload))
    if isinstance(obj, dict):
        if "ok" in obj:
            return ToolResult(ok=bool(obj["ok"]), data=obj.get("data"), error=obj.get("error"))
        return ToolResult(ok=True, data=obj)
    if isinstance(obj, str):
        return ToolResult(ok=True, data={"text": obj})
    return ToolResult(ok=True, data=obj)


def _lower(s: Any) -> str:
    return str(s or "").strip().lower()


def _safe_json_dumps(obj: Any, max_bytes: int = 2_000_000) -> str:
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    b = raw.encode("utf-8")
    if len(b) <= max_bytes:
        return raw
    trimmed = b[: max_bytes - 10]
    while True:
        try:
            return trimmed.decode("utf-8", errors="strict") + "...TRUNCATED"
        except UnicodeDecodeError:
            trimmed = trimmed[:-1]
            if not trimmed:
                return "{}"


def _file_hash(path: str) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


# ======================================================================================
# Path Safety
# ======================================================================================
def _safe_path(
    path: str,
    *,
    must_exist_parent: bool = False,
    enforce_ext: list[str] | None = None,
    forbid_overwrite_large: bool = True,
) -> str:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Empty path.")
    if len(path) > 420:
        raise ValueError("Path too long.")
    norm = path.replace("\\", "/")
    if norm.startswith("/") or norm.startswith("~"):
        norm = norm.lstrip("/")
    if ".." in norm.split("/"):
        raise PermissionError("Path traversal detected.")
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, norm))
    if not abs_path.startswith(PROJECT_ROOT):
        raise PermissionError("Escaped project root.")
    cur = PROJECT_ROOT
    rel_parts = abs_path[len(PROJECT_ROOT) :].lstrip(os.sep).split(os.sep)
    for part in rel_parts:
        if not part:
            continue
        cur = os.path.join(cur, part)
        if os.path.islink(cur):
            raise PermissionError("Symlink component disallowed.")
    parent = os.path.dirname(abs_path)
    if must_exist_parent and not os.path.isdir(parent):
        raise FileNotFoundError("Parent directory does not exist.")
    if enforce_ext and not any(abs_path.lower().endswith(e.lower()) for e in enforce_ext):
        raise ValueError(f"Extension not allowed. Must be one of {enforce_ext}")
    if forbid_overwrite_large and os.path.exists(abs_path):
        try:
            st = os.stat(abs_path)
            if stat.S_ISREG(st.st_mode) and st.st_size > MAX_WRITE_BYTES:
                raise PermissionError("Refusing to overwrite large file.")
        except FileNotFoundError:
            pass
    return abs_path
