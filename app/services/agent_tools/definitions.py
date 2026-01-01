"""
Hyper-Constants & Definition Matrix for Agent Tools
===================================================
Part of the Omni-Plan Refactoring Initiative.
"""

import os
from dataclasses import asdict, dataclass

# ======================================================================================
# Version
# ======================================================================================
__version__ = "4.5.0-hyper-l5++-omniplan"

# ======================================================================================
# Data Structures
# ======================================================================================
@dataclass
class ToolResult:
    ok: bool
    data: dict[str, str | int | bool] = None
    error: str | None = None
    meta: dict[str, Any] = None
    trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

# ======================================================================================
# Helpers
# ======================================================================================
def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def _bool_env(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(1 if default else 0)).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

# ======================================================================================
# Core Limits / Config
# ======================================================================================
PROJECT_ROOT = os.path.abspath(os.getenv("AGENT_TOOLS_PROJECT_ROOT", "/app"))

MAX_WRITE_BYTES = _int_env("AGENT_TOOLS_MAX_WRITE_BYTES", 5_000_000)
MAX_APPEND_BYTES = _int_env("AGENT_TOOLS_MAX_APPEND_BYTES", 3_000_000)
MAX_READ_BYTES = _int_env("AGENT_TOOLS_MAX_READ_BYTES", 800_000)

ENFORCE_APPEND_TOTAL = _bool_env("AGENT_TOOLS_APPEND_ENFORCE_TOTAL", True)
HASH_AFTER_WRITE = _bool_env("AGENT_TOOLS_HASH_AFTER_WRITE", True)
COMPRESS_JSON = _bool_env("AGENT_TOOLS_COMPRESS_JSON", True)

GENERIC_THINK_MAX_CHARS = _int_env("GENERIC_THINK_MAX_CHARS_INPUT", 12_000)
GENERIC_THINK_MAX_ANSWER_CHARS = _int_env("GENERIC_THINK_MAX_ANSWER_CHARS", 24_000)

AUTOFILL = _bool_env("AGENT_TOOLS_AUTOFILL_MISSING", True)
AUTOFILL_EXT = os.getenv("AGENT_TOOLS_AUTOFILL_EXTENSION", ".txt")
ACCEPT_DOTTED = _bool_env("AGENT_TOOLS_ACCEPT_DOTTED", True)
FORCE_INTENT = _bool_env("AGENT_TOOLS_FORCE_INTENT", True)

DISABLED: set[str] = {t.strip() for t in os.getenv("DISABLED_TOOLS", "").split(",") if t.strip()}
DISPATCH_ALLOW: set[str] = {
    t.strip() for t in os.getenv("DISPATCH_ALLOWLIST", "").split(",") if t.strip()
}

_MEMORY_ALLOWLIST: set[str] | None = None
_mem_list_raw = os.getenv("MEMORY_ALLOWLIST", "").strip()
if _mem_list_raw:
    _MEMORY_ALLOWLIST = {k.strip() for k in _mem_list_raw.split(",") if k.strip()}

AUTO_CREATE_ENABLED = _bool_env("AGENT_TOOLS_CREATE_MISSING", True)
AUTO_CREATE_DEFAULT_CONTENT = os.getenv(
    "AGENT_TOOLS_CREATE_DEFAULT_CONTENT", "Auto-generated placeholder file."
)
AUTO_CREATE_ALLOWED_EXTS = {
    e.strip().lower()
    for e in os.getenv("AGENT_TOOLS_CREATE_ALLOWED_EXTS", ".md,.txt,.json,.log").split(",")
    if e.strip()
}
AUTO_CREATE_MAX_BYTES = _int_env("AGENT_TOOLS_CREATE_MAX_BYTES", 300_000)

# Structural Map Config
DEEP_MAP_PATH = os.getenv("AGENT_TOOLS_DEEP_MAP_PATH", "")
DEEP_MAP_TTL = _int_env("AGENT_TOOLS_DEEP_MAP_TTL", 60)  # seconds
DEEP_LIMIT_KEYS = _int_env("AGENT_TOOLS_DEEP_LIMIT_KEYS", 0)

# Index / Search Config
CODE_INDEX_MAX_FILES = _int_env("CODE_INDEX_MAX_FILES", 2200)
CODE_INDEX_INCLUDE_EXTS = (
    os.getenv("CODE_INDEX_INCLUDE_EXTS", ".py,.md,.txt,.js,.ts,.json,.yml,.yaml").lower().split(",")
)
CODE_INDEX_EXCLUDE_DIRS = {
    d.strip()
    for d in os.getenv(
        "CODE_INDEX_EXCLUDE_DIRS", ".git,__pycache__,venv,.venv,node_modules,dist,build"
    ).split(",")
    if d.strip()
}
CODE_INDEX_MAX_FILE_BYTES = _int_env("CODE_INDEX_MAX_FILE_BYTES", 180_000)

CODE_SEARCH_MAX_RESULTS = _int_env("CODE_SEARCH_MAX_RESULTS", 24)
CODE_SEARCH_MAX_SNIPPET_LINES = _int_env("CODE_SEARCH_MAX_SNIPPET_LINES", 14)
CODE_SEARCH_CONTEXT_RADIUS = _int_env("CODE_SEARCH_CONTEXT_RADIUS", 3)
CODE_SEARCH_FILE_MAX_BYTES = _int_env("CODE_SEARCH_FILE_MAX_BYTES", 130_000)

SEMANTIC_SEARCH_ENABLED = _bool_env("SEMANTIC_SEARCH_ENABLED", False)
SEMANTIC_SEARCH_FAKE_LATENCY_MS = _int_env("SEMANTIC_SEARCH_FAKE_LATENCY_MS", 0)

# ======================================================================================
# Canonical / Alias Definitions
# ======================================================================================
CANON_WRITE = "write_file"
CANON_WRITE_IF_CHANGED = "write_file_if_changed"
CANON_READ = "read_file"
CANON_THINK = "generic_think"

WRITE_SUFFIXES = {"write", "create", "generate", "append", "touch"}
READ_SUFFIXES = {"read", "open", "load", "view", "show"}

WRITE_KEYWORDS = {"write", "create", "generate", "append", "produce", "persist", "save"}
READ_KEYWORDS = {"read", "inspect", "load", "open", "view", "show", "display"}

WRITE_ALIASES_BASE = {
    "file_writer",
    "file_system",
    "file_system_tool",
    "file_writer_tool",
    "writer",
    "create_file",
    "make_file",
}
READ_ALIASES_BASE = {"file_reader", "file_reader_tool"}
WRITE_DOTTED_ALIASES = {f"file_system.{s}" for s in WRITE_SUFFIXES}
READ_DOTTED_ALIASES = {f"file_system.{s}" for s in READ_SUFFIXES}

SUPPORTED_TYPES = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}
