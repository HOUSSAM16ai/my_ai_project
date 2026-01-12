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


def _coerce_to_tool_result(obj: dict[str, str | int | bool]) -> ToolResult:
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


def _lower(s: dict[str, str | int | bool]) -> str:
    return str(s or "").strip().lower()


def _safe_json_dumps(obj: dict[str, str | int | bool], max_bytes: int = 2_000_000) -> str:
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
    """
    Validate and normalize a file path with security checks.

    التحقق من صحة وتطبيع مسار الملف مع فحوصات الأمان.

    Args:
        path: Path to validate
        must_exist_parent: Whether parent directory must exist
        enforce_ext: List of allowed file extensions
        forbid_overwrite_large: Whether to forbid overwriting large files

    Returns:
        Absolute, validated path

    Raises:
        ValueError: For invalid paths
        PermissionError: For security violations
        FileNotFoundError: If parent doesn't exist when required
    """
    # Basic validation
    _validate_path_string(path)

    # Normalize and check for path traversal
    abs_path = _normalize_and_check_path(path)

    # Check for symlinks in path
    _check_symlinks_in_path(abs_path)

    # Check parent directory
    if must_exist_parent:
        _check_parent_exists(abs_path)

    # Check file extension
    if enforce_ext:
        _check_file_extension(abs_path, enforce_ext)

    # Check for large file overwrite
    if forbid_overwrite_large:
        _check_large_file_overwrite(abs_path)

    return abs_path


def _validate_path_string(path: str) -> None:
    """
    Validate path string basics.

    التحقق من أساسيات سلسلة المسار.
    """
    if not isinstance(path, str) or not path.strip():
        raise ValueError("Empty path.")
    if len(path) > 420:
        raise ValueError("Path too long.")


def _normalize_and_check_path(path: str) -> str:
    """
    Normalize path and check for traversal attempts.

    تطبيع المسار والتحقق من محاولات الاختراق.
    """
    norm = path.replace("\\", "/")
    if norm.startswith("/") or norm.startswith("~"):
        norm = norm.lstrip("/")

    # Check for path traversal
    if ".." in norm.split("/"):
        raise PermissionError("Path traversal detected.")

    # Get absolute path
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, norm))

    # Ensure it's within project root
    if not abs_path.startswith(PROJECT_ROOT):
        raise PermissionError("Escaped project root.")

    return abs_path


def _check_symlinks_in_path(abs_path: str) -> None:
    """
    Check for symlinks in path components.

    التحقق من الروابط الرمزية في مكونات المسار.
    """
    cur = PROJECT_ROOT
    rel_parts = abs_path[len(PROJECT_ROOT) :].lstrip(os.sep).split(os.sep)

    for part in rel_parts:
        if not part:
            continue
        cur = os.path.join(cur, part)
        if os.path.islink(cur):
            raise PermissionError("Symlink component disallowed.")


def _check_parent_exists(abs_path: str) -> None:
    """
    Check if parent directory exists.

    التحقق من وجود المجلد الأصلي.
    """
    parent = os.path.dirname(abs_path)
    if not os.path.isdir(parent):
        raise FileNotFoundError("Parent directory does not exist.")


def _check_file_extension(abs_path: str, enforce_ext: list[str]) -> None:
    """
    Check if file has allowed extension.

    التحقق من أن الملف له امتداد مسموح.
    """
    if not any(abs_path.lower().endswith(e.lower()) for e in enforce_ext):
        raise ValueError(f"Extension not allowed. Must be one of {enforce_ext}")


def _check_large_file_overwrite(abs_path: str) -> None:
    """
    Check if attempting to overwrite a large file.

    التحقق من محاولة الكتابة فوق ملف كبير.
    """
    if os.path.exists(abs_path):
        try:
            st = os.stat(abs_path)
            if stat.S_ISREG(st.st_mode) and st.st_size > MAX_WRITE_BYTES:
                raise PermissionError("Refusing to overwrite large file.")
        except FileNotFoundError:
            pass
