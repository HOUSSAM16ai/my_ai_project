"""
Hyper-File System Tools
=======================
Safe, structural-aware file manipulation.
"""

import gzip
import os

from .core import CANON_READ, CANON_WRITE, CANON_WRITE_IF_CHANGED, tool
from .definitions import (
    AUTO_CREATE_ALLOWED_EXTS,
    AUTO_CREATE_DEFAULT_CONTENT,
    AUTO_CREATE_ENABLED,
    AUTO_CREATE_MAX_BYTES,
    ENFORCE_APPEND_TOTAL,
    MAX_APPEND_BYTES,
    MAX_READ_BYTES,
    MAX_WRITE_BYTES,
    READ_ALIASES_BASE,
    READ_DOTTED_ALIASES,
    WRITE_ALIASES_BASE,
    WRITE_DOTTED_ALIASES,
    ToolResult,
)
from .structural_logic import (
    _annotate_struct_meta,
    _apply_struct_limit,
    _maybe_hash_and_size,
    _touch_layer,
)
from .utils import _content_hash, _file_hash, _safe_path


@tool(
    name="ensure_directory",
    description="Ensure a directory exists (create parents). Returns created/existed.",
    category="fs",
    capabilities=["fs", "ensure"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "must_be_new": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    },
)
def ensure_directory(path: str, must_be_new: bool = False) -> ToolResult:
    try:
        abs_path = _safe_path(path)
        if os.path.exists(abs_path):
            if not os.path.isdir(abs_path):
                return ToolResult(ok=False, error="PATH_EXISTS_NOT_DIR")
            if must_be_new:
                return ToolResult(ok=False, error="DIR_ALREADY_EXISTS")
            return ToolResult(ok=True, data={"path": abs_path, "created": False, "exists": True})
        os.makedirs(abs_path, exist_ok=True)
        return ToolResult(ok=True, data={"path": abs_path, "created": True, "exists": True})
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name=CANON_WRITE,
    description="Create or overwrite a UTF-8 file. Supports large JSON compression.",
    category="fs",
    capabilities=["fs", "write"],
    aliases=list(WRITE_ALIASES_BASE | WRITE_DOTTED_ALIASES),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "enforce_ext": {"type": "string"},
            "compress_json_if_large": {"type": "boolean", "default": True},
        },
        "required": ["path", "content"],
    },
)
def write_file(
    path: str, content: str, enforce_ext: str | None = None, compress_json_if_large: bool = True
) -> ToolResult:
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")
        # COMPRESS_JSON
        if compress_json_if_large and path.lower().endswith(".json") and len(content) > 400_000:
            gz_path = path + ".gz" if not path.lower().endswith(".gz") else path
            path = gz_path
            out_bytes = gzip.compress(content.encode("utf-8"))
            if len(out_bytes) > MAX_WRITE_BYTES:
                return ToolResult(ok=False, error="COMPRESSED_TOO_LARGE")
            abs_path = _safe_path(path, enforce_ext=[os.path.splitext(path)[1]])
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "wb") as f:
                f.write(out_bytes)
            data = {
                "written": abs_path,
                "bytes": len(out_bytes),
                "compressed": True,
                "original_len": len(content),
            }
            _annotate_struct_meta(abs_path, data)
            _maybe_hash_and_size(abs_path, data)
            if data.get("struct_layer"):
                _touch_layer(data["struct_layer"], "writes")
            _apply_struct_limit(data)
            return ToolResult(ok=True, data=data)
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_WRITE_BYTES:
            return ToolResult(ok=False, error="WRITE_TOO_LARGE")
        enforce_list = [enforce_ext] if enforce_ext else None
        abs_path = _safe_path(path, must_exist_parent=False, enforce_ext=enforce_list)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        data = {"written": abs_path, "bytes": len(encoded), "compressed": False}
        _annotate_struct_meta(abs_path, data)
        _maybe_hash_and_size(abs_path, data)
        if data.get("struct_layer"):
            _touch_layer(data["struct_layer"], "writes")
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name=CANON_WRITE_IF_CHANGED,
    description="Write only if content hash changes (skip if identical).",
    category="fs",
    capabilities=["fs", "write", "optimize"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "enforce_ext": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)
