"""
File System Tools (Refactored)
==============================

This module provides tools for file system operations.
It delegates logic to specialized handlers in `domain.filesystem`.
"""

# Re-export constants for backward compatibility if needed,
# though ideally they should be imported from config.
from app.services.agent_tools.domain.filesystem.config import MAX_READ_BYTES
from app.services.agent_tools.domain.filesystem.handlers.meta_handlers import (
    file_exists_logic,
    list_dir_logic,
)

# Import Logic Handlers
from app.services.agent_tools.domain.filesystem.handlers.read_handlers import (
    read_bulk_files_logic,
    read_file_logic,
)
from app.services.agent_tools.domain.filesystem.handlers.write_handlers import (
    append_file_logic,
    delete_file_logic,
    ensure_directory_logic,
    ensure_file_logic,
    write_file_if_changed_logic,
    write_file_logic,
)
from app.services.agent_tools.tool_model import ToolResult, tool

# ======================================================================================
# Tool Definitions (Decorated wrappers)
# ======================================================================================


@tool(
    name="read_file",
    description="Read content of a text file (auto-truncated).",
    category="fs",
    capabilities=["fs", "read"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_bytes": {"type": "integer", "default": MAX_READ_BYTES},
            "ignore_missing": {"type": "boolean", "default": False},
        },
        "required": ["path"],
    },
)
def read_file(
    path: str, max_bytes: int = MAX_READ_BYTES, ignore_missing: bool = False
) -> ToolResult:
    return read_file_logic(path, max_bytes, ignore_missing)


@tool(
    name="write_file",
    description="Write content to a file (overwrite).",
    category="fs",
    capabilities=["fs", "write"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
            "compress_json_if_large": {"type": "boolean", "default": False},
        },
        "required": ["path", "content"],
    },
)
def write_file(path: str, content: str, compress_json_if_large: bool = False) -> ToolResult:
    return write_file_logic(path, content, compress_json_if_large)


@tool(
    name="write_file_if_changed",
    description="Write file only if content differs.",
    category="fs",
    capabilities=["fs", "write"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)
def write_file_if_changed(path: str, content: str) -> ToolResult:
    return write_file_if_changed_logic(path, content)


@tool(
    name="append_file",
    description="Append content to a file.",
    category="fs",
    capabilities=["fs", "write"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)
def append_file(path: str, content: str) -> ToolResult:
    return append_file_logic(path, content)


@tool(
    name="file_exists",
    description="Check path existence and type.",
    category="fs",
    capabilities=["fs", "meta"],
    parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def file_exists(path: str) -> ToolResult:
    return file_exists_logic(path)


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
    return list_dir_logic(path, max_entries)


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
    return delete_file_logic(path, confirm)


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
    return ensure_file_logic(
        path, max_bytes, initial_content, force_create, allow_create, enforce_ext
    )


@tool(
    name="ensure_directory",
    description="Ensure a directory exists.",
    category="fs",
    capabilities=["fs", "ensure"],
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
        },
        "required": ["path"],
    },
)
def ensure_directory(path: str) -> ToolResult:
    return ensure_directory_logic(path)


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
    return read_bulk_files_logic(paths, max_bytes_per_file, ignore_missing, merge_mode)
