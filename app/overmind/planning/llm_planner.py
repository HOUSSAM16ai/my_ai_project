# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
# -*- coding: utf-8 -*-
"""
Ultra Hyper Semantic Planner + Deep Structural Index (v7.1.0-deep)
==================================================================
NEXT‑GEN L4++ PLANNING CORE
------------------------------------------------------------------
Features (Superset of 7.0.2-omni):
1. Multi‑language semantic objective parsing (Arabic / English).
2. Robust filename extraction (English + Arabic patterns) with smart normalization.
3. Multi‑file role derivation (optional JSON) + sections inference / refinement.
4. Chunked ultra‑large content synthesis (streaming via append_file) OR batch fallback.
5. Repository structural awareness:
   - Optional directory & core file scan.
   - Deep AST structural index integration (functions, classes, imports, hotspots, duplicates, dependencies)
     leveraged before content generation for higher‑fidelity artifacts.
6. Deterministic file initialization (ensure_file) + strict final write/append enforcement.
7. Artifact index & structural summary generation (Markdown + JSON) – configurable.
8. Extensive ENV gating for safe toggling & future experimentation.
9. Graceful degradation if indexing or scanning fails (no plan abort unless core invariants break).

Core Guarantees:
---------------
- Every target file requested (or inferred) gets at least one write/append action (STRICT_WRITE_ENFORCE).
- MissionPlanSchema meta enriched with structural telemetry (files_scanned, hotspot_count, duplicate_groups, index_version).
- No infinite task graphs (bounded & validated).
- Backward compatible with previous orchestrator & schema versions (PlanMeta supports extra keys).

ENV Flags (Key):
---------------
LANG / Files:
  PLANNER_FORCE_ARABIC=0|1
  PLANNER_LANGUAGE_FALLBACK=ar|en
  PLANNER_MAX_FILES=12
  PLANNER_DEFAULT_EXT=.md
  PLANNER_SMART_FILENAME=1
  PLANNER_ALLOW_SUBDIRS=1
  PLANNER_MAX_TASKS_GLOBAL=400

Chunk / Streaming:
  PLANNER_MAX_CHUNKS=50
  PLANNER_CHUNK_SIZE_HINT=1200
  PLANNER_HARD_LINE_CAP=1000000
  PLANNER_FAST_SINGLE_THRESHOLD=1800
  PLANNER_STREAMING_ENABLE=1
  PLANNER_ALLOW_APPEND_TOOL=auto|1|0
  PLANNER_APPEND_FALLBACK_BATCH=1

Higher-Level Inference:
  PLANNER_ENABLE_SECTION_INFERENCE=1
  PLANNER_ENABLE_ROLE_DERIVATION=1
  PLANNER_MULTI_ROLE_JSON=1
  PLANNER_ENABLE_CODE_HINTS=1
  PLANNER_ENSURE_FILE=1
  PLANNER_STRICT_WRITE_ENFORCE=1

Artifact Index (Light):
  PLANNER_INDEX_FILE=1
  PLANNER_INDEX_NAME=ARTIFACT_INDEX.md

Structural Deep Index (AST):
  PLANNER_DEEP_INDEX_ENABLE=1
  PLANNER_DEEP_INDEX_JSON=1
  PLANNER_DEEP_INDEX_JSON_NAME=STRUCTURAL_INDEX.json
  PLANNER_DEEP_INDEX_MD=1
  PLANNER_DEEP_INDEX_MD_NAME=STRUCTURAL_INDEX_SUMMARY.md
  PLANNER_DEEP_INDEX_MAX_JSON_BYTES=180000
  PLANNER_DEEP_INDEX_SUMMARY_MAX_LEN=3800

Read / Scan:
  PLANNER_ALLOW_LIST_READ_ANALYSIS=1
  PLANNER_CORE_READ_FILES=README.md,requirements.txt,Dockerfile,config.py,pyproject.toml

Logging:
  LLM_PLANNER_LOG_LEVEL=INFO|DEBUG|...

Meta Fields (PlanMeta):
  language, files, requested_lines, total_chunks, per_chunk, streaming, append_mode,
  role_task, section_task,
  files_scanned, hotspot_count, duplicate_groups, index_version,
  struct_index_attached, struct_index_json_task, struct_index_md_task

Flow Summary:
------------
  (Optional) Repo Scan → (Optional) Deep AST Index → Role Derivation → Section Refinement →
  Per-File Initialization → (Streamed or Batched) Chunk Generation → Wrap / Index Artifacts →
  (Optional) Structural JSON & Summary Artifacts → Final Plan

NOTE:
-----
  The structural index is generated at planning time and embedded directly into
  write_file tasks (no runtime tool call cost) unless disabled/fails.
"""

from __future__ import annotations

import os, re, math, time, logging, json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

# --------------------------------------------------------------------------------------
# Logging Setup
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("ultra_hyper_planner")
_lvl = os.getenv("LLM_PLANNER_LOG_LEVEL","").upper()
_LOG.setLevel(getattr(logging,_lvl, logging.INFO) if _lvl else logging.INFO)
if not _LOG.handlers:
    _h=logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# Base / Schema Imports (with optional stub fallback)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB","0")=="1"
