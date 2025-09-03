# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
# -*- coding: utf-8 -*-
"""
LLM GROUNDED PLANNER (LEVEL‑4 DEEP SCAN + CUSTOM ARTIFACT RESPECT)
==================================================================
Version : 4.3.0-l4-custom
Status  : Production / Hardened / Filename-Aware
Author  : Overmind Orchestrator Core (Extended)

Summary
-------
إصدار محسَّن يعالج المشكلة التي واجهتها: تجاهل اسم الملف الذي يطلبه المستخدم
(THE BUG: planner كان دائماً ينتج ARCHITECTURE_PRINCIPLES.md أو الاسم المفروض من البيئة
حتى عندما تطلب "file named X"). هذا الإصدار:

1. يعطي أولوية مطلقة لأي اسم (أسماء) ملفات يذكرها المستخدم بصيغة "file named X"
   (أو "files named X and Y" / "create file X" fallback).
2. يمكنه استخراج عدة ملفات (multi-artifact) وإنتاج خطة تكتبها جميعاً إذا رغبت.
3. يضيق شروط النمط المعماري l4_architecture_deep_scan لتفادي الاستحواذ على مهام غير
   معمارية (لن يُفعَّل إلا إذا احتوى الهدف على architecture | architectural | principles
   أو مصطلحات قوية مماثلة).
4. يعطِّل FORCE_REPORT_NAME إذا تم اكتشاف اسم ملف مخصص (إلا إذا أجبرت override).
5. يوفر طبقة Post-Process تحترم enforced_filename(s) ولا تسمح بكتابة الملف الافتراضي
   إذا تم تحديد اسم مخصص.
6. يحقن Meta غني: meta.requested_filenames / meta.pattern / meta.filename_strategy
7. يحافظ على خصائص الـ Level‑4 السابقة (list_dir / read_file / think / synthesis).
8. يضيف حماية ضد تجاوز الحد الأقصى للمهام + فحص مخاطر مبسط.
9. دعم اختيار تعطيل multi-artifact عبر متغير بيئة.

New / Updated Environment Flags
-------------------------------
PLANNER_L4_ENABLED=1|0
PLANNER_RESPECT_CUSTOM_FILENAME=1|0         (default 1)  احترم اسم المستخدم
PLANNER_ALLOW_MULTI_FILES=1|0               (default 1)  إنتاج عدة ملفات إن وُجدت
PLANNER_MIN_ARCH_SIGNAL=1|0                 (default 1)  يتطلب إشارة معمارية صريحة لتفعيل النمط
PLANNER_FORCE_REPORT_NAME=<name>            (ثابت، يتجاهله إن وجد اسم مخصص ما لم تُجبر)
PLANNER_FORCE_REPORT_NAME_STRICT=1|0        (default 0) إذا 1 يتجاوز الأسماء المخصصة (غير مستحسن)
PLANNER_L4_FINAL_FILENAME_HINT=ARCHITECTURE_PRINCIPLES.md (fallback)
PLANNER_FILE_SECONDARY_EXT=.md              الامتداد الافتراضي
PLANNER_FILENAME_REQUIRE_EXT=1|0            (default 1) تأكد من وجود امتداد
PLANNER_FILENAME_AUTO_APPEND_EXT=1|0        (default 1)
PLANNER_MAX_CUSTOM_FILES=3                  الحد الأقصى للملفات التي سيلبّيها في مهمة واحدة

(بقية المتغيرات القديمة محفوظة + موثقة في التعليقات.)

Usage Notes
-----------
- إذا ذكرت ملفاً: "create file named houssam-benemerah.md" سيتم احترامه.
- إذا ذكرت عدة: "create files named a.md and b.md" سينتج write_file لكل منهما (حتى 3).
- إذا لم تذكر "file named" لكنه ذكر "architecture report" سيستخدم النمط ويختار fallback.
- لتجربة التعطيل المؤقت للنمط: PLANNER_L4_ENABLED=0
- للتراجع لسلوك سابق (غير مستحسن): PLANNER_RESPECT_CUSTOM_FILENAME=0

Arabic
------
يستمر دعم الكشف التلقائي للعربية لتوليد Prompts بالعربية عند رصد حروف عربية أو كلمة arabic.

"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Iterable

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("llm_planner")
_env_level = os.getenv("LLM_PLANNER_LOG_LEVEL", "").upper()
if _env_level:
    _LOG.setLevel(getattr(logging, _env_level, logging.INFO))
else:
    _LOG.setLevel(logging.INFO)
if not _LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# Base / Schemas Imports (fallback stub)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB", "0") == "1"
try:
    from .base_planner import (
        BasePlanner,
        PlannerError,
        PlanValidationError,
    )
except Exception as _e:  # pragma: no cover
    if not _ALLOW_STUB:
        raise RuntimeError(
            "Failed to import base_planner (set LLM_PLANNER_ALLOW_STUB=1 for dev stub)."
        ) from _e

    class PlannerError(Exception):  # type: ignore
        def __init__(self, msg: str, planner: str = "stub", objective: str = "", **extra):
            super().__init__(msg)
            self.planner = planner
            self.objective = objective
            self.extra = extra or {}

    class PlanValidationError(PlannerError):  # type: ignore
        pass

    class BasePlanner:  # type: ignore
        name = "base_planner_stub"

        @classmethod
        def live_planner_classes(cls):
            return {}

        @classmethod
        def planner_metadata(cls):
            return {}

    _LOG.error("USING STUB BasePlanner (development mode).")

from .schemas import MissionPlanSchema, PlannedTask, PlanningContext  # type: ignore

# --------------------------------------------------------------------------------------
# Optional Services
# --------------------------------------------------------------------------------------
try:
    from app.services import maestro  # type: ignore
except Exception:
    maestro = None  # type: ignore

try:
    from app.services import agent_tools  # type: ignore
except Exception:
    agent_tools = None  # type: ignore

CANON_FUNC = getattr(agent_tools, "canonicalize_tool_name", None) if agent_tools else None

# --------------------------------------------------------------------------------------
# Environment / Config (Extended)
# --------------------------------------------------------------------------------------
STRICT_JSON_ONLY = os.getenv("LLM_PLANNER_STRICT_JSON", "0") == "1"
FALLBACK_ALLOW = os.getenv("FALLBACK_ALLOW", "1") == "1"
MAX_TASKS_GLOBAL = int(os.getenv("LLM_PLANNER_MAX_TASKS", "40"))

AUTO_FIX_FILE_TASKS = os.getenv("PLANNER_AUTO_FIX_FILE_TASKS", "1") == "1"
FORCE_FILE_TOOLS = os.getenv("PLANNER_FORCE_FILE_TOOLS", "1") == "1"
FILE_DEFAULT_EXT = os.getenv("PLANNER_FILE_DEFAULT_EXT", ".md")
FILE_DEFAULT_CONTENT = os.getenv(
    "PLANNER_FILE_DEFAULT_CONTENT",
    "Placeholder content (auto-generated)."
)
ALLOWED_TOOLS_RAW = os.getenv(
    "PLANNER_ALLOWED_TOOLS",
    "list_dir,read_file,ensure_file,generic_think,write_file"
)
ALLOWED_TOOLS = {t.strip() for t in ALLOWED_TOOLS_RAW.split(",") if t.strip()}
ENFORCE_ALLOWED = os.getenv("PLANNER_ENFORCE_ALLOWED_TOOLS", "1") == "1"
FORCE_REPORT_NAME = os.getenv("PLANNER_FORCE_REPORT_NAME", "").strip() or None
FORCE_REPORT_NAME_STRICT = os.getenv("PLANNER_FORCE_REPORT_NAME_STRICT", "0") == "1"
MAX_WRITES = int(os.getenv("PLANNER_MAX_WRITES", "2"))

# New extended flags
RESPECT_CUSTOM = os.getenv("PLANNER_RESPECT_CUSTOM_FILENAME", "1") == "1"
ALLOW_MULTI_FILES = os.getenv("PLANNER_ALLOW_MULTI_FILES", "1") == "1"
MIN_ARCH_SIGNAL = os.getenv("PLANNER_MIN_ARCH_SIGNAL", "1") == "1"
FILENAME_AUTO_APPEND_EXT = os.getenv("PLANNER_FILENAME_AUTO_APPEND_EXT", "1") == "1"
FILENAME_REQUIRE_EXT = os.getenv("PLANNER_FILENAME_REQUIRE_EXT", "1") == "1"
FILE_SECONDARY_EXT = os.getenv("PLANNER_FILE_SECONDARY_EXT", ".md")
MAX_CUSTOM_FILES = int(os.getenv("PLANNER_MAX_CUSTOM_FILES", "3"))

# Level 4 Specific
L4_ENABLED = os.getenv("PLANNER_L4_ENABLED", "1") == "1"
L4_SCAN_DIRS = [d.strip() for d in os.getenv("PLANNER_L4_SCAN_DIRS", "app,.").split(",") if d.strip()]
L4_MAX_LIST_DIRS = int(os.getenv("PLANNER_L4_MAX_LIST_DIRS", "4"))
L4_CORE_FILES = [f.strip() for f in os.getenv(
    "PLANNER_L4_CORE_FILES",
    "README.md,requirements.txt,docker-compose.yml,config.py,Dockerfile"
).split(",") if f.strip()]
L4_INCLUDE_CODE_EXTS = [e.strip().lower() for e in os.getenv(
    "PLANNER_L4_INCLUDE_CODE_EXTS",
    ".py,.md,.yml,.yaml,.toml,.json,.txt,.ini,.cfg"
).split(",") if e.strip()]
L4_MAX_CODE_FILES = int(os.getenv("PLANNER_L4_MAX_CODE_FILES", "12"))
L4_MAX_TOTAL_READS = int(os.getenv("PLANNER_L4_MAX_TOTAL_READS", "24"))
L4_MULTI_ANALYSIS = os.getenv("PLANNER_L4_MULTI_ANALYSIS", "1") == "1"
L4_ENABLE_ENSURE = os.getenv("PLANNER_L4_ENABLE_ENSURE", "1") == "1"
L4_FINAL_FILENAME_HINT = os.getenv("PLANNER_L4_FINAL_FILENAME_HINT", "ARCHITECTURE_PRINCIPLES.md").strip()
L4_MIN_SYNTH_SECTIONS = int(os.getenv("PLANNER_L4_MIN_SYNTH_SECTIONS", "6"))
L4_PRIORITY_KEYWORDS = [k.strip().lower() for k in os.getenv(
    "PLANNER_L4_PRIORITY_KEYWORDS",
    "service,api,model,config,core,main,router,controller"
).split(",") if k.strip()]

# Regex / Aliases
TOOL_ID_REGEX = re.compile(r"^tool:\d{1,5}$")
# Pattern to capture single or multiple explicit filenames
# Examples matched:
#   file named my_doc.md
#   file named my-doc
#   files named a.md and b.md
#   files named a.md, b.md and c.md
#   create file my_doc.md
FILENAME_BLOCK_REGEX = re.compile(
    r'\bfiles?\s+named\s+([A-Za-z0-9_.\-\s,]+)|\bcreate\s+file\s+([A-Za-z0-9_.\-]+)|\bfile\s+named\s+([A-Za-z0-9_.\-]+)',
    re.IGNORECASE
)

CANON_WRITE = "write_file"
CANON_READ = "read_file"
CANON_THINK = "generic_think"
TOOL_ENSURE = "ensure_file"
CANON_LIST = "list_dir"

WRITE_INTENT = {"write", "create", "generate", "append", "produce", "save", "output", "file"}
READ_INTENT = {"read", "inspect", "load", "open", "view"}
THINK_INTENT = {"analyze", "analysis", "think", "reason", "summarize", "synthesize"}

MANDATORY_ARGS = {
    CANON_WRITE: ["path", "content"],
    CANON_READ: ["path"],
    TOOL_ENSURE: ["path"]
}

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def _clip(s: str, n: int = 140) -> str:
    if not s:
        return ""
    return s if len(s) <= n else s[: n - 3] + "..."

def _lower(x: Any) -> str:
    return str(x or "").strip().lower()

def _objective_has_arabic(obj: str) -> bool:
    if "arabic" in obj.lower():
        return True
    return any('\u0600' <= ch <= '\u06FF' for ch in obj)

def _looks_like_write(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in WRITE_INTENT)

def _looks_like_read(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in READ_INTENT)

def _looks_like_think(desc: str) -> bool:
    d = desc.lower()
    return any(k in d for k in THINK_INTENT)

def _canonical_task_id(idx: int) -> str:
    return f"t{idx:02d}"

def _risk_score(tool: str, desc: str, args: Dict[str, Any], deps: List[str]) -> float:
    score = 0.0
    if tool == CANON_WRITE:
        score += 2.5
        if isinstance(args.get("content"), str):
            score += min(len(args["content"]) / 1000.0, 3.5)
    if tool == TOOL_ENSURE:
        score += 1.0
    if tool == CANON_READ:
        score += 0.8
    if tool == CANON_THINK:
        score += 1.2
    score += len(deps) * 0.3
    return round(min(score, 10.0), 2)

def _normalize_whitespace(obj: str) -> str:
    return " ".join(obj.split())

def _extract_explicit_filenames(objective: str) -> List[str]:
    """
    Extract one or multiple requested filenames.
    Priority:
      - 'files named a.md and b.md'
      - 'file named x'
      - 'create file y'
    Returns distinct up to MAX_CUSTOM_FILES.
    """
    out: List[str] = []
    norm = _normalize_whitespace(objective)
    for match in FILENAME_BLOCK_REGEX.finditer(norm):
        group_multi, group_create, group_single = match.groups()
        raw_block = group_multi or group_create or group_single
        if not raw_block:
            continue
        # Split by common delimiters
        candidates = re.split(r'\band\b|,', raw_block, flags=re.IGNORECASE)
        for c in candidates:
            c = c.strip()
            if not c:
                continue
            # Enforce extension if required
            if FILENAME_REQUIRE_EXT and FILENAME_AUTO_APPEND_EXT:
                if "." not in c:
                    c += FILE_SECONDARY_EXT
            elif FILENAME_REQUIRE_EXT and "." not in c:
                # Skip invalid if extension mandatory
                continue
            if c.lower() not in [fn.lower() for fn in out]:
                out.append(c)
            if len(out) >= MAX_CUSTOM_FILES:
                break
        if len(out) >= MAX_CUSTOM_FILES:
            break
    return out

def _extract_target_filename(objective: str) -> Optional[str]:
    """Legacy single-target extractor with fallback to first explicit file."""
    explicit = _extract_explicit_filenames(objective)
    if explicit:
        return explicit[0]
    low = objective.lower()
    for token in ("architecture_principles.md", "summary_report.md", "architecture.md"):
        if token in low:
            return token
    return None

def _autofill_file_args(tool_name: str, tool_args: Dict[str, Any], task_index: int, notes: List[str]):
    if tool_name not in MANDATORY_ARGS:
        return
    req = MANDATORY_ARGS[tool_name]
    changed = False
    if "path" in req and not tool_args.get("path"):
        filename = f"auto_generated_{task_index:02d}{FILE_DEFAULT_EXT}"
        tool_args["path"] = filename
        notes.append(f"autofill_path:{filename}")
        changed = True
    if "content" in req and tool_name == CANON_WRITE:
        if not isinstance(tool_args.get("content"), str) or not tool_args["content"].strip():
            tool_args["content"] = FILE_DEFAULT_CONTENT
            notes.append("autofill_content:default")
            changed = True
    if changed:
        notes.append("mandatory_args_filled")

def _canonicalize_tool_local(raw: str, description: str) -> Tuple[str, List[str]]:
    name = _lower(raw)
    notes: List[str] = []
    if TOOL_ID_REGEX.match(name):
        notes.append("tool_id_unmapped")
        return name, notes
    if name in {"file_writer", "writer", "create_file"} or _looks_like_write(description) or "write" in name:
        notes.append("intent_write")
        return CANON_WRITE, notes
    if name in {"file_reader", "reader"} or _looks_like_read(description) or "read" in name:
        notes.append("intent_read")
        return CANON_READ, notes
    if _looks_like_think(description) or any(k in name for k in ("think", "analy", "reason")):
        notes.append("intent_think")
        return CANON_THINK, notes
    if name == "ensure_file":
        notes.append("ensure_pass")
        return TOOL_ENSURE, notes
    return raw, notes

def _canonicalize_tool(raw: str, description: str) -> Tuple[str, List[str]]:
    if CANON_FUNC:
        try:
            c, notes = CANON_FUNC(raw, description)  # type: ignore
            return c, notes
        except Exception:
            return _canonicalize_tool_local(raw, description)
    return _canonicalize_tool_local(raw, description)

# --------------------------------------------------------------------------------------
# Pattern Engine (Deterministic Level 4)
# --------------------------------------------------------------------------------------
class PatternResult:
    def __init__(self, tasks: List[PlannedTask], notes: List[str], meta: Optional[Dict[str, Any]] = None):
        self.tasks = tasks
        self.notes = notes
        self.meta = meta or {}

class PatternEngine:
    def __init__(self, objective: str, max_tasks: int):
        self.objective = objective
        self.low = objective.lower()
        self.max_tasks = max_tasks
        self.requested_files = _extract_explicit_filenames(objective)

    def detect(self) -> Optional[PatternResult]:
        if not L4_ENABLED:
            return None

        # Architecture signal gating
        arch_tokens = ("architecture", "architectural", "principles", "system architecture")
        arch_present = any(tok in self.low for tok in arch_tokens)

        # Require explicit architecture if MIN_ARCH_SIGNAL; else fallback to old broad check
        if MIN_ARCH_SIGNAL and not arch_present:
            return None

        report_signal = any(tok in self.low for tok in ("summary", "report", "file", "principles"))
        if not report_signal:
            return None

        # If user gave custom filenames and we must respect → we still can use pattern
        # but we won't override their names. (Previously we might have disabled pattern.)
        return self._architecture_deep_scan()

    # -----------------------------
    # Level-4 Architecture Deep Scan
    # -----------------------------
    def _architecture_deep_scan(self) -> PatternResult:
        notes: List[str] = ["pattern:l4_architecture_deep_scan"]
        meta: Dict[str, Any] = {}

        want_ar = _objective_has_arabic(self.objective)

        # Determine target file(s)
        explicit_files = self.requested_files
        meta["explicit_files_detected"] = explicit_files
        # Primary target (for synthesis)
        if explicit_files and RESPECT_CUSTOM:
            target_primary = explicit_files[0]
            filename_strategy = "explicit_user"
        else:
            if FORCE_REPORT_NAME and (FORCE_REPORT_NAME_STRICT or not RESPECT_CUSTOM or not explicit_files):
                target_primary = FORCE_REPORT_NAME
                filename_strategy = "forced_env"
            else:
                extracted = _extract_target_filename(self.objective)
                if extracted and RESPECT_CUSTOM:
                    target_primary = extracted
                    filename_strategy = "extracted_phrase"
                else:
                    target_primary = L4_FINAL_FILENAME_HINT
                    filename_strategy = "fallback_hint"

        if FILENAME_AUTO_APPEND_EXT and not target_primary.lower().endswith(FILE_DEFAULT_EXT):
            target_primary += FILE_DEFAULT_EXT if target_primary.find(".") < 0 else ""

        meta["target_primary"] = target_primary
        meta["filename_strategy"] = filename_strategy

        tasks: List[PlannedTask] = []
        idx = 1

        # 1) list_dir tasks
        list_roots = L4_SCAN_DIRS[:L4_MAX_LIST_DIRS]
        list_ids: List[str] = []
        for root in list_roots:
            tid = _canonical_task_id(idx); idx += 1
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description=f"List directory '{root}' to discover candidate files.",
                    tool_name=CANON_LIST,
                    tool_args={"path": root, "max_entries": 400},
                    dependencies=[]
                )
            )
            list_ids.append(tid)
            if idx > self.max_tasks:
                notes.append("cap_hit_after_list_dir")
                return PatternResult(tasks, notes, meta)

        # 2) Core file reads
        read_ids: List[str] = []
        for cf in L4_CORE_FILES:
            if len(read_ids) >= L4_MAX_TOTAL_READS:
                break
            tid = _canonical_task_id(idx); idx += 1
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description=f"Read core file {cf} if it exists.",
                    tool_name=CANON_READ,
                    tool_args={"path": cf, "ignore_missing": True, "max_bytes": 30000},
                    dependencies=[]
                )
            )
            read_ids.append(tid)
            if idx > self.max_tasks:
                notes.append("cap_hit_after_core_reads")
                return PatternResult(tasks, notes, meta)

        # 3) Heuristic code sample
        heuristic_candidates = [
            "app/__init__.py",
            "app/config.py",
            "app/routes.py",
            "app/services/agent_tools.py",
            "app/services/master_agent_service.py",
            "app/overmind/planning/llm_planner.py",
            "app/models.py",
            "migrations/env.py",
        ]
        filtered = []
        for c in heuristic_candidates:
            ext = "." + c.split(".")[-1].lower() if "." in c else ""
            if not ext or ext in L4_INCLUDE_CODE_EXTS:
                filtered.append(c)

        for c in filtered:
            if len(read_ids) >= L4_MAX_TOTAL_READS or (len(read_ids) - len(L4_CORE_FILES)) >= L4_MAX_CODE_FILES:
                break
            tid = _canonical_task_id(idx); idx += 1
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description=f"Read sample code file {c} (ignore if missing).",
                    tool_name=CANON_READ,
                    tool_args={"path": c, "ignore_missing": True, "max_bytes": 24000},
                    dependencies=[]
                )
            )
            read_ids.append(tid)
            if idx > self.max_tasks:
                notes.append("cap_hit_after_code_reads")
                return PatternResult(tasks, notes, meta)

        # 4) Analytical phases
        analysis_ids: List[str] = []
        if L4_MULTI_ANALYSIS:
            analyses_spec = [
                ("Identify major components, layers and their responsibilities.",
                 "components_and_layers"),
                ("Map data flow, persistence stores, and external integrations (APIs, DB, services).",
                 "data_flow"),
                ("Extract key dependencies (internal modules + external libraries) and coupling hotspots.",
                 "dependencies"),
                ("Assess risks, technical debt, scalability constraints, and security considerations.",
                 "risks"),
                ("List improvement opportunities and modernization recommendations.",
                 "recommendations")
            ]
            for text, tag in analyses_spec:
                tid = _canonical_task_id(idx); idx += 1
                prompt = self._build_analysis_prompt(text, read_ids, want_ar)
                tasks.append(
                    PlannedTask(
                        task_id=tid,
                        description=f"Analytical step: {tag}",
                        tool_name=CANON_THINK,
                        tool_args={"prompt": prompt},
                        dependencies=read_ids
                    )
                )
                analysis_ids.append(tid)
                if idx > self.max_tasks:
                    notes.append("cap_hit_during_analyses")
                    return PatternResult(tasks, notes, meta)
        else:
            tid = _canonical_task_id(idx); idx += 1
            prompt = self._build_analysis_prompt(
                "Perform holistic architecture analysis (components, data flow, dependencies, risks, improvements).",
                read_ids,
                want_ar
            )
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description="Holistic architecture analysis.",
                    tool_name=CANON_THINK,
                    tool_args={"prompt": prompt},
                    dependencies=read_ids
                )
            )
            analysis_ids.append(tid)

        # 5) Synthesis
        synth_id = _canonical_task_id(idx); idx += 1
        synth_prompt = self._build_synthesis_prompt(analysis_ids, read_ids, target_primary, want_ar)
        tasks.append(
            PlannedTask(
                task_id=synth_id,
                description="Synthesize final architecture report.",
                tool_name=CANON_THINK,
                tool_args={"prompt": synth_prompt},
                dependencies=analysis_ids
            )
        )

        ensure_id: Optional[str] = None
        if L4_ENABLE_ENSURE and "ensure_file" in ALLOWED_TOOLS:
            ensure_id = _canonical_task_id(idx); idx += 1
            tasks.append(
                PlannedTask(
                    task_id=ensure_id,
                    description=f"Ensure target output file {target_primary} exists or create placeholder.",
                    tool_name=TOOL_ENSURE,
                    tool_args={
                        "path": target_primary,
                        "initial_content": "Initializing architecture/report placeholder...",
                        "enforce_ext": ".md"
                    },
                    dependencies=[]
                )
            )

        # 6) Main write for primary target
        write_primary_id = _canonical_task_id(idx); idx += 1
        tasks.append(
            PlannedTask(
                task_id=write_primary_id,
                description=f"Write final primary report to {target_primary}.",
                tool_name=CANON_WRITE,
                tool_args={
                    "path": target_primary,
                    "content": f"{{{{{synth_id}.answer}}}}"
                },
                dependencies=[synth_id] if ensure_id is None else [synth_id]
            )
        )

        # 7) Additional explicit files (multi-artifact) if requested
        if ALLOW_MULTI_FILES and RESPECT_CUSTOM and len(explicit_files) > 1:
            # Skip the first (already handled)
            for extra_name in explicit_files[1:MAX_CUSTOM_FILES]:
                if FILENAME_AUTO_APPEND_EXT and "." not in extra_name:
                    extra_name += FILE_DEFAULT_EXT
                # Add a derivative write (could copy or transform)
                wid = _canonical_task_id(idx); idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=wid,
                        description=f"Mirror synthesized architecture insights into {extra_name}.",
                        tool_name=CANON_WRITE,
                        tool_args={
                            "path": extra_name,
                            "content": f"# {extra_name}\n\n{{{{{synth_id}.answer}}}}\n"
                                        "> (Derived copy of primary synthesis; consider tailoring manually.)"
                        },
                        dependencies=[synth_id]
                    )
                )

        # Risk scoring
        for t in tasks:
            if isinstance(t.tool_args, dict):
                t.tool_args["_meta_risk"] = _risk_score(t.tool_name, t.description, t.tool_args, t.dependencies)

        meta["primary_target"] = target_primary
        meta["multi_artifact"] = len(explicit_files) > 1
        meta["explicit_count"] = len(explicit_files)
        meta["respected_user_filenames"] = bool(explicit_files and RESPECT_CUSTOM)
        meta["pattern"] = "l4_architecture_deep_scan"

        return PatternResult(tasks=tasks, notes=notes, meta=meta)

    # -------- Helper prompts
    def _build_analysis_prompt(self, focus: str, read_ids: List[str], want_ar: bool) -> str:
        ref_lines = "\n".join(f"{{{{{tid}.content}}}}" for tid in read_ids)
        if want_ar:
            return (
                f"حلّل المحور: {focus}\n"
                "استخدم المقتطفات (قد تكون بعض الملفات ناقصة):\n"
                f"{ref_lines}\n"
                "أجب بنقاط منظمة موجزة بدون حشو.\n"
            )
        return (
            f"Analyze focus area: {focus}\n"
            "Use collected file excerpts (some may be empty/missing):\n"
            f"{ref_lines}\n"
            "Respond in structured concise bullet points.\n"
        )

    def _build_synthesis_prompt(self, analysis_ids: List[str], read_ids: List[str],
                                target_file: str, want_ar: bool) -> str:
        analysis_refs = "\n".join(f"<<<ANALYSIS:{aid}>>>\n{{{{{aid}.answer}}}}" for aid in analysis_ids)
        raw_refs = "\n".join(f"{{{{{rid}.content}}}}" for rid in read_ids[:6])
        sec_count = L4_MIN_SYNTH_SECTIONS
        if want_ar:
            return (
                "اكتب تقريراً معمارياً نهائياً احترافياً بالمواصفات:\n"
                f"- الملف الهدف: {target_file}\n"
                f"- أقسام ≥ {sec_count}: مقدمة، نظرة عامة، المكونات والخدمات، تدفق البيانات، الاعتمادات، الأداء والتوسع، المخاطر والأمن، التحسينات، خاتمة.\n"
                "- أوضح الافتراضات عند غياب معلومات.\n"
                "- استخدم لغة واضحة موجزة.\n"
                f"\n[تحليلات]\n{analysis_refs}\n"
                f"\n[مقتطفات]\n{raw_refs}\n"
            )
        return (
            "Produce a PROFESSIONAL ARCHITECTURE REPORT:\n"
            f"- Target file: {target_file}\n"
            f"- ≥ {sec_count} sections: Intro, Layers Overview, Components & Services, Data Flow & Persistence, "
            "Dependencies, Scalability & Performance, Risks & Security, Recommended Improvements, Conclusion.\n"
            "- Explicitly state assumptions when info missing.\n"
            "- Concise, structured, no fluff.\n"
            f"\n[Analyses]\n{analysis_refs}\n"
            f"\n[Raw Excerpts Subset]\n{raw_refs}\n"
        )

# --------------------------------------------------------------------------------------
# Planner Class
# --------------------------------------------------------------------------------------
class LLMGroundedPlanner(BasePlanner):
    name = "llm_grounded_planner_l4"
    version = "4.3.0-l4-custom"
    tier = "core"
    production_ready = True
    capabilities = {"planning", "llm", "tool-grounding", "hybrid", "deep-scan"}
    tags = {"mission", "tasks", "level4", "custom-filename"}

    @classmethod
    def self_test(cls) -> Tuple[bool, str]:
        return True, "l4_enabled" if L4_ENABLED else "l4_disabled"

    # Public API
    def generate_plan(
        self,
        objective: str,
        context: Optional[PlanningContext] = None,
        max_tasks: Optional[int] = None
    ) -> MissionPlanSchema:
        start = time.perf_counter()
        if not self._objective_valid(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        cap = min(max_tasks or MAX_TASKS_GLOBAL, MAX_TASKS_GLOBAL)
        _LOG.info("[%s] plan_start objective='%s' cap=%d",
                  self.name, _clip(objective, 140), cap)

        explicit_files = _extract_explicit_filenames(objective)
        _LOG.debug("[%s] explicit_files=%s respect=%s", self.name, explicit_files, RESPECT_CUSTOM)

        # 1. Pattern engine
        pattern = PatternEngine(objective, cap).detect()
        if pattern:
            _LOG.info("[%s] pattern_match notes=%s", self.name, pattern.notes)
            tasks = self._finalize_pattern_tasks(pattern.tasks, objective, explicit_files, pattern.meta)
            plan = MissionPlanSchema(objective=objective, tasks=tasks)
            self._post_validate(plan, explicit_files)
            self._log_success(plan, start, degraded=False, notes=pattern.notes)
            return plan

        # 2. Structured LLM path (only if maestro present)
        structured_plan = None
        errors: List[str] = []
        if maestro and hasattr(maestro, "generation_service"):
            try:
                structured_plan = self._call_structured(objective, context, cap)
            except Exception as e:
                errors.append(f"struct_fail:{type(e).__name__}")
                _LOG.warning("[%s] structured_failed %s", self.name, e)
        else:
            errors.append("maestro_unavailable")

        if STRICT_JSON_ONLY and structured_plan is None and not FALLBACK_ALLOW:
            _LOG.warning("[%s] strict_json_only->analytic_fallback", self.name)
            fallback_tasks = self._analytic_minimal(objective, explicit_files)
            plan = MissionPlanSchema(objective=objective, tasks=fallback_tasks)
            self._post_validate(plan, explicit_files)
            self._log_success(plan, start, degraded=True, notes=errors+["analytic_min"])
            return plan

        if structured_plan:
            norm_errs: List[str] = []
            try:
                tasks = self._normalize_tasks(structured_plan.get("tasks"), cap, norm_errs, objective, explicit_files)
            except Exception as e:
                errors.append(f"normalize_fail:{type(e).__name__}")
                tasks = self._analytic_minimal(objective, explicit_files)
                degraded = True
            else:
                tasks = self._post_process_normalized(tasks, objective, explicit_files)
                degraded = False
            plan = MissionPlanSchema(objective=objective, tasks=tasks)
            self._post_validate(plan, explicit_files)
            self._log_success(plan, start, degraded=degraded, notes=errors+norm_errs)
            return plan

        # 3. Final analytic fallback
        fallback = self._analytic_minimal(objective, explicit_files)
        plan = MissionPlanSchema(objective=objective, tasks=fallback)
        self._post_validate(plan, explicit_files)
        self._log_success(plan, start, degraded=True, notes=errors+["analytic_min_final"])
        return plan

    # ----------------------------------------------------------------------------------
    # Structured LLM path
    def _call_structured(self, objective: str, context: Optional[PlanningContext], max_tasks: int) -> Dict[str, Any]:
        if maestro is None or not hasattr(maestro, "generation_service"):
            raise RuntimeError("maestro_generation_service_unavailable")
        svc = maestro.generation_service  # type: ignore
        schema = {
            "type": "object",
            "properties": {
                "objective": {"type": "string"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "tool_name": {"type": "string"},
                            "tool_args": {"type": "object"},
                            "dependencies": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["description", "tool_name"],
                    },
                },
            },
            "required": ["tasks"],
        }
        prompt = self._render_structured_prompt(objective, context, max_tasks)
        resp = svc.structured_json(
            system_prompt=(
                "You are a strict mission planner. Output ONLY JSON. "
                "Respect explicit file naming (phrases like 'file named <X>'). "
                "Use only allowed tools."
            ),
            user_prompt=prompt,
            format_schema=schema,
            temperature=0.15,
            max_retries=1,
            fail_hard=False,
        )
        if not isinstance(resp, dict):
            raise PlannerError("structured_not_dict", self.name, objective)
        return resp

    def _render_structured_prompt(self, objective: str, context: Optional[PlanningContext], max_tasks: int) -> str:
        lines = [
            "OBJECTIVE:",
            objective,
            "",
            "ALLOWED_TOOLS:",
        ]
        for t in sorted(ALLOWED_TOOLS):
            lines.append(f"- {t}")
        lines += [
            "",
            "RULES:",
            "1. If objective contains 'file named X' produce final write_file with path X.",
            "2. Multiple files allowed if phrase 'files named' used (limit small).",
            "3. Provide concise task descriptions.",
            "4. Use dependencies only when needed.",
            f"Return <= {max_tasks} tasks."
        ]
        return "\n".join(lines)

    # ----------------------------------------------------------------------------------
    # Normalization (LLM path only)
    def _normalize_tasks(
        self,
        tasks_raw: Any,
        cap: int,
        errors_out: List[str],
        objective: str,
        explicit_files: List[str]
    ) -> List[PlannedTask]:
        if not isinstance(tasks_raw, list):
            raise PlanValidationError("tasks_not_list", self.name)

        cleaned: List[PlannedTask] = []
        for idx, raw in enumerate(tasks_raw):
            if len(cleaned) >= cap:
                errors_out.append("task_cap_reached")
                break
            if not isinstance(raw, dict):
                errors_out.append(f"task_{idx}_not_dict")
                continue
            desc = str(raw.get("description") or "").strip()
            if not desc:
                errors_out.append(f"task_{idx}_missing_desc")
                continue
            raw_tool = str(raw.get("tool_name") or "unknown").strip()
            tool_args = raw.get("tool_args")
            if not isinstance(tool_args, dict):
                tool_args = {}
                errors_out.append(f"task_{idx}_args_not_object")
            deps_raw = raw.get("dependencies") or []
            deps = [d for d in deps_raw if isinstance(d, str) and re.match(r"^t\d{2}$", d)]

            tool, cnotes = _canonicalize_tool(raw_tool, desc)

            if FORCE_FILE_TOOLS and tool not in ALLOWED_TOOLS:
                if _looks_like_write(desc):
                    tool = CANON_WRITE
                elif _looks_like_read(desc):
                    tool = CANON_READ
                elif _looks_like_think(desc):
                    tool = CANON_THINK

            if ENFORCE_ALLOWED and tool not in ALLOWED_TOOLS:
                tool = CANON_THINK

            if AUTO_FIX_FILE_TASKS:
                _autofill_file_args(tool, tool_args, idx + 1, cnotes)

            tid = _canonical_task_id(len(cleaned) + 1)
            tool_args["_meta_risk"] = _risk_score(tool, desc, tool_args, deps)
            cleaned.append(
                PlannedTask(
                    task_id=tid,
                    description=desc,
                    tool_name=tool,
                    tool_args=tool_args,
                    dependencies=deps
                )
            )

        if not cleaned:
            raise PlanValidationError("no_valid_tasks", self.name)

        return cleaned

    def _post_process_normalized(self, tasks: List[PlannedTask], objective: str, explicit_files: List[str]) -> List[PlannedTask]:
        # Consolidate writes (keep last meaningful)
        write_indices = [i for i, t in enumerate(tasks) if t.tool_name == CANON_WRITE]
        if write_indices:
            if len(write_indices) > 1:
                last_idx = write_indices[-1]
                pruned: List[PlannedTask] = []
                kept_writes = 0
                for i, t in enumerate(tasks):
                    if t.tool_name == CANON_WRITE and i != last_idx:
                        content_val = (t.tool_args or {}).get("content")
                        if isinstance(content_val, str) and content_val.strip() == FILE_DEFAULT_CONTENT.strip():
                            continue
                        if kept_writes >= (MAX_WRITES - 1):
                            continue
                        kept_writes += 1
                        pruned.append(t)
                    else:
                        pruned.append(t)
                tasks = pruned
            # Normalize final write filename
            final_write = next((t for t in reversed(tasks) if t.tool_name == CANON_WRITE), None)
            if final_write:
                if explicit_files and RESPECT_CUSTOM:
                    target = explicit_files[0]
                else:
                    target = FORCE_REPORT_NAME if (FORCE_REPORT_NAME and (FORCE_REPORT_NAME_STRICT or not explicit_files)) \
                        else (_extract_target_filename(objective) or L4_FINAL_FILENAME_HINT)
                if FILENAME_AUTO_APPEND_EXT and not target.lower().endswith(FILE_DEFAULT_EXT):
                    if "." not in target:
                        target += FILE_DEFAULT_EXT
                final_write.tool_args.setdefault("path", target)

                # Multi-artifact support (additional)
                if ALLOW_MULTI_FILES and RESPECT_CUSTOM and len(explicit_files) > 1:
                    base_synth_dep = [final_write.task_id]
                    for extra in explicit_files[1:MAX_CUSTOM_FILES]:
                        if FILENAME_AUTO_APPEND_EXT and "." not in extra:
                            extra += FILE_DEFAULT_EXT
                        t_id = _canonical_task_id(len(tasks) + 1)
                        tasks.append(
                            PlannedTask(
                                task_id=t_id,
                                description=f"Secondary artifact creation for {extra}.",
                                tool_name=CANON_WRITE,
                                tool_args={
                                    "path": extra,
                                    "content": f"# {extra}\n\n{{{{{final_write.task_id}.content}}}}"
                                },
                                dependencies=base_synth_dep
                            )
                        )
        return tasks

    # ----------------------------------------------------------------------------------
    # Pattern finalization
    def _finalize_pattern_tasks(
        self,
        tasks: List[PlannedTask],
        objective: str,
        explicit_files: List[str],
        pattern_meta: Dict[str, Any]
    ) -> List[PlannedTask]:
        """
        Ensure final write respects custom filenames if present; add multi-artifact clones if needed.
        """
        if len(tasks) > MAX_TASKS_GLOBAL:
            tasks = tasks[:MAX_TASKS_GLOBAL]

        if explicit_files and RESPECT_CUSTOM:
            # find the primary write_file (last one)
            primary = next((t for t in reversed(tasks) if t.tool_name == CANON_WRITE), None)
            if primary:
                requested = explicit_files[0]
                if FILENAME_AUTO_APPEND_EXT and "." not in requested:
                    requested += FILE_DEFAULT_EXT
                old = primary.tool_args.get("path")
                primary.tool_args["path"] = requested
                _LOG.info("[llm_planner] enforce_custom_filename pattern old=%s new=%s", old, requested)

            # Add extra files if multi
            if ALLOW_MULTI_FILES and len(explicit_files) > 1:
                synth_source = primary.task_id if primary else None
                for extra in explicit_files[1:MAX_CUSTOM_FILES]:
                    if FILENAME_AUTO_APPEND_EXT and "." not in extra:
                        extra += FILE_DEFAULT_EXT
                    new_id = _canonical_task_id(len(tasks) + 1)
                    tasks.append(
                        PlannedTask(
                            task_id=new_id,
                            description=f"Secondary artifact (clone) -> {extra}",
                            tool_name=CANON_WRITE,
                            tool_args={
                                "path": extra,
                                "content": f"# {extra}\n\n{{{{{primary.task_id}.content}}}}"
                            },
                            dependencies=[primary.task_id] if synth_source else []
                        )
                    )

        # Risk refresh (some new tasks maybe)
        for t in tasks:
            if isinstance(t.tool_args, dict) and "_meta_risk" not in t.tool_args:
                t.tool_args["_meta_risk"] = _risk_score(t.tool_name, t.description, t.tool_args, t.dependencies)

        return tasks

    # ----------------------------------------------------------------------------------
    # Minimal Analytical Fallback
    def _analytic_minimal(self, objective: str, explicit_files: List[str]) -> List[PlannedTask]:
        want_ar = _objective_has_arabic(objective)
        primary = explicit_files[0] if (explicit_files and RESPECT_CUSTOM) else (
            FORCE_REPORT_NAME if (FORCE_REPORT_NAME and (FORCE_REPORT_NAME_STRICT or not explicit_files))
            else (_extract_target_filename(objective) or L4_FINAL_FILENAME_HINT)
        )
        if FILENAME_AUTO_APPEND_EXT and "." not in primary:
            primary += FILE_DEFAULT_EXT
        lang_line = "اكتب ملخصاً منظماً موجزاً." if want_ar else "Write a concise structured summary."
        prompt = (
            f"{lang_line}\nObjective:\n{objective}\n"
            "Sections: Overview, Key Points, Recommendations. State assumptions if info missing."
        )
        tasks: List[PlannedTask] = [
            PlannedTask(
                task_id="t01",
                description="Analytical summary draft.",
                tool_name=CANON_THINK,
                tool_args={"prompt": prompt, "_meta_risk": 1.0},
                dependencies=[]
            ),
            PlannedTask(
                task_id="t02",
                description=f"Write final summary file {primary}.",
                tool_name=CANON_WRITE,
                tool_args={"path": primary, "content": "{{t01.answer}}", "_meta_risk": 2.0},
                dependencies=["t01"]
            )
        ]
        # Multi-artifact cloning if requested
        if ALLOW_MULTI_FILES and RESPECT_CUSTOM and len(explicit_files) > 1:
            for extra in explicit_files[1:MAX_CUSTOM_FILES]:
                if FILENAME_AUTO_APPEND_EXT and "." not in extra:
                    extra += FILE_DEFAULT_EXT
                tasks.append(
                    PlannedTask(
                        task_id=_canonical_task_id(len(tasks) + 1),
                        description=f"Secondary artifact {extra}",
                        tool_name=CANON_WRITE,
                        tool_args={"path": extra, "content": "{{t01.answer}}", "_meta_risk": 2.5},
                        dependencies=["t01"]
                    )
                )
        return tasks

    # ----------------------------------------------------------------------------------
    # Validation
    def _post_validate(self, plan: MissionPlanSchema, explicit_files: List[str]):
        if len(plan.tasks) > MAX_TASKS_GLOBAL:
            raise PlanValidationError("exceed_global_max_tasks", self.name)
        ids = {t.task_id for t in plan.tasks}
        for t in plan.tasks:
            for d in t.dependencies:
                if d not in ids:
                    raise PlanValidationError(f"dangling_dependency:{t.task_id}->{d}", self.name)

        # Explicit file enforcement
        if RESPECT_CUSTOM and explicit_files:
            missing = []
            lower_targets = [f.lower() for f in explicit_files]
            present = []
            for t in plan.tasks:
                if t.tool_name == CANON_WRITE:
                    path = (t.tool_args or {}).get("path")
                    if path and path.lower() in lower_targets:
                        present.append(path.lower())
            for req in lower_targets:
                if req not in present:
                    missing.append(req)
            if missing:
                raise PlanValidationError(f"missing_requested_files:{missing}", self.name)

        # Soft warning for implied file
        low = plan.objective.lower()
        if any(k in low for k in ("summary", "report", "file")) and not any(t.tool_name == CANON_WRITE for t in plan.tasks):
            _LOG.warning("[%s] validation: objective implies file but no write_file produced", self.name)

    # ----------------------------------------------------------------------------------
    # Logging
    def _log_success(self, plan: MissionPlanSchema, start: float, degraded: bool, notes: Optional[List[str]] = None):
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        _LOG.info("[%s] plan_success%s tasks=%d elapsed_ms=%.1f objective='%s'",
                  self.name,
                  "_degraded" if degraded else "",
                  len(plan.tasks),
                  elapsed_ms,
                  _clip(plan.objective, 100))
        if notes:
            _LOG.debug("[%s] notes_tail=%s", self.name, notes[-12:])

    # ----------------------------------------------------------------------------------
    def _objective_valid(self, objective: str) -> bool:
        if not objective:
            return False
        x = objective.strip()
        if len(x) < 5:
            return False
        if x.isdigit():
            return False
        return True


# --------------------------------------------------------------------------------------
# Exports
# --------------------------------------------------------------------------------------
__all__ = [
    "LLMGroundedPlanner",
    "MissionPlanSchema",
    "PlannedTask",
    "PlanningContext",
    "PlannerError",
    "PlanValidationError",
]

# --------------------------------------------------------------------------------------
# Dev Quick Test
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    planner = LLMGroundedPlanner()
    tests = [
        "Analyze the system architecture and create file named houssam-benemerah.md",
        "Analyze architecture and create files named alpha.md and beta.md",
        "Produce an architecture report (Arabic) analyzing components and data flow",
        "Simple objective summary",
        "Create file named custom_note (no extension) about risks",
        "Create files named a.md, b.md and c.md summarizing modules"
    ]
    for obj in tests:
        print("\n=== OBJECTIVE:", obj)
        try:
            plan = planner.generate_plan(obj)
            print(f"Produced {len(plan.tasks)} tasks:")
            for t in plan.tasks:
                path = (t.tool_args or {}).get("path") if t.tool_name == CANON_WRITE else ""
                print(f"  {t.task_id} | {t.tool_name} | deps={t.dependencies} | "
                      f"path={path} | risk={(t.tool_args or {}).get('_meta_risk')}")
        except Exception as e:
            print("ERROR:", e)