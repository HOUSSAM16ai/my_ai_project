"""
Hyper-Memory Tools
==================
Ephemeral key-value store operations.
"""

import json

from .core import tool
from .definitions import _MEMORY_ALLOWLIST, ToolResult
from .globals import _MEMORY_LOCK, _MEMORY_STORE


@tool(
    name="memory_put",
    description="Store a small JSON-serializable string under a key (ephemeral).",
    category="memory",
    capabilities=["kv_store"],
    parameters={
        "type": "object",
        "properties": {
            "key": {"type": "string"},
            "value": {"type": "string", "description": "JSON-serializable string content"},
        },
        "required": ["key", "value"],
    },
)
def memory_put(key: str, value: str) -> ToolResult:
    if len(key) > 120:
        return ToolResult(ok=False, error="KEY_TOO_LONG")
    if len(value) > 50_000:
        return ToolResult(ok=False, error="VALUE_TOO_LONG")
    if _MEMORY_ALLOWLIST and key not in _MEMORY_ALLOWLIST:
        return ToolResult(ok=False, error="KEY_NOT_ALLOWED")
    try:
        json.dumps(value)
    except Exception:
        return ToolResult(ok=False, error="VALUE_NOT_SERIALIZABLE")
    with _MEMORY_LOCK:
        _MEMORY_STORE[key] = value
    return ToolResult(ok=True, data={"stored": True, "key": key})

@tool(
    name="memory_get",
    description="Retrieve a value by key from ephemeral memory.",
    category="memory",
    capabilities=["kv_store"],
    parameters={"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]},
)
def memory_get(key: str) -> ToolResult:
    with _MEMORY_LOCK:
        if key not in _MEMORY_STORE:
            return ToolResult(ok=False, error="KEY_NOT_FOUND")
        return ToolResult(ok=True, data={"key": key, "value": _MEMORY_STORE[key]})
