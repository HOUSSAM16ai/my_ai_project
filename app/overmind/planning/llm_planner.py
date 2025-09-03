# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
# -*- coding: utf-8 -*-
"""
Ultra Hyper Semantic Planner (v7.0.2-omni)
=========================================
قدرات:
- فهم دلالي متعدد اللغات (عربي/إنجليزي) للأوامر الحرة.
- استخراج أسماء ملفات بصيغ مختلفة (file named / احفظه في / save as / output to / deliverable ...).
- دعم عدة ملفات مع توزيع أدوار (Role Derivation JSON).
- توليد محتوى ضخم (حتى مليون سطر منطقي) عبر Chunk Streaming (append_file) أو Batch Fallback (write_file).
- استنتاج أقسام (Sections Inference) أو قبول أقسام من المستخدم.
- تحليل بنية المستودع الاختياري (list_dir + read_file) لو ذكرت structure/architecture/repository.
- حماية ضد فقد الملفات: ضمان write/append لكل ملف نهائي (STRICT_WRITE_ENFORCE).
- مرونة في التشغيل عبر ENV flags.

ENV الرئيسية:
-------------
PLANNER_FORCE_ARABIC=0|1
PLANNER_LANGUAGE_FALLBACK=ar|en
PLANNER_MAX_FILES=12
PLANNER_DEFAULT_EXT=.md
PLANNER_SMART_FILENAME=1
PLANNER_ALLOW_SUBDIRS=1
PLANNER_MAX_TASKS_GLOBAL=400

PLANNER_MAX_CHUNKS=50
PLANNER_CHUNK_SIZE_HINT=1200
PLANNER_HARD_LINE_CAP=1000000
PLANNER_FAST_SINGLE_THRESHOLD=1800
PLANNER_STREAMING_ENABLE=1
PLANNER_ALLOW_APPEND_TOOL=auto|1|0
PLANNER_APPEND_FALLBACK_BATCH=1

PLANNER_ENABLE_SECTION_INFERENCE=1
PLANNER_ENABLE_ROLE_DERIVATION=1
PLANNER_MULTI_ROLE_JSON=1
PLANNER_ENABLE_CODE_HINTS=1
PLANNER_ENSURE_FILE=1

PLANNER_INDEX_FILE=1
PLANNER_INDEX_NAME=ARTIFACT_INDEX.md
PLANNER_STRICT_WRITE_ENFORCE=1

PLANNER_ALLOW_LIST_READ_ANALYSIS=1
PLANNER_CORE_READ_FILES=README.md,requirements.txt,Dockerfile,config.py,pyproject.toml
"""

from __future__ import annotations
import os, re, math, time, logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("ultra_hyper_planner")
_lvl = os.getenv("LLM_PLANNER_LOG_LEVEL","").upper()
_LOG.setLevel(getattr(logging,_lvl, logging.INFO) if _lvl else logging.INFO)
if not _LOG.handlers:
    _h=logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# Base / Schemas Imports (Stub fallback)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB","0")=="1"
try:
    from .base_planner import BasePlanner, PlannerError, PlanValidationError  # type: ignore
except Exception:
    if not _ALLOW_STUB:
        raise
    class PlannerError(Exception):
        def __init__(self,msg,planner="stub",objective="",**extra):
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
APPEND_FALLBACK = os.getenv("PLANNER_APPEND_FALLBACK_BATCH","1")=="1"

SECTION_INFER   = os.getenv("PLANNER_ENABLE_SECTION_INFERENCE","1")=="1"
ROLE_DERIVATION = os.getenv("PLANNER_ENABLE_ROLE_DERIVATION","1")=="1"
ROLE_JSON       = os.getenv("PLANNER_MULTI_ROLE_JSON","1")=="1"
CODE_HINTS      = os.getenv("PLANNER_ENABLE_CODE_HINTS","1")=="1"
ENSURE_FILE     = os.getenv("PLANNER_ENSURE_FILE","1")=="1"

INDEX_FILE_EN   = os.getenv("PLANNER_INDEX_FILE","1")=="1"
INDEX_FILE_NAME = os.getenv("PLANNER_INDEX_NAME","ARTIFACT_INDEX.md")
STRICT_WRITE_ENF= os.getenv("PLANNER_STRICT_WRITE_ENFORCE","1")=="1"

ALLOW_LIST_READ_ANALYSIS = os.getenv("PLANNER_ALLOW_LIST_READ_ANALYSIS","1")=="1"
CORE_READ_FILES = [f.strip() for f in os.getenv(
    "PLANNER_CORE_READ_FILES",
    "README.md,requirements.txt,Dockerfile,config.py,pyproject.toml"
).split(",") if f.strip()]

# --------------------------------------------------------------------------------------
# Tools canonical names
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
# Helpers
# --------------------------------------------------------------------------------------
def _clip(s:str,n:int=140)->str: return s if len(s)<=n else s[:n-3]+"..."

def _has_arabic(s:str)->bool:
    return any('\u0600' <= c <= '\u06FF' for c in s)

