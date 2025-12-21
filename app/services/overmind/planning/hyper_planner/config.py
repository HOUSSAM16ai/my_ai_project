import os


# --------------------------------------------------------------------------------------
# ENV Helpers
# --------------------------------------------------------------------------------------
def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(1 if default else 0)).strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


# --------------------------------------------------------------------------------------
# ENV Core Flags
# --------------------------------------------------------------------------------------
FORCE_AR = _env_flag("PLANNER_FORCE_ARABIC", False)
LANG_FALLBACK = os.getenv("PLANNER_LANGUAGE_FALLBACK", "ar").lower()
MAX_FILES = _env_int("PLANNER_MAX_FILES", 12)
DEFAULT_EXT = os.getenv("PLANNER_DEFAULT_EXT", ".md")
SMART_FN = _env_flag("PLANNER_SMART_FILENAME", True)
ALLOW_SUBDIRS = _env_flag("PLANNER_ALLOW_SUBDIRS", True)
GLOBAL_TASK_CAP = _env_int("PLANNER_MAX_TASKS_GLOBAL", 550)

MAX_CHUNKS = _env_int("PLANNER_MAX_CHUNKS", 100)  # Increased for extreme complexity
CHUNK_SIZE_HINT = _env_int("PLANNER_CHUNK_SIZE_HINT", 1400)
HARD_LINE_CAP = _env_int("PLANNER_HARD_LINE_CAP", 2_000_000)  # Increased for extreme complexity
FAST_SINGLE_THRESH = _env_int("PLANNER_FAST_SINGLE_THRESHOLD", 2200)
STREAM_ENABLE = _env_flag("PLANNER_STREAMING_ENABLE", True)
ALLOW_APPEND_MODE = os.getenv("PLANNER_ALLOW_APPEND_TOOL", "auto")
STREAM_MIN_CHUNKS = _env_int("PLANNER_STREAMING_MIN_CHUNKS", 2)

SECTION_INFER = _env_flag("PLANNER_ENABLE_SECTION_INFERENCE", True)
ROLE_DERIVATION = _env_flag("PLANNER_ENABLE_ROLE_DERIVATION", True)
ROLE_JSON = _env_flag("PLANNER_MULTI_ROLE_JSON", True)
CODE_HINTS = _env_flag("PLANNER_ENABLE_CODE_HINTS", True)
ENSURE_FILE = _env_flag("PLANNER_ENSURE_FILE", True)
STRICT_WRITE_ENF = _env_flag("PLANNER_STRICT_WRITE_ENFORCE", True)

COMPREHENSIVE_MODE = _env_flag("PLANNER_COMPREHENSIVE_MODE", False)
COMPREHENSIVE_FILE_NAME = os.getenv("PLANNER_COMPREHENSIVE_NAME", "COMPREHENSIVE_ANALYSIS.md")

INDEX_FILE_EN = _env_flag("PLANNER_INDEX_FILE", True) and not COMPREHENSIVE_MODE
INDEX_FILE_NAME = os.getenv("PLANNER_INDEX_NAME", "ARTIFACT_INDEX.md")

DEEP_INDEX_JSON_EN = _env_flag("PLANNER_DEEP_INDEX_JSON", True) and not COMPREHENSIVE_MODE
DEEP_INDEX_JSON_NAME = os.getenv("PLANNER_DEEP_INDEX_JSON_NAME", "STRUCTURAL_INDEX.json")
DEEP_INDEX_MD_EN = _env_flag("PLANNER_DEEP_INDEX_MD", True) and not COMPREHENSIVE_MODE
DEEP_INDEX_MD_NAME = os.getenv("PLANNER_DEEP_INDEX_MD_NAME", "STRUCTURAL_INDEX_SUMMARY.md")
DEEP_INDEX_MAX_JSON = _env_int("PLANNER_DEEP_INDEX_MAX_JSON_BYTES", 220_000)
DEEP_INDEX_SUMMARY_MAX = _env_int("PLANNER_DEEP_INDEX_SUMMARY_MAX_LEN", 6000)

STRUCT_SEMANTIC_THINK = _env_flag("PLANNER_STRUCT_SEMANTIC_THINK", True)
STRUCT_SEMANTIC_MAX_BYTES = _env_int("PLANNER_STRUCT_SEMANTIC_MAX_BYTES", 7000)
SEMANTIC_REUSE_INDEX = _env_flag("PLANNER_SEMANTIC_REUSE_INDEX", True)
INDEX_CACHE_ENABLE = _env_flag("PLANNER_INDEX_CACHE_ENABLE", False)

GLOBAL_CODE_SUMMARY_EN = _env_flag("PLANNER_GLOBAL_CODE_SUMMARY", True)
GLOBAL_CODE_SUMMARY_MAX_FILES = _env_int("PLANNER_GLOBAL_CODE_SUMMARY_MAX_FILES", 50)
GLOBAL_CODE_SUMMARY_MAX_BYTES = _env_int("PLANNER_GLOBAL_CODE_SUMMARY_MAX_BYTES", 62_000)

ALLOW_LIST_READ_ANALYSIS = _env_flag("PLANNER_ALLOW_LIST_READ_ANALYSIS", True)
CORE_READ_FILES = [
    f.strip()
    for f in os.getenv(
        "PLANNER_CORE_READ_FILES",
        "README.md,requirements.txt,Dockerfile,config.py,pyproject.toml,docker-compose.yml,.env",
    ).split(",")
    if f.strip()
]

EXTRA_READ_GLOBS = [
    g.strip() for g in os.getenv("PLANNER_EXTRA_READ_GLOBS", "").split(",") if g.strip()
]
SCAN_DIRS = [d.strip() for d in os.getenv("PLANNER_SCAN_DIRS", "").split(",") if d.strip()]
SCAN_RECURSIVE = _env_flag("PLANNER_SCAN_RECURSIVE", False)
SCAN_EXTS = {
    e.strip().lower() for e in os.getenv("PLANNER_SCAN_EXTS", ".py").split(",") if e.strip()
}
SCAN_MAX_FILES = _env_int("PLANNER_SCAN_MAX_FILES", 140)

OPTIONAL_GROUPS = [
    g.strip()
    for g in os.getenv(
        "PLANNER_OPTIONAL_TASK_GROUPS", "semantic,global_summary,deep_arch_report"
    ).split(",")
    if g.strip()
]

# --------------------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------------------
TOOL_THINK = "generic_think"
TOOL_WRITE = "write_file"
TOOL_APPEND = "append_file"
TOOL_ENSURE = "ensure_file"
TOOL_READ = "read_file"
TOOL_LIST = "list_dir"