try:
    from .base_planner import BasePlanner, PlannerError, PlanValidationError  # type: ignore
except Exception:
    if not _ALLOW_STUB:
        raise
    class PlannerError(Exception):
        def __init__(self, msg, planner="stub", objective="", **extra):
            super().__init__(msg); self.planner=planner; self.objective=objective; self.extra=extra
    class PlanValidationError(PlannerError): ...
    class BasePlanner: name="stub"

try:
    from .schemas import MissionPlanSchema, PlannedTask, PlanningContext  # type: ignore
except Exception:
    if not _ALLOW_STUB: raise
    @dataclass
    class PlannedTask:
        task_id: str
        description: str
        tool_name: str
        tool_args: Dict[str,Any]
        dependencies: List[str]
    @dataclass
    class MissionPlanSchema:
        objective: str
        tasks: List[PlannedTask]
        meta: Dict[str,Any] = None
    class PlanningContext: ...

# --------------------------------------------------------------------------------------
# Optional Deep Index Imports
# --------------------------------------------------------------------------------------
_DEEP_INDEX_ENABLED = os.getenv("PLANNER_DEEP_INDEX_ENABLE","1")=="1"
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
# ENV FLAGS
# --------------------------------------------------------------------------------------
FORCE_AR        = os.getenv("PLANNER_FORCE_ARABIC","0")=="1"
LANG_FALLBACK   = os.getenv("PLANNER_LANGUAGE_FALLBACK","ar").lower()
MAX_FILES       = int(os.getenv("PLANNER_MAX_FILES","12"))
DEFAULT_EXT     = os.getenv("PLANNER_DEFAULT_EXT",".md")
SMART_FN        = os.getenv("PLANNER_SMART_FILENAME","1")=="1"
ALLOW_SUBDIRS   = os.getenv("PLANNER_ALLOW_SUBDIRS","1")=="1"
GLOBAL_TASK_CAP = int(os.getenv("PLANNER_MAX_TASKS_GLOBAL","400"))

MAX_CHUNKS      = int(os.getenv("PLANNER_MAX_CHUNKS","50"))
CHUNK_SIZE_HINT = int(os.getenv("PLANNER_CHUNK_SIZE_HINT","1200"))
HARD_LINE_CAP   = int(os.getenv("PLANNER_HARD_LINE_CAP","1000000"))
FAST_SINGLE_THRESH = int(os.getenv("PLANNER_FAST_SINGLE_THRESHOLD","1800"))
STREAM_ENABLE   = os.getenv("PLANNER_STREAMING_ENABLE","1")=="1"
ALLOW_APPEND_MODE= os.getenv("PLANNER_ALLOW_APPEND_TOOL","auto")  # auto|1|0

SECTION_INFER   = os.getenv("PLANNER_ENABLE_SECTION_INFERENCE","1")=="1"
ROLE_DERIVATION = os.getenv("PLANNER_ENABLE_ROLE_DERIVATION","1")=="1"
ROLE_JSON       = os.getenv("PLANNER_MULTI_ROLE_JSON","1")=="1"
CODE_HINTS      = os.getenv("PLANNER_ENABLE_CODE_HINTS","1")=="1"
ENSURE_FILE     = os.getenv("PLANNER_ENSURE_FILE","1")=="1"
STRICT_WRITE_ENF= os.getenv("PLANNER_STRICT_WRITE_ENFORCE","1")=="1"

INDEX_FILE_EN   = os.getenv("PLANNER_INDEX_FILE","1")=="1"
INDEX_FILE_NAME = os.getenv("PLANNER_INDEX_NAME","ARTIFACT_INDEX.md")

DEEP_INDEX_JSON_EN  = os.getenv("PLANNER_DEEP_INDEX_JSON","1")=="1"
DEEP_INDEX_JSON_NAME= os.getenv("PLANNER_DEEP_INDEX_JSON_NAME","STRUCTURAL_INDEX.json")
DEEP_INDEX_MD_EN    = os.getenv("PLANNER_DEEP_INDEX_MD","1")=="1"
DEEP_INDEX_MD_NAME  = os.getenv("PLANNER_DEEP_INDEX_MD_NAME","STRUCTURAL_INDEX_SUMMARY.md")
DEEP_INDEX_MAX_JSON = int(os.getenv("PLANNER_DEEP_INDEX_MAX_JSON_BYTES","180000"))
DEEP_INDEX_SUMMARY_MAX = int(os.getenv("PLANNER_DEEP_INDEX_SUMMARY_MAX_LEN","3800"))

ALLOW_LIST_READ_ANALYSIS = os.getenv("PLANNER_ALLOW_LIST_READ_ANALYSIS","1")=="1"
CORE_READ_FILES = [f.strip() for f in os.getenv(
    "PLANNER_CORE_READ_FILES",
    "README.md,requirements.txt,Dockerfile,config.py,pyproject.toml"
).split(",") if f.strip()]

