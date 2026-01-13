"""
Hyper-Global State Container
============================
Separated to avoid circular dependency loops in the Neural Mesh.
"""

import threading

# ======================================================================================
# Ephemeral Memory
# ======================================================================================
_MEMORY_STORE: dict[str, object] = {}
_MEMORY_LOCK = threading.Lock()

# ======================================================================================
# Structural Map & Layer Stats
# ======================================================================================
_DEEP_STRUCT_MAP: dict[str, object] | None = None
_DEEP_STRUCT_HASH: str | None = None
_DEEP_STRUCT_LOADED_AT: float = 0.0
_DEEP_LOCK = threading.Lock()

_LAYER_STATS: dict[str, dict[str, object]] = {}
_LAYER_LOCK = threading.Lock()

# ======================================================================================
# Registries
# ======================================================================================
_TOOL_REGISTRY: dict[str, dict[str, object]] = {}
_TOOL_STATS: dict[str, dict[str, object]] = {}
_ALIAS_INDEX: dict[str, str] = {}
_CAPABILITIES: dict[str, list[str]] = {}
_REGISTRY_LOCK = threading.Lock()
