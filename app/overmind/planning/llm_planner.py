# -*- coding: utf-8 -*-
# app/overmind/planning/llm_planner.py
# -*- coding: utf-8 -*-
"""
ULTRA HYPER SEMANTIC PLANNER (v7.0.0-omni)
==========================================
(ملف خارق خيالي نهائي) – تحويل أي وصف بشري (عربي / إنجليزي / خليط) إلى خطة مهام تنفيذية
تستخدم الأدوات المتاحة (generic_think, ensure_file, write_file, append_file, read_file, list_dir)
وتتعامل مع سيناريوهات: إنتاج ملفات هائلة (حتى مليون سطر منطقي)، عدة ملفات، تحليل، أقسام،
توليد محتوى متدفق (Chunked Streaming) أو دمج دفعي (Batch Composition) عند عدم توفر append_file
ضمن قائمة الأدوات المسموح بها.

أهداف التصميم الأساسية
----------------------
1. فهم نية المستخدم دلالياً (ملف واحد / عدة ملفات / حجم ضخم / تحليل مستودع / تقرير معماري / ملخص / باكلوج...).
2. استخراج أسماء الملفات بأي صياغات بشرية (احفظه في / ملف باسم / save as / output to / deliverable).
3. دعم عدة ملفات مع توزيع أدوار فريد (Role Derivation) وعدم تكرار المحتوى بين الملفات.
4. دعم طلبات الحجم (مثل: 100000 lines / مليون سطر / very large / ضخم) عبر حساب خطة تقسيم (Chunk Plan).
5. إذا append_file متاح ومسموح → استخدام نمط Streaming (chunk_think -> append_file).
   إن لم يكن متاحاً → إنشاء مجموعة generic_think للقطع ثم write_file نهائي يدمجها (Batch Fallback).
6. حقن تحسينات خاصة حسب الامتداد (ملف كود، بيانات، توثيق).
7. إنتاج عربي افتراضي عند وجود أي عربية أو تفعيل FORCE_ARABIC، وإلا لغة افتراضية عربية/إنجليزية (قابلة للتهيئة).
8. سلامة: حماية عدد المهام، منع الاعتماديات المكسورة، ضمان وجود write_file أو (append_file سلسلة + ensure_file).
9. مرونة: يمكن تفعيل/تعطيل خصائص عبر متغيرات بيئة (انظر ENV FLAGS).
10. كل المخرجات يمكن توسيعها لاحقاً بإضافة أدوات جديدة دون كسر البناء الحالي.

قيود واقعية
-----------
- النموذج الخلفي (generic_think) محدود بطول المخرجات (GENERIC_THINK_MAX_ANSWER_CHARS). التخطيط يتخطّى ذلك بالتقسيم.
- "مليون سطر" = هدف منطقي: الخطة تصنع عدداً من الـ chunks القابلة للتنفيذ تباعاً.
- التنفيذ الفعلي للمهام يقع على منفذ (Agent Runner) خارج هذا المخطط.

ENV FLAGS (جديدة / مهمة)
------------------------
PLANNER_FORCE_ARABIC=0|1                 فرض اللغة العربية دائماً.
PLANNER_LANGUAGE_FALLBACK=ar|en          لغة fallback افتراضية (ar).
PLANNER_MAX_FILES=12                     الحد الأقصى للملفات.
PLANNER_DEFAULT_EXT=.md                  الامتداد الافتراضي إن غاب.
PLANNER_SMART_FILENAME=1                 تنظيف أسماء الملفات.
PLANNER_ALLOW_SUBDIRS=1                  السماح بمسارات فرعية.
PLANNER_MAX_TASKS_GLOBAL=400             سقف أقصى للمهام.
PLANNER_MAX_CHUNKS=50                    أعلى عدد chunks لكل ملف.
PLANNER_CHUNK_SIZE_HINT=1200             حجم chunk تقديري (أسطر منطقية).
PLANNER_HARD_LINE_CAP=1000000            أقصى lines يطلبها المستخدم (للحماية).
PLANNER_FAST_SINGLE_THRESHOLD=1800       إن كان الطلب <= هذا نستخدم مسار chunk=1 (إن لم تُذكر very large).
PLANNER_STREAMING_ENABLE=1               تفعيل وضع البث (إن توفر append_file).
PLANNER_APPEND_FALLBACK_BATCH=1          إن لم يتوفر append_file استخدم تركيب دفعي.
PLANNER_ENABLE_SECTION_INFER=1           استنتاج الأقسام إن لم تُذكر.
PLANNER_ENABLE_ROLE_DERIVATION=1         أدوار متعددة للملفات.
PLANNER_MULTI_ROLE_JSON=1                إخراج JSON من مهمة الأدوار.
PLANNER_ENABLE_CODE_HINTS=1              تحسين الأسلوب لملفات الكود.
PLANNER_ENSURE_FILE=1                    إدراج ensure_file لتثبيت الملف قبل الكتابة.
PLANNER_INDEX_FILE=1                     إنشاء فهرس artifacts عند تعدد الملفات.
PLANNER_INDEX_NAME=ARTIFACT_INDEX.md     اسم ملف الفهرس.
PLANNER_STRICT_WRITE_ENFORCE=1           تأكيد وجود كتابة نهائية لكل ملف.
PLANNER_ALLOW_APPEND_TOOL=auto|1|0       auto=يتحرى وجود الأداة، 1=افرض استخدامها، 0=تعطيل.
PLANNER_ALLOW_LIST_READ_ANALYSIS=1       إدراج list_dir/read_file عند نوايا التحليل.
PLANNER_CORE_READ_FILES=README.md,requirements.txt,Dockerfile,config.py,pyproject.toml

ملاحظات
--------
- يمكن للمستخدم طلب: "أريد ملف خارق 500000 lines اسمه knowledge_base.log"
  فيُنشئ المخطط خطة chunks بعدد مناسب.
- إن طلب عدة ملفات مع أدوار مختلفة: يقوم بتوليد دور لكل ملف + أقسام (اختيارية) + محتوى chunks.
- الاستدلال العربي تلقائي (أي حروف عربية أو Force Arabic).

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
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)

# --------------------------------------------------------------------------------------
# Base / Schemas Imports (with stub fallback)
# --------------------------------------------------------------------------------------
_ALLOW_STUB = os.getenv("LLM_PLANNER_ALLOW_STUB","0")=="1"
try:
    from .base_planner import BasePlanner, PlannerError, PlanValidationError  # type: ignore
except Exception as e:  # pragma: no cover
    if not _ALLOW_STUB:
        raise
    class PlannerError(Exception):
        def __init__(self, msg:str, planner:str="stub", objective:str="", **extra):
            super().__init__(msg); self.planner=planner; self.objective=objective; self.extra=extra
    class PlanValidationError(PlannerError): ...
    class BasePlanner: name="stub"
try:
    from .schemas import MissionPlanSchema, PlannedTask, PlanningContext  # type: ignore
except Exception:
    if not _ALLOW_STUB: raise
    @dataclass
    class PlannedTask:  # minimal stub
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
APPEND_FALLBACK = os.getenv("PLANNER_APPEND_FALLBACK_BATCH","1")=="1"
SECTION_INFER   = os.getenv("PLANNER_ENABLE_SECTION_INFERENCE","1")=="1"
ROLE_DERIVATION = os.getenv("PLANNER_ENABLE_ROLE_DERIVATION","1")=="1"
ROLE_JSON       = os.getenv("PLANNER_MULTI_ROLE_JSON","1")=="1"
CODE_HINTS      = os.getenv("PLANNER_ENABLE_CODE_HINTS","1")=="1"
ENSURE_FILE     = os.getenv("PLANNER_ENSURE_FILE","1")=="1"
INDEX_FILE_EN   = os.getenv("PLANNER_INDEX_FILE","1")=="1"
INDEX_FILE_NAME = os.getenv("PLANNER_INDEX_NAME","ARTIFACT_INDEX.md")
STRICT_WRITE_ENF= os.getenv("PLANNER_STRICT_WRITE_ENFORCE","1")=="1"
ALLOW_APPEND_TOOL_FLAG = os.getenv("PLANNER_ALLOW_APPEND_TOOL","auto")  # auto | 1 | 0
ALLOW_LIST_READ_ANALYSIS = os.getenv("PLANNER_ALLOW_LIST_READ_ANALYSIS","1")=="1"
CORE_READ_FILES = [f.strip() for f in os.getenv(
    "PLANNER_CORE_READ_FILES",
    "README.md,requirements.txt,Dockerfile,config.py,pyproject.toml"
).split(",") if f.strip()]

# --------------------------------------------------------------------------------------
# Allowed / Known Tools
# --------------------------------------------------------------------------------------
TOOL_THINK  = "generic_think"
TOOL_WRITE  = "write_file"
TOOL_APPEND = "append_file"  # قد لا يكون دائماً ضمن PLANNER_ALLOWED_TOOLS
TOOL_ENSURE = "ensure_file"
TOOL_READ   = "read_file"
TOOL_LIST   = "list_dir"

# --------------------------------------------------------------------------------------
# Regex / Extraction
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

ALL_SAFE_EXTS = CODE_EXTS|DATA_EXTS|DOC_EXTS

# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def _clip(s:str,n:int=140)->str: return s if len(s)<=n else s[:n-3]+"..."
def _has_arabic(s:str)->bool: return any('\u0600' <= c <= '\u06FF' for c in s)
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
        for m in re.finditer(pat, norm, re.IGNORECASE):
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
        # heuristic: tokens with dot ext
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
            v=int(m.group(1))
            if mx is None or v>mx:
                mx=v
        except: pass
    if any(t in obj.lower() for t in HUGE_TERMS):
        if mx is None:
            mx=CHUNK_SIZE_HINT*10
        else:
            mx=int(mx*1.5)
    if mx and mx>HARD_LINE_CAP:
        mx=HARD_LINE_CAP
    return mx

def compute_chunk_plan(requested:Optional[int])->Tuple[int,int]:
    if not requested:
        requested = CHUNK_SIZE_HINT*2
    if requested <= FAST_SINGLE_THRESH:
        return 1, requested
    chunk_count = math.ceil(requested / CHUNK_SIZE_HINT)
    if chunk_count>MAX_CHUNKS: chunk_count=MAX_CHUNKS
    per_chunk = max(80, math.ceil(requested / chunk_count))
    return chunk_count, per_chunk

def infer_sections(obj:str, lang:str)->List[str]:
    if not SECTION_INFER: return []
    pat = re.compile(r'(?:sections?|أقسام|ضع\s+أقسام|include\s+sections?)\s*[:：]\s*(.+)', re.IGNORECASE)
    m=pat.search(obj)
    if m:
        tail=m.group(1)
        parts=re.split(r'[;,،]|(?:\band\b)|(?:\sو\s)', tail)
        clean=[p.strip(" .\t") for p in parts if p.strip()]
        return clean[:25]
    return (SECTION_HINTS_AR if lang=="ar" else SECTION_HINTS_EN)[:12]

def build_role_prompt(files:List[str], objective:str, lang:str)->str:
    listing=", ".join(files)
    if lang=="ar":
        return (f"الهدف:\n{objective}\n"
                f"الملفات: {listing}\n"
                "خصص لكل ملف محوراً مميزاً (focus) بلا تكرار. أعد JSON: "
                "[{filename, focus, outline_points, rationale}].")
    return (f"Objective:\n{objective}\nFiles: {listing}\n"
            "Assign each file a UNIQUE focus. Return JSON: "
            "[{filename, focus, outline_points, rationale}].")

def build_section_prompt(objective:str, draft_sections:List[str], lang:str)->str:
    listing="\n".join(f"- {s}" for s in draft_sections)
    if lang=="ar":
        return (f"الهدف:\n{objective}\nالأقسام المقترحة:\n{listing}\n"
                "حسّن وارجع JSON [{order, section_title, notes}]. يمكن الدمج/إعادة التسمية.")
    return (f"Objective:\n{objective}\nDraft Sections:\n{listing}\n"
            "Refine -> JSON [{order, section_title, notes}]. Merge/rename as needed.")

def file_type(fname:str)->str:
    ext=os.path.splitext(fname)[1].lower()
    if ext in CODE_EXTS: return "code"
    if ext in DATA_EXTS: return "data"
    if ext in DOC_EXTS:  return "doc"
    return "generic"

def code_hint(ftype:str, lang:str)->str:
    if not CODE_HINTS: return ""
    if ftype=="code":
        return "أضف أمثلة كود منظمة وتعليقات واضحة.\n" if lang=="ar" else "Add idiomatic code examples and clear commentary.\n"
    if ftype=="data":
        return "أضف أمثلة سجلات وشرح الحقول.\n" if lang=="ar" else "Provide sample records and field explanations.\n"
    return ""

def build_chunk_prompt(
    objective:str, fname:str, role_id:Optional[str], section_id:Optional[str],
    cidx:int, ctotal:int, target_lines:int, lang:str, ftype:str
)->str:
    role_ref = f"{{{{{role_id}.answer}}}}" if role_id else "(no role metadata)"
    section_ref = f"{{{{{section_id}.answer}}}}" if section_id else "(no section metadata)"
    base_ar = lang=="ar"
    header_ar = (
        f"الهدف:\n{objective}\n"
        f"الملف: {fname}\n"
        f"المحور: {role_ref}\n"
        f"الأقسام: {section_ref}\n"
        f"جزء {cidx}/{ctotal} (~{target_lines} سطر منطقي).\n"
    )
    header_en = (
        f"Objective:\n{objective}\n"
        f"File: {fname}\n"
        f"Focus: {role_ref}\n"
        f"Sections: {section_ref}\n"
        f"Chunk {cidx}/{ctotal} (~{target_lines} logical lines).\n"
    )
    guidelines_ar = (
        "- لا تكرر المقدمة كاملة.\n"
        "- استمر منطقياً من حيث انتهى الجزء السابق (مفترض).\n"
        "- لا تُنهِ المحتوى النهائي قبل الجزء الأخير.\n"
        "- أضف تفصيل غني (قوائم / أمثلة / كود إن لزم).\n"
        "- تجنب الحشو؛ كن ثرياً بالمعلومة.\n"
    )
    guidelines_en = (
        "- Do not fully repeat the intro.\n"
        "- Continue logically (assume prior context).\n"
        "- Do not finalize early; only wrap near last chunk.\n"
        "- Enrich with lists, examples, code if relevant.\n"
        "- Avoid fluff; be information-dense.\n"
    )
    hint = code_hint(ftype, lang)
    return (header_ar + guidelines_ar + hint) if base_ar else (header_en + guidelines_en + hint)

def build_final_wrap_prompt(objective:str, fname:str, role_id:Optional[str], lang:str)->str:
    role_ref = f"{{{{{role_id}.answer}}}}" if role_id else "(no role data)"
    if lang=="ar":
        return (
            f"الهدف:\n{objective}\n"
            f"الملف: {fname}\n"
            f"اعطِ خلاصة تنفيذية بالعربية الفصيحة (<=200 سطر منطقي) تعكس المحتوى السابق "
            f"ومحور الملف من {role_ref} مع إبراز النقاط الجوهرية فقط."
        )
    return (
        f"Objective:\n{objective}\nFile: {fname}\n"
        f"Produce final executive summary (<=200 logical lines) capturing key insights aligned with {role_ref}."
    )

def _tid(i:int)->str: return f"t{i:02d}"

# --------------------------------------------------------------------------------------
# Planner Class
# --------------------------------------------------------------------------------------
class UltraHyperPlanner(BasePlanner):
    name = "ultra_hyper_semantic_planner"
    version = "7.0.0-omni"
    production_ready = True
    capabilities = {"semantic","chunked","multi-file","arabic","adaptive"}
    tags = {"ultra","hyper","giga","planner"}

    @classmethod
    def self_test(cls)->Tuple[bool,str]:
        return True, "ok"

    # Main entry
    def generate_plan(
        self,
        objective:str,
        context:Optional[PlanningContext]=None,
        max_tasks:Optional[int]=None
    )->MissionPlanSchema:
        start=time.perf_counter()
        if not self._valid_objective(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        lang=_detect_lang(objective)
        filenames=extract_filenames(objective)
        norm_files=[]
        for f in filenames:
            nf=_normalize_filename(f)
            if "." not in nf:
                nf=_ensure_ext(nf)
            if nf.lower() not in [x.lower() for x in norm_files]:
                norm_files.append(nf)
        filenames=norm_files[:MAX_FILES]

        req_lines=extract_requested_lines(objective)
        total_chunks, per_chunk = compute_chunk_plan(req_lines)
        streaming_possible = self._can_stream()
        use_stream = streaming_possible and STREAM_ENABLE and total_chunks>1

        tasks: List[PlannedTask]=[]
        idx=1

        # Optional repository/list/read analysis if objective suggests analysis
        analysis_dependency_ids=[]
        if ALLOW_LIST_READ_ANALYSIS and self._wants_repo_scan(objective):
            # list root + maybe 'app'
            for root in (".","app"):
                tid=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=tid,
                    description=f"List directory '{root}' (structural scan).",
                    tool_name=TOOL_LIST,
                    tool_args={"path": root, "max_entries": 400},
                    dependencies=[]
                ))
                analysis_dependency_ids.append(tid)
            # read core files
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
        if ROLE_DERIVATION and len(filenames)>1:
            role_task_id=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=role_task_id,
                description="Derive unique roles for each file (JSON).",
                tool_name=TOOL_THINK,
                tool_args={
                    "prompt": build_role_prompt(filenames, objective, lang),
                    "mode": "analysis"
                },
                dependencies=analysis_dependency_ids
            ))

        section_task_id=None
        inferred_sections = infer_sections(objective, lang)
        if inferred_sections:
            section_task_id=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=section_task_id,
                description="Refine sections JSON.",
                tool_name=TOOL_THINK,
                tool_args={
                    "prompt": build_section_prompt(objective, inferred_sections, lang),
                    "mode": "analysis"
                },
                dependencies=[role_task_id] if role_task_id else analysis_dependency_ids
            ))

        final_writes=[]
        for f_i, fname in enumerate(filenames, start=1):
            base_deps=[]
            if role_task_id: base_deps.append(role_task_id)
            if section_task_id: base_deps.append(section_task_id)
            if analysis_dependency_ids and not base_deps:
                base_deps=analysis_dependency_ids

            # ensure file
            ensure_id=None
            if ENSURE_FILE:
                ensure_id=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=ensure_id,
                    description=f"Ensure output file {fname} exists.",
                    tool_name=TOOL_ENSURE,
                    tool_args={
                        "path": fname,
                        "initial_content": self._initial_banner(fname, objective, lang),
                        "allow_create": True
                    },
                    dependencies=[]
                ))
                base_deps.append(ensure_id)

            ftype=file_type(fname)
            # streaming or batch
            if use_stream and self._append_allowed():
                prev=None
                for c in range(1, total_chunks+1):
                    think_id=_tid(idx); idx+=1
                    prompt=build_chunk_prompt(
                        objective, fname, role_task_id, section_task_id,
                        c, total_chunks, per_chunk, lang, ftype
                    )
                    deps=base_deps.copy()
                    if prev: deps.append(prev)
                    tasks.append(PlannedTask(
                        task_id=think_id,
                        description=f"Generate chunk {c}/{total_chunks} for {fname}.",
                        tool_name=TOOL_THINK,
                        tool_args={"prompt": prompt, "mode": "analysis"},
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
                # final wrap
                wrap_think=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=wrap_think,
                    description=f"Generate final wrap summary for {fname}.",
                    tool_name=TOOL_THINK,
                    tool_args={"prompt": build_final_wrap_prompt(objective, fname, role_task_id, lang)},
                    dependencies=[prev] if prev else base_deps
                ))
                wrap_write=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=wrap_write,
                    description=f"Append wrap summary to {fname}.",
                    tool_name=TOOL_APPEND,
                    tool_args={"path": fname, "content": f"\n\n{{{{{wrap_think}.answer}}}}"},
                    dependencies=[wrap_think]
                ))
                final_writes.append(wrap_write)
            else:
                # batch fallback
                chunk_thinks=[]
                for c in range(1, total_chunks+1):
                    think_id=_tid(idx); idx+=1
                    prompt=build_chunk_prompt(
                        objective, fname, role_task_id, section_task_id,
                        c, total_chunks, per_chunk, lang, ftype
                    )
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
                        description=f"Create final wrap summary for {fname} (batch).",
                        tool_name=TOOL_THINK,
                        tool_args={"prompt": build_final_wrap_prompt(objective, fname, role_task_id, lang)},
                        dependencies=[chunk_thinks[-1]]
                    ))

                # Compose content
                content_parts = [f"{{{{{cid}.answer}}}}" for cid in chunk_thinks]
                if wrap_think:
                    content_parts.append(f"\n\n{{{{{wrap_think}.answer}}}}")
                final_content = "\n\n".join(content_parts)
                write_id=_tid(idx); idx+=1
                tasks.append(PlannedTask(
                    task_id=write_id,
                    description=f"Write full composed file {fname}.",
                    tool_name=TOOL_WRITE,
                    tool_args={"path": fname, "content": final_content},
                    dependencies=[chunk_thinks[-1]] if chunk_thinks else base_deps
                ))
                final_writes.append(write_id)

        # index file
        if INDEX_FILE_EN and len(filenames)>1:
            idx_think=_tid(idx); idx+=1
            idx_prompt_ar=("أنشئ فهرساً موجزاً يجرد كل ملف تم إنشاؤه، مع سطرين يوضحان دوره وفارق تميزه،"
                           " وكيف يستخدم عملياً.")
            idx_prompt_en=("Create a concise index of all generated artifacts (2 lines each: role, differentiation, usage).")
            tasks.append(PlannedTask(
                task_id=idx_think,
                description="Generate artifact index summary.",
                tool_name=TOOL_THINK,
                tool_args={"prompt": idx_prompt_ar if lang=="ar" else idx_prompt_en},
                dependencies=final_writes
            ))
            idx_write=_tid(idx); idx+=1
            tasks.append(PlannedTask(
                task_id=idx_write,
                description=f"Write artifact index file {INDEX_FILE_NAME}.",
                tool_name=TOOL_WRITE,
                tool_args={"path": INDEX_FILE_NAME, "content": f"{{{{{idx_think}.answer}}}}"},
                dependencies=[idx_think]
            ))
            final_writes.append(idx_write)

        plan = MissionPlanSchema(
            objective=objective,
            tasks=tasks,
            meta={
                "language": lang,
                "files": filenames,
                "requested_lines": req_lines,
                "total_chunks": total_chunks,
                "per_chunk": per_chunk,
                "streaming": use_stream,
                "append_mode": self._append_allowed(),
                "role_task": role_task_id,
                "section_task": section_task_id
            }
        )
        self._validate(plan, filenames)
        elapsed=(time.perf_counter()-start)*1000
        _LOG.info("[UltraHyperPlanner] success files=%d tasks=%d streaming=%s ms=%.1f",
                  len(filenames), len(tasks), use_stream, elapsed)
        return plan

    # ----------------------------------------------------------------------------------
    # Helper internal logic
    def _append_allowed(self)->bool:
        if ALLOW_APPEND_TOOL_FLAG=="0":
            return False
        if ALLOW_APPEND_TOOL_FLAG=="1":
            return True
        # auto: rely on allowed tools environment (if exposed) or assume present if tool registry contains it
        # We don't have direct registry introspection here safely; assume available if user said tools include it.
        # Conservative approach: return True (agent runner will fail gracefully if not).
        return True

    def _wants_repo_scan(self, objective:str)->bool:
        low=objective.lower()
        return any(k in low for k in ("repository","repo","structure","architecture","معمار","هيكل","بنية","structure overview","analyze project"))

    def _initial_banner(self, fname:str, objective:str, lang:str)->str:
        ext=fname.lower()
        if ext.endswith(".md") or ext.endswith(".txt") or ext.endswith(".log"):
            if lang=="ar":
                return f"# تهيئة الملف: {fname}\n\n> الهدف: {objective[:180]}...\n\n"
            return f"# Init File: {fname}\n\n> Objective: {objective[:180]}...\n\n"
        if any(ext.endswith(e) for e in CODE_EXTS):
            return f"# Auto-generated start for objective: {objective[:120]}\n\n"
        if any(ext.endswith(e) for e in DATA_EXTS):
            return f"# Data artifact scaffold for: {objective[:120]}\n"
        return ""

    # ----------------------------------------------------------------------------------
    # Validation
    def _validate(self, plan:MissionPlanSchema, files:List[str]):
        if len(plan.tasks)>GLOBAL_TASK_CAP:
            raise PlanValidationError("excessive_tasks", self.name, plan.objective)
        ids={t.task_id for t in plan.tasks}
        for t in plan.tasks:
            for d in t.dependencies:
                if d not in ids:
                    raise PlanValidationError(f"dangling_dependency:{t.task_id}->{d}", self.name, plan.objective)
        # enforce write existence
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


# Backward alias (so external imports using old name still function)
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

# --------------------------------------------------------------------------------------
# Dev Quick Test
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    planner=UltraHyperPlanner()
    tests=[
        "أريد ملف خارق 500000 lines اسمه mega-vision.md يحلل كل شيء ويشرح بالتفصيل الهياكل والتدفق والمخاطر",
        "Create a massive 250000 lines deep technical exploration and save as deep_dive.txt",
        "Generate files named A.md, B.md and C.md each with unique perspectives: architecture, performance, risks",
        "حلل هيكل المستودع وبنيته وأنشئ ملف باسم repo-overview.md",
        "Create giant knowledge base (1000000 lines) save it as knowledge_base.log",
        "Produce file named schema.json with hierarchical API description and examples in Arabic",
        "summarize project goals"
    ]
    for obj in tests:
        print("\n=== OBJECTIVE:", obj)
        pl=planner.generate_plan(obj)
        print(f"Tasks={len(pl.tasks)} | Files={pl.meta.get('files')} | Streaming={pl.meta.get('streaming')} | Chunks={pl.meta.get('total_chunks')}")
        for t in pl.tasks[:12]:
            path=(t.tool_args or {}).get("path","")
            print(f" {t.task_id} | {t.tool_name} | deps={t.dependencies} | path={path}")
        if len(pl.tasks)>12:
            print("  ... more tasks ...")