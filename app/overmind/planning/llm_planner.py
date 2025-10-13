# app/overmind/planning/llm_planner.py
"""
Ultra Hyper Semantic Planner + Deep Structural Index
Version: 7.3.0-ultra-l4++ (FINAL CONTEXT PIPELINE)

======================================================================
WHY THIS RELEASE (7.3.0 vs 7.2.0)?
======================================================================
Addresses prior residual issues:
- Avoids redundant deep_index rebuild (reuse in semantic stage).
- One-pass structural context derivation with optional semantic enrichment.
- Deterministic context source tagging (semantic|global|none).
- Safer streaming append (fixed wrap f-string; was bug in 7.2.0).
- Adaptive chunk reshaping when (#files * chunks) risks exceeding GLOBAL_TASK_CAP.
- Context injection fallback chain prioritized: semantic_struct > deep_index_summary > global_code_summary > none.
- Optional caching stub hook (future incremental index) via PLANNER_INDEX_CACHE_ENABLE (no-op placeholder).
- Consistent meta keys; legacy keys preserved for backward compatibility.
- Strict write enforcement preserved; auto-prunes optional tasks if cap pressure detected.

======================================================================
CORE PIPELINE (L4++ Semantic Generation)
======================================================================
1. Objective parsing → target files + language.
2. Optional core repo scan (list_dir + read core files).
3. Extra source gathering (globs + dirs).
4. Deep AST index (JSON / MD) (graceful failure).
5. Structural semantic THINK (optional) – reuses deep index data (no rebuild).
6. Global code summary (fallback or complement).
7. Role derivation (multi-file) + sections inference/refinement.
8. File generation (streamed append or batch) with STRUCT_CONTEXT injection.
9. Artifact index + deep architecture report (optional).
10. Meta telemetry export (all context + capacities + source origin).

======================================================================
SELECT ENV FLAGS (NEW / CHANGED)
======================================================================
# Language / Filenames
PLANNER_FORCE_ARABIC=0|1
PLANNER_LANGUAGE_FALLBACK=ar|en
PLANNER_MAX_FILES=12
PLANNER_DEFAULT_EXT=.md
PLANNER_SMART_FILENAME=1
PLANNER_ALLOW_SUBDIRS=1

# Chunking / Streaming
PLANNER_MAX_CHUNKS=60
PLANNER_CHUNK_SIZE_HINT=1400
PLANNER_HARD_LINE_CAP=1200000
PLANNER_FAST_SINGLE_THRESHOLD=2200
PLANNER_STREAMING_ENABLE=1
PLANNER_ALLOW_APPEND_TOOL=auto|1|0
PLANNER_STREAMING_MIN_CHUNKS=2        # NEW: ensure streaming only if >= this

# Intelligence
PLANNER_ENABLE_SECTION_INFERENCE=1
PLANNER_ENABLE_ROLE_DERIVATION=1
PLANNER_MULTI_ROLE_JSON=1
PLANNER_ENABLE_CODE_HINTS=1
PLANNER_ENSURE_FILE=1
PLANNER_STRICT_WRITE_ENFORCE=1

# Deep Index + Semantic
PLANNER_DEEP_INDEX_ENABLE=1
PLANNER_DEEP_INDEX_JSON=1
PLANNER_DEEP_INDEX_MD=1
PLANNER_DEEP_INDEX_JSON_NAME=STRUCTURAL_INDEX.json
PLANNER_DEEP_INDEX_MD_NAME=STRUCTURAL_INDEX_SUMMARY.md
PLANNER_DEEP_INDEX_MAX_JSON_BYTES=220000
PLANNER_DEEP_INDEX_SUMMARY_MAX_LEN=6000
PLANNER_STRUCT_SEMANTIC_THINK=1
PLANNER_STRUCT_SEMANTIC_MAX_BYTES=7000
PLANNER_SEMANTIC_REUSE_INDEX=1        # NEW: reuse index_data in semantic THINK (default on)
PLANNER_INDEX_CACHE_ENABLE=0          # Placeholder for future incremental caching

# Global Code Summary / Scan
PLANNER_GLOBAL_CODE_SUMMARY=1
PLANNER_GLOBAL_CODE_SUMMARY_MAX_FILES=50
PLANNER_GLOBAL_CODE_SUMMARY_MAX_BYTES=62000
PLANNER_EXTRA_READ_GLOBS=app/services/*.py,app/*.py
PLANNER_SCAN_DIRS=app/services
PLANNER_SCAN_RECURSIVE=1
PLANNER_SCAN_EXTS=.py
PLANNER_SCAN_MAX_FILES=140
PLANNER_ALLOW_LIST_READ_ANALYSIS=1
PLANNER_CORE_READ_FILES=README.md,requirements.txt,Dockerfile,config.py,pyproject.toml,docker-compose.yml,.env

# Artifact Index & Output
PLANNER_INDEX_FILE=1
PLANNER_INDEX_NAME=ARTIFACT_INDEX.md
PLANNER_COMPREHENSIVE_MODE=0

# Guardrails
PLANNER_MAX_TASKS_GLOBAL=550
PLANNER_OPTIONAL_TASK_GROUPS=semantic,global_summary,deep_arch_report # order of pruning under pressure

======================================================================
META FIELDS
======================================================================
language, files, requested_lines, total_chunks, per_chunk, streaming,
append_mode, role_task, section_task,
files_scanned, hotspot_count, duplicate_groups, index_version,
struct_index_attached, struct_index_json_task, struct_index_md_task,
struct_semantic_task, global_code_summary_task,
struct_context_injected, struct_context_source,
extra_source_files_count, container_files_detected,
scan_features_enabled, tasks_pruned, adaptive_chunking, task_budget

======================================================================
FALLBACK RULES
======================================================================
Priority of context injection:
1) struct_semantic_task.answer
2) struct_index_md_task.answer (summary)
3) global_code_summary_task.answer
4) (none -> no structural injection)

If nearing GLOBAL_TASK_CAP:
- Optional groups pruned by PLANNER_OPTIONAL_TASK_GROUPS order.
- Streaming may auto-downgrade to batch for fewer tasks (adaptive_chunking=True).

======================================================================
LICENSE / SAFETY
======================================================================
All operations are planning-only; actual tool invocation handled outside.
No destructive operations planned except file creation/append/write tokens assumed safe
under orchestrator validation.
"""

from __future__ import annotations

import glob
import json
import logging
import math
import os
import re
import time
from dataclasses import dataclass
from typing import Any

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("ultra_hyper_planner")
_lvl = os.getenv("LLM_PLANNER_LOG_LEVEL", "").upper()
_LOG.setLevel(getattr(logging, _lvl, logging.INFO) if _lvl else logging.INFO)
if not _LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# Base / Schemas (stubs if import fails and allowed)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB", "0") == "1"
try:
    from .base_planner import BasePlanner, PlannerError, PlanValidationError  # type: ignore