def write_file_if_changed(path: str, content: str, enforce_ext: str | None = None) -> ToolResult:
    try:
        abs_path = _safe_path(path, enforce_ext=[enforce_ext] if enforce_ext else None)
        new_hash = _content_hash(content)
        if os.path.exists(abs_path):
            existing_hash = _file_hash(abs_path)
            if existing_hash == new_hash:
                data = {
                    "path": abs_path,
                    "skipped": True,
                    "reason": "UNCHANGED",
                    "hash": existing_hash,
                }
                _annotate_struct_meta(abs_path, data)
                if data.get("struct_layer"):
                    _touch_layer(data["struct_layer"], "writes")
                _apply_struct_limit(data)
                return ToolResult(ok=True, data=data)

        # Only pass enforce_ext if it's provided to avoid validation errors on None
        kwargs = {"path": path, "content": content}
        if enforce_ext is not None:
            kwargs["enforce_ext"] = enforce_ext

        return write_file(**kwargs)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="append_file",
    description="Append UTF-8 text. Enforces total size if configured.",
    category="fs",
    capabilities=["fs", "write", "stream"],
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"],
    },
)
def append_file(path: str, content: str) -> ToolResult:
    try:
        if not isinstance(content, str):
            return ToolResult(ok=False, error="CONTENT_NOT_STRING")
        encoded = content.encode("utf-8")
        # if len(encoded) > MAX_APPEND_BYTES:
        #     return ToolResult(ok=False, error="APPEND_CHUNK_TOO_LARGE")
        abs_path = _safe_path(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if ENFORCE_APPEND_TOTAL and os.path.exists(abs_path):
            current = os.path.getsize(abs_path)
            if current + len(encoded) > MAX_APPEND_BYTES:
                return ToolResult(ok=False, error="APPEND_TOTAL_LIMIT_EXCEEDED")
        with open(abs_path, "a", encoding="utf-8") as f:
            f.write(content)
        data = {"appended": abs_path, "bytes": len(encoded)}
        _annotate_struct_meta(abs_path, data)
        _maybe_hash_and_size(abs_path, data)
        if data.get("struct_layer"):
            _touch_layer(data["struct_layer"], "appends")
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name=CANON_READ,
    description="Read UTF-8 text (soft-missing support).",
    category="fs",
    capabilities=["fs", "read"],
    aliases=list(READ_ALIASES_BASE | READ_DOTTED_ALIASES),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer", "default": 20000},
            "ignore_missing": {"type": "boolean", "default": True},
        },
        "required": ["path"],
    },
)
def read_file(path: str, max_bytes: int = 20000, ignore_missing: bool = True) -> ToolResult:
    try:
        max_eff = int(min(max_bytes, MAX_READ_BYTES))
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            if ignore_missing:
                data = {
                    "path": abs_path,
                    "content": "",
                    "truncated": False,
                    "exists": False,
                    "missing": True,
                }
                _annotate_struct_meta(abs_path, data)
                if data.get("struct_layer"):
                    _touch_layer(data["struct_layer"], "reads")
                _apply_struct_limit(data)
                return ToolResult(ok=True, data=data)
            return ToolResult(ok=False, error="FILE_NOT_FOUND")
        if os.path.isdir(abs_path):
            return ToolResult(ok=False, error="IS_DIRECTORY")
        mode = "rb" if abs_path.lower().endswith(".gz") else "r"
        if mode == "rb":
            with open(abs_path, "rb") as f:
                data_bytes = f.read(max_eff + 10)
            truncated = len(data_bytes) > max_eff
            try:
                text = data_bytes[:max_eff].decode("utf-8", errors="replace")
            except Exception:
                text = ""
            res = {
                "path": abs_path,
                "content": text,
                "truncated": truncated,
                "exists": True,
                "missing": False,
                "binary_mode": True,
            }
            _annotate_struct_meta(abs_path, res)
            if res.get("struct_layer"):
                _touch_layer(res["struct_layer"], "reads")
            _apply_struct_limit(res)
            return ToolResult(ok=True, data=res)
        with open(abs_path, encoding="utf-8") as f:
            data_txt = f.read(max_eff + 10)
        truncated = len(data_txt) > max_eff
        res = {
            "path": abs_path,
            "content": data_txt[:max_eff],
            "truncated": truncated,
            "exists": True,
            "missing": False,
        }
        _annotate_struct_meta(abs_path, res)
        if res.get("struct_layer"):
            _touch_layer(res["struct_layer"], "reads")
        _apply_struct_limit(res)
        return ToolResult(ok=True, data=res)
    except UnicodeDecodeError:
        return ToolResult(ok=False, error="NOT_UTF8_TEXT")
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="file_exists",
    description="Check path existence and type.",
    category="fs",
    capabilities=["fs", "meta"],
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def file_exists(path: str) -> ToolResult:
    try:
        abs_path = _safe_path(path)
        data = {
            "path": abs_path,
            "exists": os.path.exists(abs_path),
            "is_dir": os.path.isdir(abs_path),
            "is_file": os.path.isfile(abs_path),
        }
        _annotate_struct_meta(abs_path, data)
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="list_dir",
    description="List directory entries (name,type,size).",
    category="fs",
    capabilities=["fs", "meta"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "default": "."},
            "max_entries": {"type": "integer", "default": 400},
        },
    },
)
def list_dir(path: str = ".", max_entries: int = 400) -> ToolResult:
    try:
        abs_path = _safe_path(path)
        if not os.path.isdir(abs_path):
            return ToolResult(ok=False, error="NOT_A_DIRECTORY")
        entries = []
        for name in sorted(os.listdir(abs_path))[:max_entries]:
            p = os.path.join(abs_path, name)
            entries.append(
                {
                    "name": name,
                    "is_dir": os.path.isdir(p),
                    "is_file": os.path.isfile(p),
                    "size": os.path.getsize(p) if os.path.isfile(p) else None,
                }
            )
        data = {"path": abs_path, "entries": entries}
        _annotate_struct_meta(abs_path, data)
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="delete_file",
    description="Delete a file (confirm=True required).",
    category="fs",
    capabilities=["fs", "write"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "confirm": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    },
)
def delete_file(path: str, confirm: bool = False) -> ToolResult:
    try:
        if not confirm:
            return ToolResult(ok=False, error="CONFIRM_REQUIRED")
        abs_path = _safe_path(path)
        if not os.path.exists(abs_path):
            return ToolResult(ok=False, error="FILE_NOT_FOUND")
        if os.path.isdir(abs_path):
            return ToolResult(ok=False, error="IS_DIRECTORY")
        os.remove(abs_path)
        data = {"deleted": True, "path": abs_path}
        _annotate_struct_meta(abs_path, data)
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="ensure_file",
    description="Ensure text file exists; create if allowed.",
    category="fs",
    capabilities=["fs", "ensure"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer", "default": 40000},
            "initial_content": {"type": "string", "default": ""},
            "force_create": {"type": "boolean", "default": False},
            "allow_create": {"type": "boolean", "default": True},
            "enforce_ext": {"type": "string"},
        },
        "required": ["path"],
    },
)
def ensure_file(
    path: str,
    max_bytes: int = 40000,
    initial_content: str = "",
    force_create: bool = False,
    allow_create: bool = True,
    enforce_ext: str | None = None,
) -> ToolResult:
    try:
        max_eff = int(min(max_bytes, MAX_READ_BYTES))
        lowered = path.lower()
        if enforce_ext:
            if not lowered.endswith(enforce_ext.lower()):
                return ToolResult(ok=False, error="EXTENSION_MISMATCH")
        else:
            if AUTO_CREATE_ALLOWED_EXTS and not any(
                lowered.endswith(x) for x in AUTO_CREATE_ALLOWED_EXTS
            ):
                return ToolResult(ok=False, error="EXT_NOT_ALLOWED")
        abs_path = _safe_path(path)
        path_exists = os.path.exists(abs_path)
        if path_exists and not force_create:
            if os.path.isdir(abs_path):
                return ToolResult(ok=False, error="IS_DIRECTORY")
            mode = "rb" if abs_path.lower().endswith(".gz") else "r"
            if mode == "rb":
                with open(abs_path, "rb") as f:
                    d = f.read(max_eff + 10)
                truncated = len(d) > max_eff
                try:
                    preview = d[:max_eff].decode("utf-8", errors="replace")
                except Exception:
                    preview = ""
            else:
                with open(abs_path, encoding="utf-8") as f:
                    d = f.read(max_eff + 10)
                truncated = len(d) > max_eff
                preview = d[:max_eff]
            data = {
                "path": abs_path,
                "content": preview,
                "truncated": truncated,
                "exists": True,
                "missing": False,
                "created": False,
            }
            _annotate_struct_meta(abs_path, data)
            if data.get("struct_layer"):
                _touch_layer(data["struct_layer"], "ensures")
            _apply_struct_limit(data)
            return ToolResult(ok=True, data=data)
        if not path_exists and (not allow_create or not AUTO_CREATE_ENABLED):
            return ToolResult(ok=False, error="FILE_NOT_FOUND")
        content = initial_content if initial_content.strip() else AUTO_CREATE_DEFAULT_CONTENT
        encoded = content.encode("utf-8")
        if len(encoded) > AUTO_CREATE_MAX_BYTES:
            return ToolResult(ok=False, error="INITIAL_CONTENT_TOO_LARGE")
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        data = {
            "path": abs_path,
            "content": content[:max_eff],
            "truncated": len(content) > max_eff,
            "exists": True,
            "missing": False,
            "created": True,
        }
        _annotate_struct_meta(abs_path, data)
        if data.get("struct_layer"):
            _touch_layer(data["struct_layer"], "ensures")
        _apply_struct_limit(data)
        return ToolResult(ok=True, data=data)
    except UnicodeDecodeError:
        return ToolResult(ok=False, error="NOT_UTF8_TEXT")
    except Exception as e:
        return ToolResult(ok=False, error=str(e))


