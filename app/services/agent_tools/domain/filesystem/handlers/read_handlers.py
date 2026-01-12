"""
Handlers for reading files.
"""

import gzip
import os

from app.services.agent_tools.domain.filesystem.config import MAX_READ_BYTES
from app.services.agent_tools.domain.filesystem.validators.path_validator import (
    validate_file,
    validate_path,
)
from app.services.agent_tools.tool_model import ToolResult


def read_file_logic(
    path: str, max_bytes: int = MAX_READ_BYTES, ignore_missing: bool = False
) -> ToolResult:
    """
    Reads content from a file with safety limits.
    """
    try:
        if ignore_missing:
            # Check existence manually without raising first
            try:
                abs_path = validate_path(path, allow_missing=True)
                if not os.path.exists(abs_path):
                    return ToolResult(
                        ok=True,
                        data={"path": abs_path, "content": "", "exists": False, "missing": True},
                    )
            except ValueError as e:
                return ToolResult(ok=False, error=str(e))

        # Normal validation
        try:
            abs_path = validate_file(path)
        except (FileNotFoundError, IsADirectoryError, ValueError) as e:
            # Map Python exceptions to ToolResult errors expected by tests
            str(e)
            if isinstance(e, FileNotFoundError):
                return ToolResult(ok=False, error="FILE_NOT_FOUND")
            if isinstance(e, IsADirectoryError):
                return ToolResult(ok=False, error="IS_DIRECTORY")
            return ToolResult(ok=False, error=str(e))

        max_eff = min(max_bytes, MAX_READ_BYTES)

        # Gzip handling
        if abs_path.lower().endswith(".gz"):
            # Note: The original implementation returned raw bytes decoded as utf-8 or empty string on fail
            # We strictly follow the test expectation: return some content and binary_mode=True
            try:
                with gzip.open(abs_path, "rt", encoding="utf-8") as f:
                    content = f.read(max_eff + 10)
            except Exception:
                # Fallback or just return raw preview if possible?
                # Original code read as rb then decode.
                with open(abs_path, "rb") as f:
                    raw = f.read(max_eff)
                content = raw.decode("utf-8", errors="replace")

            truncated = len(content) > max_eff
            return ToolResult(
                ok=True,
                data={
                    "path": abs_path,
                    "content": content[:max_eff],
                    "truncated": truncated,
                    "exists": True,
                    "binary_mode": True,
                },
            )

        # Normal Text
        with open(abs_path, encoding="utf-8", errors="replace") as f:
            content = f.read(max_eff + 10)

        truncated = len(content) > max_eff
        preview = content[:max_eff]

        return ToolResult(
            ok=True,
            data={"path": abs_path, "content": preview, "truncated": truncated, "exists": True},
        )

    except Exception as e:
        return ToolResult(ok=False, error=str(e))


def read_bulk_files_logic(
    paths: list[str],
    max_bytes_per_file: int = 60000,
    ignore_missing: bool = True,
    merge_mode: str = "json",
) -> ToolResult:
    """Reads multiple files."""
    out = []
    max_eff = int(min(max_bytes_per_file, MAX_READ_BYTES))
    total_chars = 0

    for p in paths:
        try:
            # We use validate_path(allow_missing=True) so we can handle existence check manually
            abs_path = validate_path(p, allow_missing=True)

            if not os.path.exists(abs_path):
                if ignore_missing:
                    out.append({"path": abs_path, "exists": False, "content": ""})
                    continue
                return ToolResult(ok=False, error=f"FILE_NOT_FOUND:{p}")

            if os.path.isdir(abs_path):
                out.append({"path": abs_path, "exists": False, "error": "IS_DIRECTORY"})
                continue

            if os.path.getsize(abs_path) > max_eff:
                with open(abs_path, encoding="utf-8", errors="replace") as f:
                    content = f.read(max_eff)
                truncated = True
            else:
                with open(abs_path, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                truncated = False

            total_chars += len(content)
            out.append(
                {"path": abs_path, "exists": True, "truncated": truncated, "content": content}
            )

            if total_chars > 1_500_000:
                break

        except Exception as e:
            if not ignore_missing:
                return ToolResult(ok=False, error=str(e))
            out.append({"path": p, "exists": False, "error": str(e)})

    if merge_mode == "concat":
        merged = "\n\n".join(
            f"# {os.path.basename(o['path'])}\n{o.get('content', '')}"
            for o in out
            if o.get("content")
        )
        return ToolResult(
            ok=True,
            data={
                "mode": "concat",
                "content": merged,
                "files_count": len(out),
                "total_chars": len(merged),
            },
        )

    return ToolResult(ok=True, data={"mode": "json", "files": out, "files_count": len(out)})