except Exception:
    if not _ALLOW_STUB:
        raise

    class PlannerError(Exception):
        def __init__(self, msg, planner="stub", objective="", **extra):
            super().__init__(msg)
            self.planner = planner
            self.objective = objective
            self.extra = extra

    class PlanValidationError(PlannerError): ...

    class BasePlanner:
        name = "stub"


try:
    from .schemas import MissionPlanSchema, PlannedTask, PlanningContext  # type: ignore
except Exception:
    if not _ALLOW_STUB:
        raise

    @dataclass
    class PlannedTask:
        task_id: str
        description: str
        tool_name: str
        tool_args: dict[str, Any]
        dependencies: list[str]

    @dataclass
    class MissionPlanSchema:
        objective: str
        tasks: list[PlannedTask]
        meta: dict[str, Any] = None

    class PlanningContext: ...


# --------------------------------------------------------------------------------------
# Deep Index Imports
# --------------------------------------------------------------------------------------
_DEEP_INDEX_ENABLED = os.getenv("PLANNER_DEEP_INDEX_ENABLE", "1") == "1"
if _DEEP_INDEX_ENABLED:
    try:
        from .deep_indexer import build_index, summarize_for_prompt  # type: ignore

        _HAS_INDEXER = True
    except Exception as _e:
        _LOG.warning("Deep indexer import failed: %s", _e)
        _HAS_INDEXER = False
else:
    _HAS_INDEXER = False


# --------------------------------------------------------------------------------------
# ENV Helpers
# --------------------------------------------------------------------------------------
def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except:
        return default