def _detect_lang(obj:str)->str:
    if FORCE_AR: return "ar"
    if _has_arabic(obj) or "arabic" in obj.lower(): return "ar"
    if "english" in obj.lower(): return "en"
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
    base_ar= lang=="ar"
    header_ar=(f"الهدف:\n{objective}\nالملف:{fname}\nالمحور:{role_ref}\nالأقسام:{section_ref}\n"
               f"جزء {cidx}/{ctotal} (~{target_lines} سطر منطقي)\n")
    header_en=(f"Objective:\n{objective}\nFile:{fname}\nFocus:{role_ref}\nSections:{section_ref}\n"
               f"Chunk {cidx}/{ctotal} (~{target_lines} lines)\n")
    guide_ar=("- لا تكرر المقدمة.\n- استمر منطقياً.\n- لا تختتم قبل الجزء الأخير.\n"
              "- أضف تفاصيل/قوائم/أمثلة.\n- تجنب الحشو.\n")
    guide_en=("- Do not fully repeat intro.\n- Maintain logical continuity.\n- No early finalization.\n"
              "- Add depth/lists/examples.\n- Avoid fluff.\n")
    return (header_ar+guide_ar+code_hint(ftype,lang)) if base_ar else (header_en+guide_en+code_hint(ftype,lang))

def build_final_wrap_prompt(objective:str, fname:str, role_id:Optional[str], lang:str)->str:
    role_ref=f"{{{{{role_id}.answer}}}}" if role_id else "(no-role)"
    if lang=="ar":
        return (f"الهدف:\n{objective}\nالملف:{fname}\n"
                f"قدّم خلاصة تنفيذية عربية مركّزة (<=200 سطر) مستفادة من {role_ref}.")
    return (f"Objective:\n{objective}\nFile:{fname}\n"
            f"Provide concise executive wrap-up (<=200 lines) leveraging {role_ref} insights.")

def _tid(i:int)->str: return f"t{i:02d}"