# --------------------------------------------------------------------------------------
# Tool Canonical Names
# --------------------------------------------------------------------------------------
TOOL_THINK  = "generic_think"
TOOL_WRITE  = "write_file"
TOOL_APPEND = "append_file"
TOOL_ENSURE = "ensure_file"
TOOL_READ   = "read_file"
TOOL_LIST   = "list_dir"

# --------------------------------------------------------------------------------------
# Regex & Patterns
# --------------------------------------------------------------------------------------
FILENAME_PATTERNS = [
    r'\bfile\s+named\s+([A-Za-z0-9_\-./]+)',
    r'\bfiles?\s+named\s+([A-Za-z0-9_\-./,\s]+)',
    r'\bsave\s+(?:it\s+)?as\s+([A-Za-z0-9_\-./]+)',
    r'\bwrite\s+(?:to|into)\s+([A-Za-z0-9_\-./]+)',
    r'\boutput\s+to\s+([A-Za-z0-9_\-./]+)',
    r'\bdeliver(?:able)?\s+([A-Za-z0-9_\-./]+)',
    r'ملف\s+باسم\s+([A-Za-z0-9_\-./]+)',
    r'ملفات\s+باسم\s+([A-Za-z0-9_\-./,\s]+)',
    r'احفظه\s+في\s+([A-Za-z0-9_\-./]+)',
    r'اكتب\s+في\s+([A-Za-z0-9_\-./]+)',
    r'الناتج\s+في\s+([A-Za-z0-9_\-./]+)',
    r'مخرجات\s+في\s+([A-Za-z0-9_\-./]+)'
]
SEP_SPLIT = re.compile(r'\s*(?:,|و|and)\s*', re.IGNORECASE)
LINE_REQ  = re.compile(r'(\d{2,9})\s*(?:lines?|أسطر|سطر)', re.IGNORECASE)
HUGE_TERMS= ["very large","huge","massive","enormous","gigantic","immense","ضخم","هائل","كبير جدا","مليونية","كثيرة جدا","مليونية"]

SECTION_HINTS_AR = ["مقدمة","نظرة عامة","تحليل","معمارية","تدفق البيانات","مكونات","تفاصيل","مخاطر","تحسينات","توصيات","خاتمة","ملاحق"]
SECTION_HINTS_EN = ["Introduction","Overview","Analysis","Architecture","Data Flow","Components","Details","Risks","Improvements","Recommendations","Conclusion","Appendices"]

CODE_EXTS = {".py",".js",".ts",".go",".java",".c",".cpp",".rb",".rs",".php",".sh",".ps1",".sql"}
DATA_EXTS = {".json",".yml",".yaml",".ini",".cfg",".toml",".csv",".xml"}
DOC_EXTS  = {".md",".rst",".txt",".log",".html",".adoc"}

# --------------------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------------------
def _has_arabic(s:str)->bool:
    return any('\u0600' <= c <= '\u06FF' for c in s)

def _detect_lang(obj:str)->str:
    if FORCE_AR: return "ar"
    low = obj.lower()
    if _has_arabic(obj) or "arabic" in low: return "ar"
    if "english" in low: return "en"
    return LANG_FALLBACK if LANG_FALLBACK in ("ar","en") else "ar"

def _normalize_filename(fn:str)->str:
    fn=fn.strip()
    if SMART_FN:
        fn=fn.replace("\\","/").replace("//","/")
        fn=re.sub(r'[^A-Za-z0-9_\-./]','_',fn)
    if not ALLOW_SUBDIRS and "/" in fn:
        fn=fn.split("/")[-1]
    return fn

def _ensure_ext(fn:str)->str:
    if "." not in fn:
        return fn + DEFAULT_EXT
    return fn

def extract_filenames(obj:str)->List[str]:
    norm=" ".join(obj.split())
    out=[]
    for pat in FILENAME_PATTERNS:
        for m in re.finditer(pat,norm,re.IGNORECASE):
            raw=m.group(1)
            if not raw: continue
            parts=SEP_SPLIT.split(raw)
            for p in parts:
                p=_normalize_filename(p)
                if not p: continue
                if "." not in p:
                    p=_ensure_ext(p)
                if p.lower() not in [x.lower() for x in out]:
                    out.append(p)
                if len(out)>=MAX_FILES: break
            if len(out)>=MAX_FILES: break
        if len(out)>=MAX_FILES: break
    if not out:
        guess=re.findall(r'\b([A-Za-z0-9_\-]+(?:\.[A-Za-z0-9_\-]+))\b', norm)
        for g in guess:
            g=_normalize_filename(g)
            if g.lower() not in [x.lower() for x in out]:
                out.append(g)
            if len(out)>=MAX_FILES: break
    if not out:
        out=["output"+DEFAULT_EXT]
    return out[:MAX_FILES]