def _env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(int(1 if default else 0))).strip().lower() in (
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

MAX_CHUNKS = _env_int("PLANNER_MAX_CHUNKS", 60)
CHUNK_SIZE_HINT = _env_int("PLANNER_CHUNK_SIZE_HINT", 1400)
HARD_LINE_CAP = _env_int("PLANNER_HARD_LINE_CAP", 1_200_000)
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

# --------------------------------------------------------------------------------------
# Patterns & Sets
# --------------------------------------------------------------------------------------
FILENAME_PATTERNS = [
    r"\bfile\s+named\s+([A-Za-z0-9_\-./]+)",
    r"\bfiles?\s+named\s+([A-Za-z0-9_\-./,\s]+)",
    r"\bsave\s+(?:it\s+)?as\s+([A-Za-z0-9_\-./]+)",
    r"\bwrite\s+(?:to|into)\s+([A-Za-z0-9_\-./]+)",
    r"\boutput\s+to\s+([A-Za-z0-9_\-./]+)",
    r"\bdeliver(?:able)?\s+([A-Za-z0-9_\-./]+)",
    r"ملف\s+باسم\s+([A-Za-z0-9_\-./]+)",
    r"ملفات\s+باسم\s+([A-Za-z0-9_\-./,\s]+)",
    r"احفظه\s+في\s+([A-Za-z0-9_\-./]+)",
    r"اكتب\s+في\s+([A-Za-z0-9_\-./]+)",
    r"الناتج\s+في\s+([A-Za-z0-9_\-./]+)",
    r"مخرجات\s+في\s+([A-Za-z0-9_\-./]+)",
]
SEP_SPLIT = re.compile(r"\s*(?:,|و|and)\s*", re.IGNORECASE)
LINE_REQ = re.compile(r"(\d{2,9})\s*(?:lines?|أسطر|سطر)", re.IGNORECASE)
HUGE_TERMS = [
    "very large",
    "huge",
    "massive",
    "enormous",
    "gigantic",
    "immense",
    "ضخم",
    "هائل",
    "كبير جدا",
    "مليونية",
    "كثيرة جدا",
    "مليونية",
]

SECTION_HINTS_AR = [
    "مقدمة",
    "نظرة عامة",
    "تحليل",
    "معمارية",
    "تدفق البيانات",
    "مكونات",
    "تفاصيل",
    "مخاطر",
    "تحسينات",
    "توصيات",
    "خاتمة",
    "ملاحق",
]
SECTION_HINTS_EN = [
    "Introduction",
    "Overview",
    "Analysis",
    "Architecture",
    "Data Flow",
    "Components",
    "Details",
    "Risks",
    "Improvements",
    "Recommendations",
    "Conclusion",
    "Appendices",
]

CODE_EXTS = {
    ".py",
    ".js",
    ".ts",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".rb",
    ".rs",
    ".php",
    ".sh",
    ".ps1",
    ".sql",
}
DATA_EXTS = {".json", ".yml", ".yaml", ".ini", ".cfg", ".toml", ".csv", ".xml"}
DOC_EXTS = {".md", ".rst", ".txt", ".log", ".html", ".adoc"}


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def _has_arabic(s: str) -> bool:
    return any("\u0600" <= c <= "\u06ff" for c in s)


def _detect_lang(obj: str) -> str:
    if FORCE_AR:
        return "ar"
    low = obj.lower()
    if _has_arabic(obj) or "arabic" in low:
        return "ar"
    if "english" in low:
        return "en"
    return LANG_FALLBACK if LANG_FALLBACK in ("ar", "en") else "ar"


def _normalize_filename(fn: str) -> str:
    fn = fn.strip()
    if SMART_FN:
        fn = fn.replace("\\", "/").replace("//", "/")
        fn = re.sub(r"[^A-Za-z0-9_\-./]", "_", fn)
    if not ALLOW_SUBDIRS and "/" in fn:
        fn = fn.split("/")[-1]
    return fn


def _ensure_ext(fn: str) -> str:
    return fn if "." in fn else fn + DEFAULT_EXT


def extract_filenames(obj: str) -> list[str]:
    norm = " ".join(obj.split())
    out = []
    for pat in FILENAME_PATTERNS:
        for m in re.finditer(pat, norm, re.IGNORECASE):
            raw = m.group(1)
            if not raw:
                continue
            for p in SEP_SPLIT.split(raw):
                p = _normalize_filename(p)
                if not p:
                    continue
                if "." not in p:
                    p = _ensure_ext(p)
                if p.lower() not in [x.lower() for x in out]:
                    out.append(p)
                if len(out) >= MAX_FILES:
                    break
        if len(out) >= MAX_FILES:
            break
    if not out:
        guess = re.findall(r"\b([A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+))\b", norm)
        for g in guess:
            g = _normalize_filename(g)
            if g.lower() not in [x.lower() for x in out]:
                out.append(g)
            if len(out) >= MAX_FILES:
                break
    if not out:
        out = ["output" + DEFAULT_EXT]
    return out[:MAX_FILES]


def extract_requested_lines(obj: str) -> int | None:
    mx = None
    for m in LINE_REQ.finditer(obj):
        try:
            val = int(m.group(1))
            if mx is None or val > mx:
                mx = val
        except:
            pass
    if any(t in obj.lower() for t in HUGE_TERMS):
        mx = CHUNK_SIZE_HINT * 10 if mx is None else int(mx * 1.5)
    if mx and mx > HARD_LINE_CAP:
        mx = HARD_LINE_CAP
    return mx


def compute_chunk_plan(requested: int | None) -> tuple[int, int]:
    if not requested:
        requested = CHUNK_SIZE_HINT * 2
    if requested <= FAST_SINGLE_THRESH:
        return 1, requested
    chunk_count = math.ceil(requested / CHUNK_SIZE_HINT)
    if chunk_count > MAX_CHUNKS:
        chunk_count = MAX_CHUNKS
    per_chunk = max(80, math.ceil(requested / chunk_count))
    return chunk_count, per_chunk


def infer_sections(obj: str, lang: str) -> list[str]:
    if not SECTION_INFER:
        return []
    pat = re.compile(
        r"(?:sections?|أقسام|ضع\s+أقسام|include\s+sections?)\s*[:：]\s*(.+)", re.IGNORECASE
    )
    m = pat.search(obj)
    if m:
        tail = m.group(1)
        parts = re.split(r"[;,،]|(?:\band\b)|(?:\sو\s)", tail)
        cleaned = [p.strip(" .\t") for p in parts if p.strip()]
        return cleaned[:25]
    return (SECTION_HINTS_AR if lang == "ar" else SECTION_HINTS_EN)[:12]


def file_type(fn: str) -> str:
    ext = os.path.splitext(fn)[1].lower()
    if ext in CODE_EXTS:
        return "code"
    if ext in DATA_EXTS:
        return "data"
    if ext in DOC_EXTS:
        return "doc"
    return "generic"


def code_hint(ftype: str, lang: str) -> str:
    if not CODE_HINTS:
        return ""
    if ftype == "code":
        return (
            "أضف أمثلة كود وتعليقات عميقة.\n"
            if lang == "ar"
            else "Add deep code samples & commentary.\n"
        )
    if ftype == "data":
        return (
            "أضف سجلات نموذجية وشرح الحقول.\n"
            if lang == "ar"
            else "Provide sample records & field descriptions.\n"
        )
    return ""


def _truncate(s: str, max_chars: int) -> str:
    return s if len(s) <= max_chars else s[:max_chars] + "\n[TRUNCATED]"


def _tid(i: int) -> str:
    return f"t{i:02d}"


# --------------------------------------------------------------------------------------
# Prompt Builders
# --------------------------------------------------------------------------------------
def build_role_prompt(
    files: list[str], objective: str, lang: str, struct_ref: str | None = None
) -> str:
    listing = ", ".join(files)
    struct_block = f"\nSTRUCT_CONTEXT:\n{struct_ref}\n" if struct_ref else ""
    if lang == "ar":
        return (
            f"الهدف:\n{objective}\nالملفات: {listing}{struct_block}"
            "حدد لكل ملف دوراً فريداً بدون تداخل. أعد JSON: "
            "[{filename,focus,outline_points,rationale,risks,potential_extensions}]."
        )
    return (
        f"Objective:\n{objective}\nFiles: {listing}{struct_block}"
        "Assign each file a distinct role (no overlap). Return JSON: "
        "[{filename,focus,outline_points,rationale,risks,potential_extensions}]."
    )


def build_section_prompt(
    objective: str, draft_sections: list[str], lang: str, struct_ref: str | None = None
) -> str:
    listing = "\n".join(f"- {s}" for s in draft_sections)
    struct_block = f"\nSTRUCT_CONTEXT:\n{struct_ref}\n" if struct_ref else ""
    if lang == "ar":
        return (
            f"الهدف:\n{objective}\nالأقسام المقترحة:\n{listing}{struct_block}"
            "حسّن وأعد JSON: [{order,section_title,notes,priority}]."
        )
    return (
        f"Objective:\n{objective}\nDraft Sections:\n{listing}{struct_block}"
        "Refine -> JSON [{order,section_title,notes,priority}]."
    )


def build_chunk_prompt(
    objective: str,
    fname: str,
    role_id: str | None,
    section_id: str | None,
    cidx: int,
    ctotal: int,
    target_lines: int,
    lang: str,
    ftype: str,
    struct_placeholder: str | None = None,
    inline_struct: str = "",
) -> str:
    role_ref = f"{{{{{role_id}.answer}}}}" if role_id else "(no-role)"
    sect_ref = f"{{{{{section_id}.answer}}}}" if section_id else "(no-sections)"
    if struct_placeholder:
        struct_ref = f"\nSTRUCT_CONTEXT:\n{{{{{struct_placeholder}.answer}}}}"
    elif inline_struct:
        struct_ref = f"\nSTRUCT_CONTEXT:\n{_truncate(inline_struct,800)}"
    else:
        struct_ref = ""
    if lang == "ar":
        header = (
            f"الهدف:\n{objective}\nالملف:{fname}\nالدور:{role_ref}\nالأقسام:{sect_ref}{struct_ref}\n"
            f"جزء {cidx}/{ctotal} (~{target_lines} سطر)\n"
        )
        guide = (
            "- تابع تدريجياً.\n- لا خاتمة قبل الجزء الأخير.\n- أضف قوائم، أمثلة، مخاطر، تحسينات.\n"
            "- لا تكرر المقدمة كاملة.\n"
        )
        return header + guide + code_hint(ftype, lang)
    header = (
        f"Objective:\n{objective}\nFile:{fname}\nRole:{role_ref}\nSections:{sect_ref}{struct_ref}\n"
        f"Chunk {cidx}/{ctotal} (~{target_lines} lines)\n"
    )
    guide = (
        "- Maintain flow; no early finalization.\n- Add lists/examples/risks/refactor ideas.\n"
        "- Avoid full intro repetition.\n"
    )
    return header + guide + code_hint(ftype, lang)


def build_final_wrap_prompt(
    objective: str,
    fname: str,
    role_id: str | None,
    lang: str,
    struct_placeholder: str | None = None,
    inline_struct: str = "",
) -> str:
    role_ref = f"{{{{{role_id}.answer}}}}" if role_id else "(no-role)"
    if struct_placeholder:
        struct_ref = f"\nSTRUCT_CONTEXT:\n{{{{{struct_placeholder}.answer}}}}"
    elif inline_struct:
        struct_ref = f"\nSTRUCT_CONTEXT:\n{_truncate(inline_struct,800)}"
    else:
        struct_ref = ""
    if lang == "ar":
        return (
            f"الهدف:\n{objective}\nالملف:{fname}{struct_ref}\n"
            f"اكتب خلاصة تنفيذية موجزة (<=200 سطر) مبنية على {role_ref} وتتضمن توصيات عملية مرتبة."
        )
    return (
        f"Objective:\n{objective}\nFile:{fname}{struct_ref}\n"
        f"Produce an executive wrap (<=200 lines) leveraging {role_ref} + prioritized recommendations."
    )


# --------------------------------------------------------------------------------------
# Extra Source Scan
# --------------------------------------------------------------------------------------
def _collect_extra_files() -> list[str]:
    collected: set[str] = set()
    # Globs
    for pattern in EXTRA_READ_GLOBS:
        for p in glob.glob(pattern, recursive=True):
            if len(collected) >= SCAN_MAX_FILES:
                break
            if os.path.isfile(p):
                collected.add(p)
        if len(collected) >= SCAN_MAX_FILES:
            break
    # Directories
    for base in SCAN_DIRS:
        if not os.path.isdir(base):
            continue
        if SCAN_RECURSIVE:
            for root, _, files in os.walk(base):
                for f in files:
                    if len(collected) >= SCAN_MAX_FILES:
                        break
                    ext = os.path.splitext(f)[1].lower()
                    if ext in SCAN_EXTS:
                        collected.add(os.path.join(root, f))
                if len(collected) >= SCAN_MAX_FILES:
                    break
        else:
            for f in os.listdir(base):
                if len(collected) >= SCAN_MAX_FILES:
                    break
                fp = os.path.join(base, f)
                if os.path.isfile(fp):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in SCAN_EXTS:
                        collected.add(fp)
        if len(collected) >= SCAN_MAX_FILES:
            break
    return sorted(collected)[:SCAN_MAX_FILES]


def _container_files_present() -> list[str]:
    return [f for f in ("docker-compose.yml", ".env") if os.path.exists(f)]


# --------------------------------------------------------------------------------------
# Planner
# --------------------------------------------------------------------------------------
class UltraHyperPlanner(BasePlanner):
    name = "ultra_hyper_semantic_planner"
    version = "7.3.0-ultra-l4++"
    production_ready = True
    capabilities = {
        "semantic",
        "chunked",
        "multi-file",
        "arabic",
        "adaptive",
        "struct_index",
        "architecture",
        "telemetry",
        "global_scan",
    }
    tags = {"ultra", "hyper", "planner", "index", "semantic"}

    # ------------------------------------------------------------------
    def generate_plan(
        self,
        objective: str,
        context: PlanningContext | None = None,
        max_tasks: int | None = None,
    ) -> MissionPlanSchema:
        start = time.perf_counter()
        if not self._valid_objective(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        lang = _detect_lang(objective)
        files = self._resolve_target_files(objective)
        req_lines = extract_requested_lines(objective)
        total_chunks, per_chunk = compute_chunk_plan(req_lines)

        # Adaptive chunk reduction if risk of exceeding cap
        adaptive_chunking = False
        est_per_file_stream = total_chunks * 2 + (
            2 if total_chunks > 1 else 1
        )  # think+append per chunk + wrap pair
        est_tasks_core = 25  # overhead (scans + roles + sections + index etc.)
        projected = est_tasks_core + len(files) * est_per_file_stream
        if projected > GLOBAL_TASK_CAP and total_chunks > 1:
            # reduce chunks proportionally
            reduction_factor = projected / float(GLOBAL_TASK_CAP)
            new_total = max(1, int(total_chunks / math.ceil(reduction_factor)))
            if new_total < total_chunks:
                total_chunks = new_total
                per_chunk = max(
                    80, math.ceil((req_lines or CHUNK_SIZE_HINT * 2) / max(1, total_chunks))
                )
                adaptive_chunking = True

        streaming_possible = self._can_stream()
        use_stream = streaming_possible and STREAM_ENABLE and total_chunks >= STREAM_MIN_CHUNKS

        tasks: list[PlannedTask] = []
        idx = 1
        base_deps = []
        analysis_dependency_ids = []

        # ---------- Repo scan ----------
        if ALLOW_LIST_READ_ANALYSIS and self._wants_repo_scan(objective):
            idx = self._add_repo_scan_tasks(tasks, idx, analysis_dependency_ids)

        # ---------- Extra sources ----------
        extra_files = _collect_extra_files()
        extra_read_ids = []
        if extra_files:
            for ef in extra_files:
                tid = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=tid,
                        description=f"Read extra source {ef}.",
                        tool_name=TOOL_READ,
                        tool_args={"path": ef, "ignore_missing": True, "max_bytes": 50000},
                        dependencies=[],
                    )
                )
                extra_read_ids.append(tid)
            analysis_dependency_ids.extend(extra_read_ids)

        # ---------- Deep index ----------
        struct_meta, idx_meta = self._attempt_deep_index(tasks, idx, analysis_dependency_ids, lang)
        idx = idx_meta["next_idx"]
        index_deps = idx_meta["deps"]

        # Deep summary text (precomputed) for reuse
        deep_summary_text = struct_meta.get("summary_inline")

        # ---------- Semantic structural THINK ----------
        struct_semantic_task = None
        if struct_meta["attached"] and STRUCT_SEMANTIC_THINK:
            try:
                if SEMANTIC_REUSE_INDEX and deep_summary_text:
                    sem_source = deep_summary_text
                else:
                    # fallback regenerate summary
                    if _DEEP_INDEX_ENABLED and _HAS_INDEXER:
                        index_for_sem = build_index(".")
                        sem_source = summarize_for_prompt(
                            index_for_sem,
                            max_len=min(STRUCT_SEMANTIC_MAX_BYTES, DEEP_INDEX_SUMMARY_MAX),
                        )
                    else:
                        sem_source = deep_summary_text or ""
                sem_prompt_ar = (
                    "حلل الملخص البنيوي وأعد JSON:\n"
                    "{layers:[...],services:[...],infra:[...],utilities:[...],hotspots:[...],duplicates:[...],"
                    "refactor_opportunities:[{item,impact,effort}],risks:[{issue,likelihood,impact}],patterns:[...]}\n\n"
                    f"{_truncate(sem_source, STRUCT_SEMANTIC_MAX_BYTES)}"
                )
                sem_prompt_en = (
                    "Analyze structural summary -> JSON schema:\n"
                    "{layers:[...],services:[...],infra:[...],utilities:[...],hotspots:[...],duplicates:[...],"
                    "refactor_opportunities:[{item,impact,effort}],risks:[{issue,likelihood,impact}],patterns:[...]}\n\n"
                    f"{_truncate(sem_source, STRUCT_SEMANTIC_MAX_BYTES)}"
                )
                struct_semantic_task = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=struct_semantic_task,
                        description="Semantic structural JSON (enriched).",
                        tool_name=TOOL_THINK,
                        tool_args={"prompt": sem_prompt_ar if lang == "ar" else sem_prompt_en},
                        dependencies=index_deps,
                    )
                )
                index_deps.append(struct_semantic_task)
                struct_meta["struct_semantic_task"] = struct_semantic_task
            except Exception as e:
                _LOG.warning("Semantic structural step failed: %s", e)

        # ---------- Global code summary (optional) ----------
        global_code_summary_task = None
        if GLOBAL_CODE_SUMMARY_EN and extra_read_ids:
            try:
                if len(extra_read_ids) > GLOBAL_CODE_SUMMARY_MAX_FILES:
                    use_ids = extra_read_ids[:GLOBAL_CODE_SUMMARY_MAX_FILES]
                else:
                    use_ids = extra_read_ids
                refs = []
                for t in use_ids:
                    refs.append(f"[{t}] => {{{{{t}.answer.content}}}}")
                gc_prompt_ar = (
                    "لخص هذه الملفات إلى خريطة وحدات/خدمات/بنية/وظائف حرجة/تكرارات محتملة. "
                    "أعد JSON: {modules:[...],services:[...],infra:[...],utilities:[...],"
                    "notable_functions:[...],potential_containers:[...],global_risks:[...]}.\n"
                    + _truncate("\n".join(refs), GLOBAL_CODE_SUMMARY_MAX_BYTES)
                )
                gc_prompt_en = (
                    "Summarize files into repository map (modules/services/layers/critical funcs/duplicate hints). "
                    "Return JSON: {modules:[...],services:[...],infra:[...],utilities:[...],"
                    "notable_functions:[...],potential_containers:[...],global_risks:[...]}.\n"
                    + _truncate("\n".join(refs), GLOBAL_CODE_SUMMARY_MAX_BYTES)
                )
                global_code_summary_task = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=global_code_summary_task,
                        description="Global code semantic summary JSON.",
                        tool_name=TOOL_THINK,
                        tool_args={"prompt": gc_prompt_ar if lang == "ar" else gc_prompt_en},
                        dependencies=extra_read_ids,
                    )
                )
            except Exception as e:
                _LOG.warning("Global code summary failed: %s", e)

        # Determine context placeholder and source
        struct_placeholder_ref = None
        context_source = "none"
        if struct_semantic_task:
            struct_placeholder_ref = struct_semantic_task
            context_source = "semantic"
        elif struct_meta.get("md_task"):
            struct_placeholder_ref = struct_meta["md_task"]
            context_source = "deep_index_summary"
        elif global_code_summary_task:
            struct_placeholder_ref = global_code_summary_task
            context_source = "global"
        inline_struct = ""  # currently not used because we have placeholder references
        struct_meta["struct_context_injected"] = context_source != "none"

        # ---------- Roles ----------
        role_task_id = None
        if ROLE_DERIVATION and len(files) > 1:
            role_task_id = _tid(idx)
            idx += 1
            ref = f"{{{{{struct_placeholder_ref}.answer}}}}" if struct_placeholder_ref else ""
            tasks.append(
                PlannedTask(
                    task_id=role_task_id,
                    description="Derive unique roles JSON (no overlap).",
                    tool_name=TOOL_THINK,
                    tool_args={
                        "prompt": build_role_prompt(
                            files, objective, lang, struct_ref=_truncate(ref or "", 1100)
                        )
                    },
                    dependencies=index_deps or analysis_dependency_ids,
                )
            )

        # ---------- Sections ----------
        section_task_id = None
        inferred_sections = infer_sections(objective, lang)
        if inferred_sections:
            section_task_id = _tid(idx)
            idx += 1
            ref = f"{{{{{struct_placeholder_ref}.answer}}}}" if struct_placeholder_ref else ""
            tasks.append(
                PlannedTask(
                    task_id=section_task_id,
                    description="Refine sections JSON.",
                    tool_name=TOOL_THINK,
                    tool_args={
                        "prompt": build_section_prompt(
                            objective, inferred_sections, lang, struct_ref=_truncate(ref or "", 900)
                        )
                    },
                    dependencies=(
                        [role_task_id] if role_task_id else (index_deps or analysis_dependency_ids)
                    ),
                )
            )

        # ---------- File generation ----------
        final_writes = []
        idx = self._add_file_generation_blocks(
            tasks=tasks,
            idx=idx,
            files=files,
            objective=objective,
            lang=lang,
            role_task_id=role_task_id,
            section_task_id=section_task_id,
            analysis_deps=(index_deps or analysis_dependency_ids),
            total_chunks=total_chunks,
            per_chunk=per_chunk,
            use_stream=use_stream,
            final_writes=final_writes,
            struct_placeholder=struct_placeholder_ref,
            inline_struct=inline_struct,
        )

        # ---------- Comprehensive Analysis (replaces fragmented outputs) ----------
        if COMPREHENSIVE_MODE:
            idx = self._add_comprehensive_analysis(
                tasks, idx, lang, final_writes, files, struct_meta
            )
        else:
            # ---------- Artifact index ----------
            idx = self._maybe_add_artifact_index(tasks, idx, lang, final_writes, files)

            # ---------- Architecture deep report ----------
            deep_report_task = None
            if struct_meta["attached"]:
                deep_report_task = self._maybe_add_deep_arch_report(
                    tasks, idx, lang, (index_deps or analysis_dependency_ids), struct_meta
                )
                if deep_report_task:
                    idx = deep_report_task["next_idx"]
                    final_writes.append(deep_report_task["write_id"])

        # ---------- Optional pruning if cap exceeded ----------
        tasks_pruned = []
        idx, tasks_pruned = self._prune_if_needed(tasks, idx, final_writes)

        container_files = _container_files_present()
        meta = {
            "language": lang,
            "files": files,
            "requested_lines": req_lines,
            "total_chunks": total_chunks,
            "per_chunk": per_chunk,
            "streaming": use_stream,
            "append_mode": self._append_allowed(),
            "role_task": role_task_id,
            "section_task": section_task_id,
            # index telemetry
            "files_scanned": struct_meta.get("files_scanned"),
            "hotspot_count": struct_meta.get("hotspot_count"),
            "duplicate_groups": struct_meta.get("duplicate_groups"),
            "index_version": struct_meta.get("index_version"),
            "struct_index_attached": struct_meta["attached"],
            "struct_index_json_task": struct_meta.get("json_task"),
            "struct_index_md_task": struct_meta.get("md_task"),
            "struct_semantic_task": struct_meta.get("struct_semantic_task"),
            "global_code_summary_task": global_code_summary_task,
            "struct_context_injected": struct_meta.get("struct_context_injected"),
            "struct_context_source": context_source,
            # extras
            "extra_source_files_count": len(extra_files),
            "container_files_detected": container_files,
            "scan_features_enabled": bool(extra_files),
            # new telemetry
            "tasks_pruned": tasks_pruned,
            "adaptive_chunking": adaptive_chunking,
            "task_budget": {"cap": GLOBAL_TASK_CAP, "planned": len(tasks)},
        }

        plan = MissionPlanSchema(objective=objective, tasks=tasks, meta=meta)
        self._validate(plan, files)
        elapsed = (time.perf_counter() - start) * 1000
        _LOG.info(
            "[Planner v7.3.0] tasks=%d pruned=%d streaming=%s ctx=%s semantic=%s global=%s ms=%.1f",
            len(tasks),
            len(tasks_pruned),
            use_stream,
            context_source,
            bool(struct_semantic_task),
            bool(global_code_summary_task),
            elapsed,
        )
        return plan

    # ----------------------------------------------------------------------------------
    # Internal Steps
    # ----------------------------------------------------------------------------------
    def _add_repo_scan_tasks(
        self, tasks: list[PlannedTask], idx: int, deps_accum: list[str]
    ) -> int:
        for root in (".", "app"):
            tid = _tid(idx)
            idx += 1
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description=f"List directory '{root}' (struct awareness).",
                    tool_name=TOOL_LIST,
                    tool_args={"path": root, "max_entries": 600},
                    dependencies=[],
                )
            )
            deps_accum.append(tid)
        for cf in CORE_READ_FILES[:18]:
            tid = _tid(idx)
            idx += 1
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description=f"Read core file {cf} (ignore missing).",
                    tool_name=TOOL_READ,
                    tool_args={"path": cf, "ignore_missing": True, "max_bytes": 65000},
                    dependencies=[],
                )
            )
            deps_accum.append(tid)
        return idx

    def _attempt_deep_index(
        self, tasks: list[PlannedTask], idx: int, base_deps: list[str], lang: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        struct_meta = {"attached": False}
        deps_out = []
        if not (_DEEP_INDEX_ENABLED and _HAS_INDEXER):
            return struct_meta, {"next_idx": idx, "deps": deps_out}
        try:
            index_data = build_index(".")
            # cache placeholder (future): if INDEX_CACHE_ENABLE: ...
            struct_meta.update(
                {
                    "attached": True,
                    "files_scanned": index_data.get("files_scanned"),
                    "hotspot_count": (
                        len(index_data.get("complexity_hotspots_top50", []))
                        if index_data.get("complexity_hotspots_top50")
                        else None
                    ),
                    "duplicate_groups": (
                        len(index_data.get("duplicate_function_bodies", {}))
                        if index_data.get("duplicate_function_bodies")
                        else None
                    ),
                    "index_version": index_data.get("index_version", "ast-deep-v1"),
                }
            )
            # store summary inline (for semantic reuse)
            summary_text = summarize_for_prompt(index_data, max_len=DEEP_INDEX_SUMMARY_MAX)
            struct_meta["summary_inline"] = summary_text

            # JSON
            if DEEP_INDEX_JSON_EN:
                truncated_json = self._truncate_json(index_data, DEEP_INDEX_MAX_JSON)
                json_task = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=json_task,
                        description="Write structural index JSON.",
                        tool_name=TOOL_WRITE,
                        tool_args={"path": DEEP_INDEX_JSON_NAME, "content": truncated_json},
                        dependencies=base_deps,
                    )
                )
                deps_out.append(json_task)
                struct_meta["json_task"] = json_task
            # MD summary
            if DEEP_INDEX_MD_EN:
                header = (
                    "## Structural AST Index Summary\n"
                    if lang != "ar"
                    else "## ملخص الفهرسة البنائية (AST)\n"
                )
                md_content = header + "\n```\n" + summary_text + "\n```\n"
                md_task = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=md_task,
                        description="Write structural summary markdown.",
                        tool_name=TOOL_WRITE,
                        tool_args={"path": DEEP_INDEX_MD_NAME, "content": md_content},
                        dependencies=base_deps,
                    )
                )
                deps_out.append(md_task)
                struct_meta["md_task"] = md_task
        except Exception as e:
            _LOG.warning("Deep index failed: %s", e)
        return struct_meta, {"next_idx": idx, "deps": deps_out}

    def _truncate_json(self, data: dict[str, Any], max_bytes: int) -> str:
        raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        if len(raw.encode("utf-8")) <= max_bytes:
            return raw
        slim = dict(data)
        if "modules" in slim:
            slim["modules"] = [
                {
                    "path": m.get("path"),
                    "fn_count": len(m.get("functions", [])),
                    "class_count": len(m.get("classes", [])),
                }
                for m in slim["modules"][:250]
            ]
        raw2 = json.dumps(slim, ensure_ascii=False, separators=(",", ":"))
        if len(raw2.encode("utf-8")) <= max_bytes:
            return raw2
        return raw2[: max_bytes - 60] + "...TRUNCATED..."

    def _add_file_generation_blocks(
        self,
        tasks: list[PlannedTask],
        idx: int,
        files: list[str],
        objective: str,
        lang: str,
        role_task_id: str | None,
        section_task_id: str | None,
        analysis_deps: list[str],
        total_chunks: int,
        per_chunk: int,
        use_stream: bool,
        final_writes: list[str],
        struct_placeholder: str | None,
        inline_struct: str,
    ) -> int:
        for fname in files:
            base_deps = []
            if role_task_id:
                base_deps.append(role_task_id)
            if section_task_id:
                base_deps.append(section_task_id)
            if analysis_deps and not base_deps:
                base_deps = analysis_deps

            if ENSURE_FILE:
                ensure_id = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=ensure_id,
                        description=f"Ensure file {fname} exists.",
                        tool_name=TOOL_ENSURE,
                        tool_args={
                            "path": fname,
                            "initial_content": self._initial_banner(fname, objective, lang),
                        },
                        dependencies=[],
                    )
                )
                base_deps.append(ensure_id)

            ftype = file_type(fname)

            if use_stream and self._append_allowed() and total_chunks > 1:
                prev = None
                for c in range(1, total_chunks + 1):
                    think_id = _tid(idx)
                    idx += 1
                    prompt = build_chunk_prompt(
                        objective,
                        fname,
                        role_task_id,
                        section_task_id,
                        c,
                        total_chunks,
                        per_chunk,
                        lang,
                        ftype,
                        struct_placeholder=struct_placeholder,
                        inline_struct=inline_struct,
                    )
                    deps = base_deps.copy()
                    if prev:
                        deps.append(prev)
                    tasks.append(
                        PlannedTask(
                            task_id=think_id,
                            description=f"Stream chunk {c}/{total_chunks} for {fname}.",
                            tool_name=TOOL_THINK,
                            tool_args={"prompt": prompt},
                            dependencies=deps,
                        )
                    )
                    append_id = _tid(idx)
                    idx += 1
                    tasks.append(
                        PlannedTask(
                            task_id=append_id,
                            description=f"Append chunk {c} to {fname}.",
                            tool_name=TOOL_APPEND,
                            tool_args={"path": fname, "content": f"{{{{{think_id}.answer}}}}"},
                            dependencies=[think_id],
                        )
                    )
                    prev = append_id
                wrap_think = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=wrap_think,
                        description=f"Generate final wrap (stream) for {fname}.",
                        tool_name=TOOL_THINK,
                        tool_args={
                            "prompt": build_final_wrap_prompt(
                                objective,
                                fname,
                                role_task_id,
                                lang,
                                struct_placeholder,
                                inline_struct,
                            )
                        },
                        dependencies=[prev] if prev else base_deps,
                    )
                )
                wrap_append = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=wrap_append,
                        description=f"Append final wrap to {fname}.",
                        tool_name=TOOL_APPEND,
                        tool_args={"path": fname, "content": f"\n\n{{{{{wrap_think}.answer}}}}"},
                        dependencies=[wrap_think],
                    )
                )
                final_writes.append(wrap_append)
            else:
                chunk_thinks = []
                for c in range(1, total_chunks + 1):
                    think_id = _tid(idx)
                    idx += 1
                    prompt = build_chunk_prompt(
                        objective,
                        fname,
                        role_task_id,
                        section_task_id,
                        c,
                        total_chunks,
                        per_chunk,
                        lang,
                        ftype,
                        struct_placeholder,
                        inline_struct,
                    )
                    deps = base_deps.copy()
                    if chunk_thinks:
                        deps.append(chunk_thinks[-1])
                    tasks.append(
                        PlannedTask(
                            task_id=think_id,
                            description=f"Batch chunk {c}/{total_chunks} for {fname}.",
                            tool_name=TOOL_THINK,
                            tool_args={"prompt": prompt},
                            dependencies=deps,
                        )
                    )
                    chunk_thinks.append(think_id)
                wrap_think = None
                if total_chunks > 1:
                    wrap_think = _tid(idx)
                    idx += 1
                    tasks.append(
                        PlannedTask(
                            task_id=wrap_think,
                            description=f"Generate final wrap (batch) for {fname}.",
                            tool_name=TOOL_THINK,
                            tool_args={
                                "prompt": build_final_wrap_prompt(
                                    objective,
                                    fname,
                                    role_task_id,
                                    lang,
                                    struct_placeholder,
                                    inline_struct,
                                )
                            },
                            dependencies=[chunk_thinks[-1]],
                        )
                    )
                parts = [f"{{{{{cid}.answer}}}}" for cid in chunk_thinks]
                if wrap_think:
                    parts.append(f"\n\n{{{{{wrap_think}.answer}}}}")
                combined = "\n\n".join(parts)
                write_id = _tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=write_id,
                        description=f"Write composed file {fname} (batch).",
                        tool_name=TOOL_WRITE,
                        tool_args={"path": fname, "content": combined},
                        dependencies=[chunk_thinks[-1]] if chunk_thinks else base_deps,
                    )
                )
                final_writes.append(write_id)
        return idx

    def _maybe_add_artifact_index(
        self, tasks: list[PlannedTask], idx: int, lang: str, deps: list[str], files: list[str]
    ) -> int:
        if not (INDEX_FILE_EN and len(files) > 1):
            return idx
        idx_think = _tid(idx)
        idx += 1
        p_ar = "أنشئ فهرساً موجزاً لكل ملف (سطران: التركيز والاستخدام)."
        p_en = "Create concise artifact index (2 lines per file: focus & usage)."
        tasks.append(
            PlannedTask(
                task_id=idx_think,
                description="Generate artifact index.",
                tool_name=TOOL_THINK,
                tool_args={"prompt": p_ar if lang == "ar" else p_en},
                dependencies=deps,
            )
        )
        idx_write = _tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=idx_write,
                description=f"Write artifact index {INDEX_FILE_NAME}.",
                tool_name=TOOL_WRITE,
                tool_args={"path": INDEX_FILE_NAME, "content": f"{{{{{idx_think}.answer}}}}"},
                dependencies=[idx_think],
            )
        )
        return idx

    def _maybe_add_deep_arch_report(
        self,
        tasks: list[PlannedTask],
        idx: int,
        lang: str,
        deps: list[str],
        struct_meta: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not struct_meta.get("attached"):
            return None
        prompt_ar = (
            "حلل بيانات الفهرس (JSON + ملخص) وقدم تقرير معمارية متقدم "
            "(طبقات، خدمات، تبعيات، نقاط ساخنة، تكرار، أولويات refactor، مخاطر، فرص تحسين). "
            "Markdown منظم مختصر."
        )
        prompt_en = (
            "Analyze structural index (JSON + summary) → advanced architecture report "
            "(layers, services, dependencies, hotspots, duplicates, refactor priorities, risks, improvements). "
            "Return concise structured Markdown."
        )
        think_id = _tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=think_id,
                description="Synthesize deep architecture report.",
                tool_name=TOOL_THINK,
                tool_args={"prompt": prompt_ar if lang == "ar" else prompt_en},
                dependencies=deps,
            )
        )
        write_id = _tid(idx)
        idx += 1
        out_name = "DEEP_ARCHITECTURE_REPORT.md"
        tasks.append(
            PlannedTask(
                task_id=write_id,
                description=f"Write deep architecture report {out_name}.",
                tool_name=TOOL_WRITE,
                tool_args={"path": out_name, "content": f"{{{{{think_id}.answer}}}}"},
                dependencies=[think_id],
            )
        )
        return {"next_idx": idx, "write_id": write_id, "think_id": think_id}

    def _add_comprehensive_analysis(
        self,
        tasks: list[PlannedTask],
        idx: int,
        lang: str,
        deps: list[str],
        files: list[str],
        struct_meta: dict[str, Any],
    ) -> int:
        """Create one comprehensive analysis file instead of multiple fragmented files."""
        prompt_ar = """حلل المشروع بشكل شامل وقدم تقرير واحد متكامل يتضمن:

- طبقات النظام والخدمات (الحاويات الثلاث: db, web, ai_service)
- التبعيات والعلاقات بين المكونات
- النقاط الساخنة والمناطق الحرجة في الكود

- ملخص الملفات الرئيسية ووظائفها
- الفئات والوظائف المهمة
- نقاط الدخول والواجهات البرمجية

- التكرار في الكود وفرص التحسين
- فرص إعادة الهيكلة والتنظيم
- المخاطر المحتملة ونقاط الضعف

- أولويات التحسين والتطوير
- الخطوات التالية المقترحة
- أفضل الممارسات للصيانة

قدم تحليل عميق ومنظم بذكاء خارق في ملف واحد شامل."""

        prompt_en = """Analyze the project comprehensively and provide one integrated report including:

- System layers and services (three containers: db, web, ai_service)
- Dependencies and relationships between components
- Hotspots and critical areas in the code

- Summary of key files and their functions
- Important classes and functions
- Entry points and APIs

- Code duplication and improvement opportunities
- Refactoring and reorganization opportunities
- Potential risks and weaknesses

- Improvement and development priorities
- Suggested next steps
- Best practices for maintenance

Provide deep, organized analysis with superhuman intelligence in one comprehensive file."""

        think_id = _tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=think_id,
                description="Generate comprehensive project analysis.",
                tool_name=TOOL_THINK,
                tool_args={"prompt": prompt_ar if lang == "ar" else prompt_en},
                dependencies=deps,
            )
        )

        write_id = _tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=write_id,
                description=f"Write comprehensive analysis {COMPREHENSIVE_FILE_NAME}.",
                tool_name=TOOL_WRITE,
                tool_args={
                    "path": COMPREHENSIVE_FILE_NAME,
                    "content": f"{{{{{think_id}.answer}}}}",
                },
                dependencies=[think_id],
            )
        )

        return idx

    def _prune_if_needed(
        self, tasks: list[PlannedTask], idx: int, final_writes: list[str]
    ) -> tuple[int, list[str]]:
        if len(tasks) <= GLOBAL_TASK_CAP:
            return idx, []
        pruned = []
        # Build quick lookup by category (semantic/global_summary/deep_arch_report)
        group_map = {
            "semantic": lambda t: "Semantic structural JSON" in t.description,
            "global_summary": lambda t: "Global code semantic summary" in t.description,
            "deep_arch_report": lambda t: "deep architecture report" in t.description.lower(),
        }
        id_to_task = {t.task_id: t for t in tasks}
        # Remove groups until under cap
        for group in OPTIONAL_GROUPS:
            if len(tasks) <= GLOBAL_TASK_CAP:
                break
            matcher = group_map.get(group)
            if not matcher:
                continue
            removable = [t for t in tasks if matcher(t)]
            if not removable:
                continue
            for rt in removable:
                # Avoid removing final file writes that might satisfy STRICT enforcement (architecture report is optional though)
                if rt.task_id in final_writes:
                    continue
                tasks.remove(rt)
                pruned.append(rt.task_id)
                if len(tasks) <= GLOBAL_TASK_CAP:
                    break
        return idx, pruned

    # ----------------------------------------------------------------------------------
    # Utilities
    # ----------------------------------------------------------------------------------
    def _resolve_target_files(self, objective: str) -> list[str]:
        raw = extract_filenames(objective)
        normalized = []
        for f in raw:
            nf = _normalize_filename(f)
            if "." not in nf:
                nf = _ensure_ext(nf)
            if nf.lower() not in [x.lower() for x in normalized]:
                normalized.append(nf)
        return normalized[:MAX_FILES]

    def _can_stream(self) -> bool:
        mode = ALLOW_APPEND_MODE
        if mode == "0":
            return False
        if mode == "1":
            return True
        allowed_env = os.getenv("PLANNER_ALLOWED_TOOLS", "")
        if allowed_env:
            allowed = {t.strip() for t in allowed_env.split(",") if t.strip()}
            return "append_file" in allowed
        return True

    def _append_allowed(self) -> bool:
        return self._can_stream()

    def _wants_repo_scan(self, objective: str) -> bool:
        low = objective.lower()
        return any(
            k in low
            for k in (
                "repository",
                "repo",
                "structure",
                "architecture",
                "معمار",
                "هيكل",
                "بنية",
                "analyze project",
            )
        )

    def _initial_banner(self, fname: str, objective: str, lang: str) -> str:
        ext = fname.lower()
        trunc = objective[:220]
        if ext.endswith((".md", ".txt", ".log", ".rst", ".adoc", ".html")):
            return (
                (f"# تهيئة: {fname}\n\n> الهدف: {trunc}...\n\n")
                if lang == "ar"
                else (f"# Init: {fname}\n\n> Objective: {trunc}...\n\n")
            )
        if any(ext.endswith(e) for e in CODE_EXTS):
            return f"# Scaffold for objective: {objective[:150]}\n\n"
        if any(ext.endswith(e) for e in DATA_EXTS):
            return f"# Data artifact scaffold: {objective[:150]}\n"
        return ""

    def _validate(self, plan: MissionPlanSchema, files: list[str]):
        if len(plan.tasks) > GLOBAL_TASK_CAP:
            raise PlanValidationError("excessive_tasks", self.name, plan.objective)
        ids = {t.task_id for t in plan.tasks}
        for t in plan.tasks:
            for d in t.dependencies:
                if d not in ids:
                    raise PlanValidationError(
                        f"dangling_dependency:{t.task_id}->{d}", self.name, plan.objective
                    )
        if STRICT_WRITE_ENF:
            for f in files:
                if not any(
                    (tt.tool_name in (TOOL_WRITE, TOOL_APPEND))
                    and (tt.tool_args or {}).get("path", "").lower() == f.lower()
                    for tt in plan.tasks
                ):
                    raise PlanValidationError(f"missing_file_write:{f}", self.name, plan.objective)

    def _valid_objective(self, objective: str) -> bool:
        if not objective or len(objective.strip()) < 5:
            return False
        if objective.strip().isdigit():
            return False
        return True


# Backward alias
LLMGroundedPlanner = UltraHyperPlanner

__all__ = [
    "UltraHyperPlanner",
    "LLMGroundedPlanner",
    "MissionPlanSchema",
    "PlannedTask",
    "PlanningContext",
    "PlannerError",
    "PlanValidationError",
]

# --------------------------------------------------------------------------------------
# Self-test (manual)
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    planner = UltraHyperPlanner()
    demo = (
        "Analyze repository architecture, container layout and create file named "
        "ARCHITECTURE_overmind.md plus additional performance report"
    )
    plan = planner.generate_plan(demo)
    print("Meta:", json.dumps(plan.meta, ensure_ascii=False, indent=2))
    print("Tasks:", len(plan.tasks))