# --------------------------------------------------------------------------------------
# Planner
# --------------------------------------------------------------------------------------
class UltraHyperPlanner(BasePlanner):
    name = "ultra_hyper_semantic_planner"
    version = "7.0.2-omni"
    production_ready = True
    capabilities = {"semantic","chunked","multi-file","arabic","adaptive"}
    tags = {"ultra","hyper","planner"}

    @classmethod
    def self_test(cls)->Tuple[bool,str]:
        return True, "ok"

    def generate_plan(self, objective:str, context:Optional[PlanningContext]=None,
                      max_tasks:Optional[int]=None)->MissionPlanSchema:
        start=time.perf_counter()
        if not self._valid_objective(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        lang=_detect_lang(objective)
        files=extract_filenames(objective)
        normalized=[]
        for f in files:
            nf=_normalize_filename(f)
            if "." not in nf: nf=_ensure_ext(nf)
            if nf.lower() not in [x.lower() for x in normalized]:
                normalized.append(nf)
        files=normalized[:MAX_FILES]

        req_lines=extract_requested_lines(objective)
        total_chunks, per_chunk = compute_chunk_plan(req_lines)
        streaming_possible = self._can_stream()
        use_stream = streaming_possible and STREAM_ENABLE and total_chunks>1

        tasks: List[PlannedTask]=[]
        idx=1
        analysis_dependency_ids=[]
        if ALLOW_LIST_READ_ANALYSIS and self._wants_repo_scan(objective):
            for root in (".","app"):
                tid=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=tid,
                    description=f"List directory '{root}' (structure scan).",
                    tool_name=TOOL_LIST,
                    tool_args={"path": root, "max_entries": 400},
                    dependencies=[]
                ))
                analysis_dependency_ids.append(tid)
            for cf in CORE_READ_FILES[:10]:
                tid=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=tid,
                    description=f"Read core file {cf} (ignore missing).",
                    tool_name=TOOL_READ,
                    tool_args={"path": cf, "ignore_missing": True, "max_bytes": 40000},
                    dependencies=[]
                ))
                analysis_dependency_ids.append(tid)

        role_task_id=None
        if ROLE_DERIVATION and len(files)>1:
            role_task_id=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=role_task_id,
                description="Derive unique roles JSON.",
                tool_name=TOOL_THINK,
                tool_args={"prompt": build_role_prompt(files, objective, lang)},
                dependencies=analysis_dependency_ids
            ))

        section_task_id=None
        inferred_sections=infer_sections(objective, lang)
        if inferred_sections:
            section_task_id=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=section_task_id,
                description="Refine sections JSON.",
                tool_name=TOOL_THINK,
                tool_args={"prompt": build_section_prompt(objective, inferred_sections, lang)},
                dependencies=[role_task_id] if role_task_id else analysis_dependency_ids
            ))

        final_writes=[]
        for f_i,fname in enumerate(files, start=1):
            base_deps=[]
            if role_task_id: base_deps.append(role_task_id)
            if section_task_id: base_deps.append(section_task_id)
            if analysis_dependency_ids and not base_deps:
                base_deps=analysis_dependency_ids

            ensure_id=None
            if ENSURE_FILE:
                ensure_id=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=ensure_id,
                    description=f"Ensure file {fname} exists.",
                    tool_name=TOOL_ENSURE,
                    tool_args={"path": fname, "initial_content": self._initial_banner(fname, objective, lang)},
                    dependencies=[]
                ))
                base_deps.append(ensure_id)

            ftype=file_type(fname)

            if use_stream and self._append_allowed():
                prev=None
                for c in range(1,total_chunks+1):
                    think_id=_tid(idx); idx+=1
                    prompt=build_chunk_prompt(objective,fname,role_task_id,section_task_id,
                                              c,total_chunks,per_chunk,lang,ftype)
                    deps=base_deps.copy()
                    if prev: deps.append(prev)
                    tasks.append(PlannedTask(
                        task_id=think_id,
                        description=f"Generate chunk {c}/{total_chunks} for {fname}.",
                        tool_name=TOOL_THINK,
                        tool_args={"prompt": prompt},
                        dependencies=deps
                    ))
                    append_id=_tid(idx); idx+=1
                    tasks.append(PlannedTask(
                        task_id=append_id,
                        description=f"Append chunk {c} to {fname}.",
                        tool_name=TOOL_APPEND,
                        tool_args={"path": fname, "content": f"{{{{{think_id}.answer}}}}"},
                        dependencies=[think_id]
                    ))
                    prev=append_id
                wrap_think=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=wrap_think,
                    description=f"Generate final wrap for {fname}.",
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
                chunk_thinks=[]
                for c in range(1,total_chunks+1):
                    think_id=_tid(idx); idx+=1
                    prompt=build_chunk_prompt(objective,fname,role_task_id,section_task_id,
                                              c,total_chunks,per_chunk,lang,ftype)
                    deps=base_deps.copy()
                    if chunk_thinks: deps.append(chunk_thinks[-1])
                    tasks.append(PlannedTask(
                        task_id=think_id,
                        description=f"Batch chunk {c}/{total_chunks} for {fname}.",
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
                        description=f"Final batch wrap for {fname}.",
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
                    description=f"Write composed file {fname}.",
                    tool_name=TOOL_WRITE,
                    tool_args={"path": fname, "content": final_content},
                    dependencies=[chunk_thinks[-1]] if chunk_thinks else base_deps
                ))
                final_writes.append(write_id)

        if INDEX_FILE_EN and len(files)>1:
            idx_think=_tid(idx); idx+=1
            idx_prompt_ar="أنشئ فهرساً مختصراً لكل الملفات الناتجة (سطران لكل ملف: المحور، الاستخدام)."
            idx_prompt_en="Create concise index for all generated artifacts (2 lines each: focus, usage)."
            tasks.append(PlannedTask(
                task_id=idx_think,
                description="Generate artifact index summary.",
                tool_name=TOOL_THINK,
                tool_args={"prompt": idx_prompt_ar if lang=='ar' else idx_prompt_en},
                dependencies=final_writes
            ))
            idx_write=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=idx_write,
                description=f"Write artifact index {INDEX_FILE_NAME}.",
                tool_name=TOOL_WRITE,
                tool_args={"path": INDEX_FILE_NAME, "content": f"{{{{{idx_think}.answer}}}}"},
                dependencies=[idx_think]
            ))
            final_writes.append(idx_write)

        plan=MissionPlanSchema(
            objective=objective,
            tasks=tasks,
            meta={
                "language": lang,
                "files": files,
                "requested_lines": req_lines,
                "total_chunks": total_chunks,
                "per_chunk": per_chunk,
                "streaming": use_stream,
                "append_mode": self._append_allowed(),
                "role_task": role_task_id,
                "section_task": section_task_id
            }
        )
        self._validate(plan, files)
        elapsed=(time.perf_counter()-start)*1000
        _LOG.info("[UltraHyperPlanner v7.0.2] tasks=%d files=%d streaming=%s ms=%.1f",
                  len(tasks), len(files), use_stream, elapsed)
        return plan

    # --- Internal Checks ---
    def _can_stream(self)->bool:
        if ALLOW_APPEND_MODE=="0": return False
        if ALLOW_APPEND_MODE=="1": return True
        # auto: تحرّي وجود الأداة في القائمة
        allowed_env=os.getenv("PLANNER_ALLOWED_TOOLS","")
        if allowed_env:
            allowed={t.strip() for t in allowed_env.split(",") if t.strip()}
            return "append_file" in allowed
        return True  # تفاؤلي

    def _append_allowed(self)->bool:
        return self._can_stream()

    def _wants_repo_scan(self, objective:str)->bool:
        low=objective.lower()
        return any(k in low for k in ("repository","repo","structure","architecture","معمار","هيكل","بنية","analyze project"))

    def _initial_banner(self, fname:str, objective:str, lang:str)->str:
        ext=fname.lower()
        if ext.endswith((".md",".txt",".log",".rst",".adoc",".html")):
            return (f"# تهيئة: {fname}\n\n> الهدف: {objective[:180]}...\n\n") if lang=='ar' \
                   else (f"# Init: {fname}\n\n> Objective: {objective[:180]}...\n\n")
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
    demo="Analyze repository structure and create file named repo-overview.md"
    print(p.generate_plan(demo).meta)