def extract_requested_lines(obj:str)->Optional[int]:
    mx=None
    for m in LINE_REQ.finditer(obj):
        try:
            val=int(m.group(1))
            if mx is None or val>mx:
                mx=val
        except: pass
    if any(t in obj.lower() for t in HUGE_TERMS):
        if mx is None: mx=CHUNK_SIZE_HINT*10
        else: mx=int(mx*1.5)
    if mx and mx>HARD_LINE_CAP: mx=HARD_LINE_CAP
    return mx

def compute_chunk_plan(requested:Optional[int])->Tuple[int,int]:
    if not requested: requested=CHUNK_SIZE_HINT*2
    if requested <= FAST_SINGLE_THRESH:
        return 1, requested
    chunk_count=math.ceil(requested/CHUNK_SIZE_HINT)
    if chunk_count>MAX_CHUNKS: chunk_count=MAX_CHUNKS
    per_chunk=max(80, math.ceil(requested/chunk_count))
    return chunk_count, per_chunk

def infer_sections(obj:str, lang:str)->List[str]:
    if not SECTION_INFER: return []
    pat=re.compile(r'(?:sections?|أقسام|ضع\s+أقسام|include\s+sections?)\s*[:：]\s*(.+)', re.IGNORECASE)
    m=pat.search(obj)
    if m:
        tail=m.group(1)
        parts=re.split(r'[;,،]|(?:\band\b)|(?:\sو\s)', tail)
        cleaned=[p.strip(" .\t") for p in parts if p.strip()]
        return cleaned[:25]
    return (SECTION_HINTS_AR if lang=="ar" else SECTION_HINTS_EN)[:12]

def build_role_prompt(files:List[str], objective:str, lang:str)->str:
    listing=", ".join(files)
    if lang=="ar":
        return (f"الهدف:\n{objective}\nالملفات: {listing}\n"
                "خصص لكل ملف محوراً فريداً بلا تكرار. أعد JSON: "
                "[{filename, focus, outline_points, rationale}].")
    return (f"Objective:\n{objective}\nFiles: {listing}\nAssign each a distinct focus. JSON: "
            "[{filename, focus, outline_points, rationale}].")

def build_section_prompt(objective:str, draft_sections:List[str], lang:str)->str:
    listing="\n".join(f"- {s}" for s in draft_sections)
    if lang=="ar":
        return (f"الهدف:\n{objective}\nالأقسام المقترحة:\n{listing}\n"
                "حسّن وأعد JSON: [{order, section_title, notes}].")
    return (f"Objective:\n{objective}\nDraft Sections:\n{listing}\n"
            "Refine -> JSON [{order, section_title, notes}].")

def file_type(fn:str)->str:
    ext=os.path.splitext(fn)[1].lower()
    if ext in CODE_EXTS: return "code"
    if ext in DATA_EXTS: return "data"
    if ext in DOC_EXTS:  return "doc"
    return "generic"

def code_hint(ftype:str, lang:str)->str:
    if not CODE_HINTS: return ""
    if ftype=="code":
        return "أضف أمثلة كود واضحة وتعليقات.\n" if lang=="ar" else "Add clear code examples & commentary.\n"
    if ftype=="data":
        return "أضف أمثلة سجلات وشرح الحقول.\n" if lang=="ar" else "Provide sample records & field explanations.\n"
    return ""

def build_chunk_prompt(objective:str, fname:str, role_id:Optional[str], section_id:Optional[str],
                       cidx:int, ctotal:int, target_lines:int, lang:str, ftype:str)->str:
    role_ref=f"{{{{{role_id}.answer}}}}" if role_id else "(no-role)"
    section_ref=f"{{{{{section_id}.answer}}}}" if section_id else "(no-sections)"
    if lang=="ar":
        header=(f"الهدف:\n{objective}\nالملف:{fname}\nالمحور:{role_ref}\nالأقسام:{section_ref}\n"
                f"جزء {cidx}/{ctotal} (~{target_lines} سطر منطقي)\n")
        guide=("- لا تكرر المقدمة.\n- استمر منطقياً.\n- لا تختتم قبل الجزء الأخير.\n"
               "- أضف تفاصيل/قوائم/أمثلة.\n- تجنب الحشو.\n")
        return header+guide+code_hint(ftype,lang)
    header=(f"Objective:\n{objective}\nFile:{fname}\nFocus:{role_ref}\nSections:{section_ref}\n"
            f"Chunk {cidx}/{ctotal} (~{target_lines} lines)\n")
    guide=("- Do not fully repeat intro.\n- Maintain logical continuity.\n- No early finalization.\n"
           "- Add depth/lists/examples.\n- Avoid fluff.\n")
    return header+guide+code_hint(ftype,lang)

def build_final_wrap_prompt(objective:str, fname:str, role_id:Optional[str], lang:str)->str:
    role_ref=f"{{{{{role_id}.answer}}}}" if role_id else "(no-role)"
    if lang=="ar":
        return (f"الهدف:\n{objective}\nالملف:{fname}\n"
                f"قدّم خلاصة تنفيذية عربية مركّزة (<=200 سطر) مستفادة من {role_ref}.")
    return (f"Objective:\n{objective}\nFile:{fname}\n"
            f"Provide concise executive wrap-up (<=200 lines) leveraging {role_ref} insights.")

