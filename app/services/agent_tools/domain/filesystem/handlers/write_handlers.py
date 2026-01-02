"""
Handlers for writing and modifying files.
"""

import os
from app.services.agent_tools.domain.filesystem.validators.path_validator import validate_path, validate_file
import gzip
from app.services.agent_tools.domain.filesystem.config import (
    MAX_WRITE_BYTES, MAX_APPEND_BYTES, ENFORCE_APPEND_TOTAL,
    AUTO_CREATE_ENABLED, AUTO_CREATE_MAX_BYTES, AUTO_CREATE_DEFAULT_CONTENT, AUTO_CREATE_ALLOWED_EXTS
)
from app.services.agent_tools.tool_model import ToolResult

def write_file_logic(path: str, content: str, compress_json_if_large: bool = False) -> ToolResult:
    """Writes content to a file, overwriting it."""
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")

        # Check size limit
        # The test patches MAX_WRITE_BYTES but the previous code didn't check it.
        # We need to respect the constant.
        if len(content.encode('utf-8')) > MAX_WRITE_BYTES:
             return ToolResult(ok=False, error="WRITE_TOO_LARGE")

        abs_path = validate_path(path, allow_missing=True)

        # Directory check
        if os.path.exists(abs_path) and os.path.isdir(abs_path):
            return ToolResult(ok=False, error="IS_DIRECTORY")

        # Compression logic
        if compress_json_if_large and path.endswith(".json") and len(content) > 400_000:
             abs_path += ".gz"
             with gzip.open(abs_path, "wt", encoding="utf-8") as f:
                 f.write(content)
             return ToolResult(ok=True, data={"written": True, "path": abs_path, "bytes": len(content), "compressed": True})

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        return ToolResult(ok=True, data={"written": True, "path": abs_path, "bytes": len(content)})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


def write_file_if_changed_logic(path: str, content: str) -> ToolResult:
    """Writes only if content differs."""
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")

        abs_path = validate_path(path, allow_missing=True)

        if os.path.exists(abs_path):
            if os.path.isdir(abs_path):
                return ToolResult(ok=False, error="IS_DIRECTORY")

            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    current = f.read()
                if current == content:
                    return ToolResult(ok=True, data={"skipped": True, "reason": "UNCHANGED", "path": abs_path})
            except Exception:
                # If read fails (e.g. binary), we might overwrite or error.
                # Original logic didn't handle binary check specifically for this, so we proceed.
                pass

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        return ToolResult(ok=True, data={"written": True, "path": abs_path})

    except Exception as e:
        return ToolResult(ok=False, error=str(e))


def append_file_logic(path: str, content: str) -> ToolResult:
    """Appends content to a file."""
    try:
        if not isinstance(content, str):
            # Strict error string matching test expectation
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")

        abs_path = validate_path(path, allow_missing=True)

        if os.path.isdir(abs_path):
            return ToolResult(ok=False, error="IS_DIRECTORY")

        # Check total size limit
        current_size = os.path.getsize(abs_path) if os.path.exists(abs_path) else 0
        if ENFORCE_APPEND_TOTAL and (current_size + len(content) > MAX_APPEND_BYTES):
            return ToolResult(ok=False, error="APPEND_TOTAL_LIMIT_EXCEEDED")

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(content)

        return ToolResult(ok=True, data={"appended": True, "path": abs_path, "new_size": current_size + len(content)})

    except Exception as e:
        return ToolResult(ok=False, error=str(e))


def delete_file_logic(path: str, confirm: bool = False) -> ToolResult:
    """Deletes a file."""
    try:
        if not confirm:
            return ToolResult(ok=False, error="CONFIRM_REQUIRED")

        # Use validate_file to handle checks
        try:
            abs_path = validate_file(path)
        except (FileNotFoundError, IsADirectoryError, ValueError) as e:
            if isinstance(e, FileNotFoundError): return ToolResult(ok=False, error="FILE_NOT_FOUND")
            if isinstance(e, IsADirectoryError): return ToolResult(ok=False, error="IS_DIRECTORY")
            return ToolResult(ok=False, error=str(e))

        os.remove(abs_path)
        return ToolResult(ok=True, data={"deleted": True, "path": abs_path})

    except Exception as e:
        return ToolResult(ok=False, error=str(e))


def ensure_file_logic(
    path: str,
    max_bytes: int = 40000,
    initial_content: str = "",
    force_create: bool = False,
    allow_create: bool = True,
    enforce_ext: str | None = None,
) -> ToolResult:
    """Ensures a file exists, creating it if necessary."""
    try:
        # Check extensions
        lowered = path.lower()
        if enforce_ext:
            if not lowered.endswith(enforce_ext.lower()):
                return ToolResult(ok=False, error="EXTENSION_MISMATCH")
        elif AUTO_CREATE_ALLOWED_EXTS and not any(lowered.endswith(x) for x in AUTO_CREATE_ALLOWED_EXTS):
            return ToolResult(ok=False, error="EXT_NOT_ALLOWED")

        abs_path = validate_path(path, allow_missing=True)
        path_exists = os.path.exists(abs_path)

        # If exists
        if path_exists and not force_create:
            if os.path.isdir(abs_path):
                return ToolResult(ok=False, error="IS_DIRECTORY")

            # Read preview
            try:
                with open(abs_path, encoding="utf-8") as f:
                    d = f.read(max_bytes + 10)
                truncated = len(d) > max_bytes
                preview = d[:max_bytes]
            except Exception:
                preview = ""
                truncated = False

            return ToolResult(ok=True, data={
                "path": abs_path,
                "content": preview,
                "truncated": truncated,
                "exists": True,
                "missing": False,
                "created": False
            })

        # Create if needed
        if not path_exists and (not allow_create or not AUTO_CREATE_ENABLED):
            return ToolResult(ok=False, error="FILE_NOT_FOUND")

        content = initial_content if initial_content.strip() else AUTO_CREATE_DEFAULT_CONTENT
        if len(content.encode("utf-8")) > AUTO_CREATE_MAX_BYTES:
            return ToolResult(ok=False, error="INITIAL_CONTENT_TOO_LARGE")

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        return ToolResult(ok=True, data={
            "path": abs_path,
            "content": content[:max_bytes],
            "truncated": len(content) > max_bytes,
            "exists": True,
            "missing": False,
            "created": True
        })

    except Exception as e:
        return ToolResult(ok=False, error=str(e))
