import os


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except Exception:
        return default


def _env_flag(name: str, default: bool = False) -> bool:
    raw = _env(name, "1" if default else "0").lower()
    return raw in ("1", "true", "yes", "on")

# Snapshot configuration for introspection
CONFIG = {
    "CACHE_ENABLE": _env_flag("PLANNER_INDEX_CACHE_ENABLE", False),
    "CACHE_DIR": _env("DEEP_INDEX_CACHE_DIR", ".planner_cache"),
    "MAX_FILE_BYTES": _env_int("DEEP_INDEX_MAX_FILE_BYTES", 300_000),
    "MAX_FILES": _env_int("DEEP_INDEX_MAX_FILES", 4000),
    "THREADS": _env_int("DEEP_INDEX_THREADS", 4),
    "EXCLUDE_DIRS": [
        d.strip()
        for d in _env(
            "DEEP_INDEX_EXCLUDE_DIRS",
            ".git,__pycache__,venv,env,.venv,node_modules,dist,build,migrations",
        ).split(",")
        if d.strip()
    ],
    "INCLUDE_GLOBS": [
        g.strip() for g in _env("DEEP_INDEX_INCLUDE_GLOBS", "").split(",") if g.strip()
    ],
    "INTERNAL_PREFIXES": tuple(
        p.strip() for p in _env("DEEP_INDEX_INTERNAL_PREFIXES", "app,src").split(",") if p.strip()
    ),
    "DUP_HASH_PREFIX": _env_int("DEEP_INDEX_DUP_HASH_PREFIX", 16),
    "HOTSPOT_COMPLEXITY": _env_int("DEEP_INDEX_COMPLEXITY_HOTSPOT_CX", 12),
    "HOTSPOT_LOC": _env_int("DEEP_INDEX_COMPLEXITY_HOTSPOT_LOC", 120),
    "CALL_GRAPH_ENABLE": _env_flag("DEEP_INDEX_CALL_GRAPH", True),
    "LAYER_HEURISTICS": _env_flag("DEEP_INDEX_LAYER_HEURISTICS", True),
    "SUMMARY_EXTRA": _env_flag("DEEP_INDEX_SUMMARY_EXTRA", True),
    "DETECT_SERVICES": _env_flag("DEEP_INDEX_DETECT_SERVICES", True),
    "MAX_CALL_GRAPH_EDGES": _env_int("DEEP_INDEX_MAX_CALL_GRAPH_EDGES", 12_000),
    "MAX_DUP_GROUPS": _env_int("DEEP_INDEX_MAX_DUP_GROUPS", 250),
    "TIME_PROFILE": _env_flag("DEEP_INDEX_TIME_PROFILE", True),
}