@tool(
    name="read_bulk_files",
    description="Read multiple small text files. Returns JSON or concatenated blob.",
    category="fs",
    capabilities=["fs", "read", "batch"],
    parameters={
        "type": "object",
        "properties": {
            "paths": {"type": "array", "default": []},
            "max_bytes_per_file": {"type": "integer", "default": 60000},
            "ignore_missing": {"type": "boolean", "default": True},
            "merge_mode": {"type": "string", "default": "json", "description": "json|concat"},
        },
        "required": ["paths"],
    },
)
def read_bulk_files(
    paths: list[str],
    max_bytes_per_file: int = 60000,
    ignore_missing: bool = True,
    merge_mode: str = "json",
) -> ToolResult:
    out = []
    max_eff = int(min(max_bytes_per_file, MAX_READ_BYTES))
    total_chars = 0
    for p in paths:
        try:
            abs_path = _safe_path(p)
            if not os.path.exists(abs_path):
                if ignore_missing:
                    out.append({"path": abs_path, "exists": False, "content": ""})
                    continue
                else:
                    return ToolResult(ok=False, error=f"FILE_NOT_FOUND:{p}")
            if os.path.isdir(abs_path):
                out.append({"path": abs_path, "exists": False, "error": "IS_DIRECTORY"})
                continue
            if os.path.getsize(abs_path) > max_eff:
                # Partial read
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
            if total_chars > 1_500_000:  # Hard safety limit
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