def _tid(i:int)->str: return f"t{i:02d}"

# --------------------------------------------------------------------------------------
# Planner Implementation
# --------------------------------------------------------------------------------------
class UltraHyperPlanner(BasePlanner):
    name = "ultra_hyper_semantic_planner"
    version = "7.1.0-deep"
    production_ready = True
    capabilities = {
        "semantic","chunked","multi-file","arabic","adaptive",
        "struct_index","architecture","telemetry"
    }
    tags = {"ultra","hyper","planner","index"}

    @classmethod
    def self_test(cls)->Tuple[bool,str]:
        return True, "ok"

    # --------------------------- Public Entry ---------------------------
    def generate_plan(self, objective:str, context:Optional[PlanningContext]=None,
                      max_tasks:Optional[int]=None)->MissionPlanSchema:
        start=time.perf_counter()
        if not self._valid_objective(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        lang=_detect_lang(objective)
        files=self._resolve_target_files(objective)
        req_lines=extract_requested_lines(objective)
        total_chunks, per_chunk = compute_chunk_plan(req_lines)
        streaming_possible = self._can_stream()
        use_stream = streaming_possible and os.getenv("PLANNER_STREAMING_ENABLE","1")=="1" and total_chunks>1

        tasks: List[PlannedTask]=[]
        idx=1
        analysis_dependency_ids=[]

        # ---------- Optional Repo Scan ----------
        if ALLOW_LIST_READ_ANALYSIS and self._wants_repo_scan(objective):
            idx = self._add_repo_scan_tasks(tasks, idx, analysis_dependency_ids)

        # ---------- Deep Structural Index (AST) ----------
        struct_meta, index_tasks_meta = self._attempt_deep_index(tasks, idx, analysis_dependency_ids, lang)
        idx = index_tasks_meta["next_idx"]
        struct_deps = index_tasks_meta["deps"]

        # ---------- Role Derivation ----------
        role_task_id=None
        if ROLE_DERIVATION and len(files)>1:
            role_task_id=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=role_task_id,
                description="Derive unique roles JSON for each target file (no overlap).",
                tool_name=TOOL_THINK,
                tool_args={"prompt": build_role_prompt(files, objective, lang)},
                dependencies=(struct_deps or analysis_dependency_ids)
            ))

        # ---------- Section Refinement ----------
        section_task_id=None
        inferred_sections=infer_sections(objective, lang)
        if inferred_sections:
            section_task_id=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=section_task_id,
                description="Refine / optimize suggested sections JSON.",
                tool_name=TOOL_THINK,
                tool_args={"prompt": build_section_prompt(objective, inferred_sections, lang)},
                dependencies=[role_task_id] if role_task_id else (struct_deps or analysis_dependency_ids)
            ))

        # ---------- File Generation ----------
        final_writes=[]
        idx = self._add_file_generation_blocks(
            tasks=tasks,
            idx=idx,
            files=files,
            objective=objective,
            lang=lang,
            role_task_id=role_task_id,
            section_task_id=section_task_id,
            analysis_deps=(struct_deps or analysis_dependency_ids),
            total_chunks=total_chunks,
            per_chunk=per_chunk,
            use_stream=use_stream,
            final_writes=final_writes
        )

        # ---------- Artifact Index (High-Level) ----------
        if INDEX_FILE_EN and len(files)>1:
            idx = self._add_artifact_index(tasks, idx, lang, final_writes, INDEX_FILE_NAME)

        # ---------- Structural Summary Artifacts (Optional) ----------
        if struct_meta["attached"]:
            idx = self._add_structural_summary_artifacts(
                tasks=tasks,
                idx=idx,
                lang=lang,
                deps=(struct_deps or analysis_dependency_ids),
                struct_meta=struct_meta,
                final_writes=final_writes
            )

        # ---------- Plan & Meta ----------
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
            # Structural Index Telemetry
            "files_scanned": struct_meta.get("files_scanned"),
            "hotspot_count": struct_meta.get("hotspot_count"),
            "duplicate_groups": struct_meta.get("duplicate_groups"),
            "index_version": struct_meta.get("index_version"),
            "struct_index_attached": struct_meta["attached"],
            "struct_index_json_task": struct_meta.get("json_task"),
            "struct_index_md_task": struct_meta.get("md_task")
        }

        plan=MissionPlanSchema(
            objective=objective,
            tasks=tasks,
            meta=meta
        )
        self._validate(plan, files)
        elapsed=(time.perf_counter()-start)*1000
        _LOG.info(
            "[UltraHyperPlanner v7.1.0-deep] tasks=%d files=%d streaming=%s struct_index=%s ms=%.1f",
            len(tasks), len(files), use_stream, struct_meta["attached"], elapsed
        )
        return plan

    # --------------------------- Internal: Repo Scan ---------------------------
    def _add_repo_scan_tasks(self, tasks:List[PlannedTask], idx:int, deps_accum:List[str]) -> int:
        for root in (".","app"):
            tid=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=tid,
                description=f"List directory '{root}' for structural awareness (ignore hidden?).",
                tool_name=TOOL_LIST,
                tool_args={"path": root, "max_entries": 500},
                dependencies=[]
            ))
            deps_accum.append(tid)
        for cf in CORE_READ_FILES[:12]:
            tid=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=tid,
                description=f"Read core file {cf} (ignore missing) for contextual grounding.",
                tool_name=TOOL_READ,
                tool_args={"path": cf, "ignore_missing": True, "max_bytes": 50000},
                dependencies=[]
            ))
            deps_accum.append(tid)
        return idx

    # --------------------------- Internal: Deep Index -------------------------
    def _attempt_deep_index(self, tasks:List[PlannedTask], idx:int,
                            base_deps:List[str], lang:str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Builds structural AST index at planning time (no tool invocation).
        Optionally emits write_file tasks for JSON & summary MD.
        """
        struct_meta = {
            "attached": False
        }
        deps_out: List[str] = []

        if not (_DEEP_INDEX_ENABLED and _HAS_INDEXER):
            return struct_meta, {"next_idx": idx, "deps": deps_out}

        try:
            # Build index (planning-time)
            index_data = build_index(".")
            struct_meta.update({
                "attached": True,
                "files_scanned": index_data.get("files_scanned"),
                "hotspot_count": len(index_data.get("complexity_hotspots_top50", [])),
                "duplicate_groups": len(index_data.get("duplicate_function_bodies", {})),
                "index_version": index_data.get("index_version","ast-deep-v1")
            })

            # JSON artifact task (if enabled)
            json_task_id=None
            if DEEP_INDEX_JSON_EN:
                truncated_json = self._truncate_json(index_data, DEEP_INDEX_MAX_JSON)
                json_task_id=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=json_task_id,
                    description="Write structural AST index JSON artifact.",
                    tool_name=TOOL_WRITE,
                    tool_args={
                        "path": DEEP_INDEX_JSON_NAME,
                        "content": truncated_json
                    },
                    dependencies=base_deps  # optional dependency on initial scans
                ))
                deps_out.append(json_task_id)
                struct_meta["json_task"]=json_task_id

            # Summary MD artifact (if enabled)
            md_task_id=None
            if DEEP_INDEX_MD_EN:
                summary_text = summarize_for_prompt(index_data, max_len=DEEP_INDEX_SUMMARY_MAX)
                # Wrap for readability:
                if lang=="ar":
                    header="## ملخص الفهرسة البنائية (AST)\n"
                else:
                    header="## Structural AST Index Summary\n"
                md_content = header + "\n```\n" + summary_text + "\n```\n"
                md_task_id=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=md_task_id,
                    description="Write structural index summary markdown.",
                    tool_name=TOOL_WRITE,
                    tool_args={
                        "path": DEEP_INDEX_MD_NAME,
                        "content": md_content
                    },
                    dependencies=base_deps
                ))
                deps_out.append(md_task_id)
                struct_meta["md_task"]=md_task_id

        except Exception as e:
            _LOG.warning("Deep index build failed (graceful continue): %s", e)

        return struct_meta, {"next_idx": idx, "deps": deps_out}

    def _truncate_json(self, data:Dict[str,Any], max_bytes:int)->str:
        raw=json.dumps(data, ensure_ascii=False, separators=(",",":"))
        if len(raw.encode("utf-8")) <= max_bytes:
            return raw
        # Basic shrink: remove 'modules' content details (heavy) keep summary
        slim = dict(data)
        if "modules" in slim:
            slim["modules"] = [{"path": m.get("path"), "fn_count": len(m.get("functions",[])), "class_count": len(m.get("classes",[]))} for m in slim["modules"][:200]]
        raw2=json.dumps(slim, ensure_ascii=False, separators=(",",":"))
        if len(raw2.encode("utf-8")) <= max_bytes:
            return raw2
        return raw2[:max_bytes-50]+"..."

    # ---------------------- Internal: File Generation Blocks ------------------
    def _add_file_generation_blocks(self, tasks:List[PlannedTask], idx:int, files:List[str],
                                    objective:str, lang:str,
                                    role_task_id:Optional[str], section_task_id:Optional[str],
                                    analysis_deps:List[str],
                                    total_chunks:int, per_chunk:int, use_stream:bool,
                                    final_writes:List[str]) -> int:
        for fname in files:
            base_deps=[]
            if role_task_id: base_deps.append(role_task_id)
            if section_task_id: base_deps.append(section_task_id)
            if analysis_deps and not base_deps:
                base_deps=analysis_deps

            ensure_id=None
            if ENSURE_FILE:
                ensure_id=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=ensure_id,
                    description=f"Ensure file {fname} exists (scaffold / banner).",
                    tool_name=TOOL_ENSURE,
                    tool_args={"path": fname, "initial_content": self._initial_banner(fname, objective, lang)},
                    dependencies=[]
                ))
                base_deps.append(ensure_id)

            ftype=file_type(fname)

            if use_stream and self._append_allowed() and total_chunks>1:
                prev=None
                for c in range(1,total_chunks+1):
                    think_id=_tid(idx); idx+=1
                    prompt=build_chunk_prompt(objective,fname,role_task_id,section_task_id,
                                              c,total_chunks,per_chunk,lang,ftype)
                    deps=base_deps.copy()
                    if prev: deps.append(prev)
                    tasks.append(PlannedTask(
                        task_id=think_id,
                        description=f"Generate streamed chunk {c}/{total_chunks} for {fname}.",
                        tool_name=TOOL_THINK,
                        tool_args={"prompt": prompt},
                        dependencies=deps
                    ))
                    append_id=_tid(idx); idx+=1
                    tasks.append(PlannedTask(
                        task_id=append_id,
                        description=f"Append streamed chunk {c} to {fname}.",
                        tool_name=TOOL_APPEND,
                        tool_args={"path": fname, "content": f"{{{{{think_id}.answer}}}}"},
                        dependencies=[think_id]
                    ))
                    prev=append_id
                wrap_think=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=wrap_think,
                    description=f"Generate final wrap (stream mode) for {fname}.",
                    tool_name=TOOL_THINK,
                    tool_args={"prompt": build_final_wrap_prompt(objective,fname,role_task_id,lang)},
                    dependencies=[prev] if prev else base_deps
                ))
                wrap_write=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=wrap_write,
                    description=f"Append final wrap to {fname}.",
                    tool_name=TOOL_APPEND,
                    tool_args={"path": fname, "content": f"\n\n{{{{{wrap_think}.answer}}}}"},
                    dependencies=[wrap_think]
                ))
                final_writes.append(wrap_write)
            else:
                # Batch mode
                chunk_thinks=[]
                for c in range(1,total_chunks+1):
                    think_id=_tid(idx); idx+=1
                    prompt=build_chunk_prompt(objective,fname,role_task_id,section_task_id,
                                              c,total_chunks,per_chunk,lang,ftype)
                    deps=base_deps.copy()
                    if chunk_thinks: deps.append(chunk_thinks[-1])
                    tasks.append(PlannedTask(
                        task_id=think_id,
                        description=f"Generate batch chunk {c}/{total_chunks} for {fname}.",
                        tool_name=TOOL_THINK,
                        tool_args={"prompt": prompt},
                        dependencies=deps
                    ))
                    chunk_thinks.append(think_id)
                wrap_think=None
                if total_chunks>1:
                    wrap_think=_tid(idx); idx+=1
                    tasks.append(PlannedTask(
                        task_id=wrap_think,
                        description=f"Generate final wrap (batch) for {fname}.",
                        tool_name=TOOL_THINK,
                        tool_args={"prompt": build_final_wrap_prompt(objective,fname,role_task_id,lang)},
                        dependencies=[chunk_thinks[-1]]
                    ))
                parts=[f"{{{{{cid}.answer}}}}" for cid in chunk_thinks]
                if wrap_think: parts.append(f"\n\n{{{{{wrap_think}.answer}}}}")
                final_content="\n\n".join(parts)
                write_id=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=write_id,
                    description=f"Write composed file {fname} (batch mode).",
                    tool_name=TOOL_WRITE,
                    tool_args={"path": fname, "content": final_content},
                    dependencies=[chunk_thinks[-1]] if chunk_thinks else base_deps
                ))
                final_writes.append(write_id)
        return idx

    # ---------------------- Internal: Artifact Index -------------------------
    def _add_artifact_index(self, tasks:List[PlannedTask], idx:int, lang:str,
                            deps:List[str], index_name:str)->int:
        idx_think=_tid(idx); idx+=1
        idx_prompt_ar="أنشئ فهرساً موجزاً لكل الملفات الناتجة (سطران لكل ملف: المحور المحتمل والاستخدام)."
        idx_prompt_en="Create a concise index of all generated artifacts (2 lines each: probable focus & usage)."
        tasks.append(PlannedTask(
            task_id=idx_think,
            description="Generate artifact index summary.",
            tool_name=TOOL_THINK,
            tool_args={"prompt": idx_prompt_ar if lang=='ar' else idx_prompt_en},
            dependencies=deps
        ))
        idx_write=_tid(idx); idx+=1
        tasks.append(PlannedTask(
            task_id=idx_write,
            description=f"Write artifact index {index_name}.",
            tool_name=TOOL_WRITE,
            tool_args={"path": index_name, "content": f"{{{{{idx_think}.answer}}}}"},
            dependencies=[idx_think]
        ))
        return idx

    # ------------------ Internal: Structural Summaries (MD) -------------------
    def _add_structural_summary_artifacts(self, tasks:List[PlannedTask], idx:int,
                                          lang:str, deps:List[str],
                                          struct_meta:Dict[str,Any],
                                          final_writes:List[str]) -> int:
        """
        Adds an optional THINK task that synthesizes a higher-level architecture
        & refactor insight summary using placeholders from previously written
        structural JSON / summary MD (if both exist).
        """
        summary_inputs=[]
        if struct_meta.get("json_task"):
            summary_inputs.append(f"{{{{{struct_meta['json_task']}.content}}}}")
        if struct_meta.get("md_task"):
            summary_inputs.append(f"{{{{{struct_meta['md_task']}.content}}}}")
        if not summary_inputs:
            return idx

        combined_ref = "\n\n".join(summary_inputs)
        prompt_ar = (
            "حلل البيانات الهيكلية التالية (JSON/ملخص) واستخرج تقريراً معمقاً:\n"
            "- طبقات (Layers) / تكتلات\n- نقاط تعقيد حرجة\n- تكرار وظيفي\n"
            "- فرص إعادة هيكلة مرتبة بالأولوية\n- مخاطر فنية مختصرة\n"
            "أخرج Markdown منظم بدون إسهاب."
        )
        prompt_en = (
            "Analyze the structural data (JSON / summaries) and produce an advanced report:\n"
            "- Layered decomposition / clusters\n- Critical complexity hotspots\n"
            "- Duplicate function logic\n- Ranked refactor opportunities\n"
            "- Concise technical risks\nReturn structured Markdown (succinct)."
        )
        think_id=_tid(idx); idx+=1
        tasks.append(PlannedTask(
            task_id=think_id,
            description="Synthesize advanced structural architecture & refactor insights.",
            tool_name=TOOL_THINK,
            tool_args={"prompt": (prompt_ar if lang=='ar' else prompt_en) + "\n\n" + combined_ref[:4000]},
            dependencies=deps
        ))
        write_id=_tid(idx); idx+=1
        out_name = "DEEP_ARCHITECTURE_REPORT.md"
        tasks.append(PlannedTask(
            task_id=write_id,
            description=f"Write deep architecture report {out_name}.",
            tool_name=TOOL_WRITE,
            tool_args={"path": out_name, "content": f"{{{{{think_id}.answer}}}}"},
            dependencies=[think_id]
        ))
        final_writes.append(write_id)
        return idx

    # --------------------------- Validation & Utilities -----------------------
    def _resolve_target_files(self, objective:str)->List[str]:
        raw=extract_filenames(objective)
        normalized=[]
        for f in raw:
            nf=_normalize_filename(f)
            if "." not in nf: nf=_ensure_ext(nf)
            if nf.lower() not in [x.lower() for x in normalized]:
                normalized.append(nf)
        return normalized[:MAX_FILES]

    def _can_stream(self)->bool:
        mode=ALLOW_APPEND_MODE
        if mode=="0": return False
        if mode=="1": return True
        # auto detection via optional whitelist
        allowed_env=os.getenv("PLANNER_ALLOWED_TOOLS","")
        if allowed_env:
            allowed={t.strip() for t in allowed_env.split(",") if t.strip()}
            return "append_file" in allowed
        return True  # optimistic

    def _append_allowed(self)->bool:
        return self._can_stream()

    def _wants_repo_scan(self, objective:str)->bool:
        low=objective.lower()
        return any(k in low for k in ("repository","repo","structure","architecture","معمار","هيكل","بنية","analyze project"))

    def _initial_banner(self, fname:str, objective:str, lang:str)->str:
        ext=fname.lower()
        truncated = objective[:180]
        if ext.endswith((".md",".txt",".log",".rst",".adoc",".html")):
            return (f"# تهيئة: {fname}\n\n> الهدف: {truncated}...\n\n") if lang=='ar' \
                   else (f"# Init: {fname}\n\n> Objective: {truncated}...\n\n")
        if any(ext.endswith(e) for e in CODE_EXTS):
            return f"# Auto-generated scaffold for: {objective[:120]}\n\n"
        if any(ext.endswith(e) for e in DATA_EXTS):
            return f"# Data artifact scaffold: {objective[:120]}\n"
        return ""

    def _validate(self, plan:MissionPlanSchema, files:List[str]):
        if len(plan.tasks)>GLOBAL_TASK_CAP:
            raise PlanValidationError("excessive_tasks", self.name, plan.objective)
        ids={t.task_id for t in plan.tasks}
        for t in plan.tasks:
            for d in t.dependencies:
                if d not in ids:
                    raise PlanValidationError(f"dangling_dependency:{t.task_id}->{d}", self.name, plan.objective)
        if STRICT_WRITE_ENF:
            for f in files:
                if not any(
                    (tt.tool_name in (TOOL_WRITE,TOOL_APPEND)) and (tt.tool_args or {}).get("path","").lower()==f.lower()
                    for tt in plan.tasks
                ):
                    raise PlanValidationError(f"missing_file_write:{f}", self.name, plan.objective)

    def _valid_objective(self, objective:str)->bool:
        if not objective or len(objective.strip())<5: return False
        if objective.strip().isdigit(): return False
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
    "PlanValidationError"
]

if __name__ == "__main__":
    p=UltraHyperPlanner()
    demo="Analyze repository structure and create file named repo-overview.md plus a deep architecture report"
    plan = p.generate_plan(demo)
    print("Meta:", json.dumps(plan.meta, ensure_ascii=False, indent=2))
    print("Tasks:", len(plan.tasks))