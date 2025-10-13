"""
Ultra Deep Structural / Semantic-Oriented Indexer (Enhanced v2)
================================================================
هذا الملف مُعاد كتابته ليكون "خارِق" ومتوافقاً بشكل كامل مع UltraHyperPlanner (v7.3.0)
مع الحفاظ على التوافق الخلفي (Backward Compatibility) مع التوقيعات:
    - build_index(root=".")
    - summarize_for_prompt(index: dict, max_len: int = ...)

الأهداف الأساسية:
1. استخراج هيكلي عميق للكود (دوال، أصناف، تعقيد، تكرارات، تبعيات).
2. دعم تحليلات إضافية (طبقات layers، خدمات محتملة، نقاط دخول entrypoints، call graph مبسّط).
3. كشف التكرار بالهاش بعد تطبيع الكود.
4. دعم Caching اختياري (Incremental) يقلّل إعادة التحليل (مستند إلى ENV).
5. إنتاج ملخصات مختلفة قابلة للدمج في خط أنابيب التخطيط (planner).
6. توفير بيانات قياس (metrics) للتليمتري (عدد ملفات، متوسط تعقيد، أكبر دوال ... إلخ).
7. تصميم دفاعي (Graceful Degradation) – أي فشل لا يكسر المنظومة بل يُسجل error.

ENV FLAGS (قابلة للضبط)
----------------------------------------------------------------
PLANNER_INDEX_CACHE_ENABLE=0|1        تفعيل الكاش (متوافق مع الـ Planner)
DEEP_INDEX_CACHE_DIR=.planner_cache   مجلد تخزين الكاش
DEEP_INDEX_MAX_FILE_BYTES=300000      أقصى حجم ملف (بايت)
DEEP_INDEX_MAX_FILES=4000             أقصى عدد ملفات Python
DEEP_INDEX_THREADS=4                  عدد خيوط التحليل (0 أو 1 = تسلسلي)
DEEP_INDEX_EXCLUDE_DIRS=.git,__pycache__,venv,env,.venv,node_modules,dist,build,migrations
DEEP_INDEX_INCLUDE_GLOBS=             (اختياري) جلوبات إضافية لملفات Python
DEEP_INDEX_INTERNAL_PREFIXES=app,src  بادئات تُعتبر تبعيات داخلية
DEEP_INDEX_DUP_HASH_PREFIX=16         طول هاش التكرار (حروف hex)
DEEP_INDEX_COMPLEXITY_HOTSPOT_CX=12   حد التعقيد لاعتبار الدالة hotspot
DEEP_INDEX_COMPLEXITY_HOTSPOT_LOC=120 حد الأسطر لاعتبار الدالة hotspot
DEEP_INDEX_CALL_GRAPH=1               بناء call graph مبسّط
DEEP_INDEX_LAYER_HEURISTICS=1         تفعيل استدلال الطبقات
DEEP_INDEX_SUMMARY_EXTRA=1            تضمين أقسام إضافية في الملخص
DEEP_INDEX_DETECT_SERVICES=1          محاولة تمييز خدمات (service candidates)
DEEP_INDEX_MAX_CALL_GRAPH_EDGES=12000 حد أقصى لحواف call graph (قبل القص)
DEEP_INDEX_MAX_DUP_GROUPS=250         حد أقصى لمجموعات التكرار
DEEP_INDEX_TIME_PROFILE=1             إدراج أزمنة مراحل البناء

النتائج الجديدة (حقول إضافية)
----------------------------------------------------------------
- file_metrics: قائمة قياسات لكل ملف
- layers: خريطة layer -> ملفات
- service_candidates: قائمة ملفات/وحدات مشكوك أنها خدمات
- entrypoints: ملفات تحتوي if __name__ == "__main__"
- call_graph_edges_sample: عينة من حواف call graph (اختياري)
- global_metrics: ملخص إحصائي عالي المستوى
- cache_used / cached_files / changed_files / skipped_large_files
- generated_at (ISO8601)
- config (صورة من إعدادات التكوين)
- version_details: معلومات داخلية عن الإصدار

ملاحظات التوافق:
- الحقول التي يعتمد عليها UltraHyperPlanner موجودة (files_scanned, modules,
  complexity_hotspots_top50, duplicate_function_bodies, index_version).
- يمكن للمخطط تجاهل الحقول الإضافية دون ضرر.

"""

from __future__ import annotations

import ast
import glob
import hashlib
import json
import math
import os
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from typing import Any

# --------------------------------------------------------------------------------------
# Configuration Helpers
# --------------------------------------------------------------------------------------


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


# --------------------------------------------------------------------------------------
# Data Classes
# --------------------------------------------------------------------------------------


@dataclass
class FunctionInfo:
    name: str
    lineno: int
    end_lineno: int
    loc: int
    hash: str
    complexity: int
    recursive: bool
    tags: list[str]
    calls_out: list[str]  # raw callee names (not resolved fully)


@dataclass
class ClassInfo:
    name: str
    lineno: int
    end_lineno: int
    loc: int
    bases: list[str]


@dataclass
class FileModule:
    path: str
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[str]
    call_names: dict[str, int]
    file_hash: str
    error: str | None = None
    entrypoint: bool = False
    loc: int = 0


# --------------------------------------------------------------------------------------
# Utility Functions
# --------------------------------------------------------------------------------------


def _read_file(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_hash(path: str) -> str:
    try:
        st = os.stat(path)
        # سريع: mtime + size + sha256 جزئي للمحتوى (أول 64KB)
        with open(path, "rb") as f:
            head = f.read(64 * 1024)
        composite = f"{path}:{st.st_mtime_ns}:{st.st_size}:{hashlib.sha256(head).hexdigest()}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()
    except Exception:
        return "deadbeef"


def _hash_norm_function(code: str, prefix: int) -> str:
    """
    تطبيع شديد الاختصار:
      - إزالة التعليقات
      - إزالة السطور الفارغة
      - إزالة المسافات المتكررة
      - الاقتصار على أول prefix حروف من sha256
    """
    lines = []
    skip_doc = False
    doc_open = None
    for ln in code.splitlines():
        stripped = ln.strip()
        if not stripped:
            continue
        # التعليقات المنفصلة
        if stripped.startswith("#"):
            continue
        # محاولة إزالة السلاسل متعددة الأسطر (Docstring) البدائية
        if stripped.startswith(('"""', "'''")):
            marker = stripped[:3]
            if stripped.count(marker) == 1 and not stripped.endswith(marker):
                # بدأ docstring متعدد الأسطر
                skip_doc = True
                doc_open = marker
                continue
            if stripped.count(marker) >= 2:
                # سطر واحد docstring كامل – تجاهله
                continue
        if skip_doc:
            if doc_open and doc_open in stripped:
                skip_doc = False
            continue
        lines.append(stripped)
    norm = " ".join(lines)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:prefix]


def _estimate_complexity(node: ast.AST) -> int:
    """
    بسيط / محسّن قليلاً: حساب فروع التحكم + وزن بسيط للمركبات المنطقية.
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(
            child,
            (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith, ast.Match),
        ):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(1, len(getattr(child, "values", [])) - 1)
        elif isinstance(child, ast.ExceptHandler) or isinstance(
            child, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)
        ):
            complexity += 1
    return complexity


def _categorize(code: str) -> list[str]:
    lower = code.lower()
    tags: set[str] = set()
    if "async def " in lower:
        tags.add("async")
    if " for " in lower or " while " in lower:
        tags.add("iterative")
    if "math." in lower or "import math" in lower:
        tags.add("numeric")
    if "re." in lower:
        tags.add("regex")
    if any(x in lower for x in ("requests.", "httpx.", "urllib.")):
        tags.add("network")
    if any(x in lower for x in ("flask", "fastapi", "django")):
        tags.add("web")
    if "os." in lower or "subprocess" in lower:
        tags.add("system")
    if any(x in lower for x in ("sklearn", "torch", "tensorflow", "xgboost")):
        tags.add("ml")
    if any(x in lower for x in ("openai", "anthropic", "gemini", "langchain", "llama")):
        tags.add("llm")
    return sorted(list(tags))


def _layer_for_path(path: str) -> str | None:
    if not CONFIG["LAYER_HEURISTICS"]:
        return None
    segments = path.replace("\\", "/").split("/")
    # بسط heuristics
    if any("test" in s.lower() for s in segments):
        return "tests"
    if "migrations" in segments:
        return "migrations"
    if "api" in segments or "routes" in segments:
        return "api"
    if "services" in segments or "service" in segments:
        return "service"
    if "models" in segments or "schemas" in segments:
        return "model"
    if "utils" in segments or "helpers" in segments:
        return "utility"
    if "scripts" in segments or "cli" in segments:
        return "script"
    if "config" in segments or "settings" in segments:
        return "config"
    return None


def _service_candidate(path: str, code: str) -> bool:
    if not CONFIG["DETECT_SERVICES"]:
        return False
    lower = code.lower()
    # معيار مبسط: ملف في services/ أو يحتوي بناء FastAPI/Blueprint/Router
    if "services" in path or "service" in path:
        return True
    if any(x in lower for x in ("fastapi(", "flask(", "blueprint(", "apirouter(")):
        return True
    return False


# --------------------------------------------------------------------------------------
# File Collection
# --------------------------------------------------------------------------------------


def _collect_python_files(root: str) -> tuple[list[str], list[str]]:
    """
    Returns: (files, skipped_large_files)
    """
    max_bytes = CONFIG["MAX_FILE_BYTES"]
    exclude_dirs = CONFIG["EXCLUDE_DIRS"]
    py_files: list[str] = []
    skipped: list[str] = []
    root = os.path.abspath(root)

    def _excluded(dp: str) -> bool:
        for part in dp.replace("\\", "/").split("/"):
            if part in exclude_dirs:
                return True
        return False

    for dirpath, dirnames, filenames in os.walk(root):
        if _excluded(dirpath):
            continue
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            try:
                size = os.path.getsize(full)
                if size > max_bytes:
                    skipped.append(full)
                    continue
                py_files.append(full)
            except Exception:
                continue
        if len(py_files) >= CONFIG["MAX_FILES"]:
            break

    # Include extra globs if provided
    for pattern in CONFIG["INCLUDE_GLOBS"]:
        for matched in glob.glob(pattern, recursive=True):
            if matched.endswith(".py") and matched not in py_files:
                try:
                    if os.path.getsize(matched) <= max_bytes:
                        py_files.append(matched)
                except Exception:
                    pass

    return sorted(py_files)[: CONFIG["MAX_FILES"]], skipped


# --------------------------------------------------------------------------------------
# Parsing / Extraction
# --------------------------------------------------------------------------------------


def _parse_single_file(path: str, prior_hash: str | None = None) -> FileModule:
    code = _read_file(path)
    file_sha = _file_hash(path)
    if not code:
        return FileModule(
            path=path,
            functions=[],
            classes=[],
            imports=[],
            call_names={},
            file_hash=file_sha,
            error="empty_or_unreadable",
        )

    # If prior hash matches and caching could reuse parse (we still parse again if not using incremental storage)
    try:
        tree = ast.parse(code)
    except Exception as e:
        return FileModule(
            path=path,
            functions=[],
            classes=[],
            imports=[],
            call_names={},
            file_hash=file_sha,
            error=f"parse_error:{e}",
        )

    lines = code.splitlines()
    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []
    imports: list[str] = []
    call_counter = Counter()
    entrypoint = False

    # Detect entrypoint (approx)
    if "__name__" in code and "__main__" in code:
        # Cheap pattern
        for ln in lines:
            if "if __name__" in ln and "__main__" in ln:
                entrypoint = True
                break

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            slice_src = "\n".join(lines[start - 1 : end])
            h = _hash_norm_function(slice_src, CONFIG["DUP_HASH_PREFIX"])
            cx = _estimate_complexity(node)
            recursive = any(
                isinstance(ch, ast.Call)
                and isinstance(ch.func, ast.Name)
                and ch.func.id == node.name
                for ch in ast.walk(node)
            )
            tags = _categorize(slice_src)
            calls_out = []
            for ch in ast.walk(node):
                if isinstance(ch, ast.Call):
                    # capture name / attribute tail
                    if isinstance(ch.func, ast.Name):
                        calls_out.append(ch.func.id)
                    elif isinstance(ch.func, ast.Attribute):
                        calls_out.append(ch.func.attr)
            functions.append(
                FunctionInfo(
                    name=node.name,
                    lineno=start,
                    end_lineno=end,
                    loc=(end - start + 1),
                    hash=h,
                    complexity=cx,
                    recursive=recursive,
                    tags=tags,
                    calls_out=calls_out,
                )
            )
        elif isinstance(node, ast.ClassDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(b.attr)
                else:
                    bases.append(type(b).__name__)
            classes.append(
                ClassInfo(
                    name=node.name, lineno=start, end_lineno=end, loc=(end - start + 1), bases=bases
                )
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            else:
                if node.module:
                    imports.append(node.module)
        elif isinstance(node, ast.Call):
            fn_name = None
            if isinstance(node.func, ast.Name):
                fn_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                fn_name = node.func.attr
            if fn_name:
                call_counter[fn_name] += 1

    return FileModule(
        path=path,
        functions=functions,
        classes=classes,
        imports=imports,
        call_names=dict(call_counter),
        file_hash=file_sha,
        entrypoint=entrypoint,
        loc=len(lines),
    )


# --------------------------------------------------------------------------------------
# Caching Layer
# --------------------------------------------------------------------------------------


def _cache_paths(cache_dir: str) -> tuple[str, str]:
    os.makedirs(cache_dir, exist_ok=True)
    return (
        os.path.join(cache_dir, "deep_index_cache.json"),
        os.path.join(cache_dir, "deep_index_meta.json"),
    )


def _load_cache(cache_dir: str) -> dict[str, Any]:
    if not CONFIG["CACHE_ENABLE"]:
        return {}
    main_path, meta_path = _cache_paths(cache_dir)
    try:
        if os.path.exists(main_path):
            with open(main_path, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        return {}
    return {}


def _save_cache(cache_dir: str, data: dict[str, Any]) -> None:
    if not CONFIG["CACHE_ENABLE"]:
        return
    main_path, meta_path = _cache_paths(cache_dir)
    try:
        tmp = main_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, main_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            meta = {
                "saved_at": time.time(),
                "files": len(data.get("files", {})),
                "version_details": data.get("version_details"),
            }
            json.dump(meta, f, ensure_ascii=False)
    except Exception:
        pass


# --------------------------------------------------------------------------------------
# Call Graph & Aggregation
# --------------------------------------------------------------------------------------


def _build_call_graph(modules: list[FileModule]) -> tuple[list[tuple[str, str, str, str]], Counter]:
    """
    Returns:
      edges: [(file, function, callee_raw, callee_resolved? (maybe empty))]
      frequency: global callee count
    """
    if not CONFIG["CALL_GRAPH_ENABLE"]:
        return [], Counter()

    # Map function name -> list[(file, name)]
    fn_index = defaultdict(list)
    for m in modules:
        for fn in m.functions:
            fn_index[fn.name].append((m.path, fn.name))

    edges: list[tuple[str, str, str, str]] = []
    freq = Counter()

    for m in modules:
        for fn in m.functions:
            for callee in fn.calls_out:
                freq[callee] += 1
                resolved = ""
                # Resolve only if unique in index
                targets = fn_index.get(callee)
                if targets and len(targets) == 1:
                    resolved = f"{targets[0][0]}::{callee}"
                edges.append((m.path, fn.name, callee, resolved))
                if len(edges) >= CONFIG["MAX_CALL_GRAPH_EDGES"]:
                    break
            if len(edges) >= CONFIG["MAX_CALL_GRAPH_EDGES"]:
                break
        if len(edges) >= CONFIG["MAX_CALL_GRAPH_EDGES"]:
            break
    return edges, freq


def _aggregate_metrics(modules: list[FileModule]) -> dict[str, Any]:
    fn_count = 0
    total_cx = 0
    cx_values = []
    max_cx = 0
    max_fn = None
    total_loc = 0
    hotspots = []

    for m in modules:
        total_loc += m.loc
        for fn in m.functions:
            fn_count += 1
            total_cx += fn.complexity
            cx_values.append(fn.complexity)
            if fn.complexity > max_cx:
                max_cx = fn.complexity
                max_fn = f"{m.path}::{fn.name}"
            if fn.complexity >= CONFIG["HOTSPOT_COMPLEXITY"] or fn.loc >= CONFIG["HOTSPOT_LOC"]:
                hotspots.append(
                    {"file": m.path, "name": fn.name, "loc": fn.loc, "complexity": fn.complexity}
                )

    avg_cx = (total_cx / fn_count) if fn_count else 0.0
    std_cx = 0.0
    if cx_values:
        mean = avg_cx
        variance = sum((c - mean) ** 2 for c in cx_values) / len(cx_values)
        std_cx = math.sqrt(variance)

    return {
        "total_functions": fn_count,
        "total_loc": total_loc,
        "avg_function_complexity": round(avg_cx, 2),
        "std_function_complexity": round(std_cx, 2),
        "max_function_complexity": max_cx,
        "max_function_complexity_ref": max_fn,
        "hotspots_collected": len(hotspots),
        "hotspots": hotspots[:50],
    }


def _build_dependencies(
    modules: list[FileModule], internal_prefixes: tuple[str, ...]
) -> dict[str, list[str]]:
    dep_graph = defaultdict(set)
    for m in modules:
        for imp in m.imports:
            if imp.startswith(internal_prefixes):
                dep_graph[m.path].add(imp)
    return {k: sorted(v) for k, v in dep_graph.items()}


def _collect_dup_groups(modules: list[FileModule]) -> dict[str, list[dict[str, Any]]]:
    dup_map = defaultdict(list)
    for m in modules:
        for fn in m.functions:
            dup_map[fn.hash].append(
                {"file": m.path, "name": fn.name, "loc": fn.loc, "complexity": fn.complexity}
            )
    result = {h: v for h, v in dup_map.items() if len(v) > 1}
    # Trim to MAX_DUP_GROUPS to prevent explosion
    if len(result) > CONFIG["MAX_DUP_GROUPS"]:
        trimmed = {}
        for i, (k, v) in enumerate(result.items()):
            if i >= CONFIG["MAX_DUP_GROUPS"]:
                break
            trimmed[k] = v
        result = trimmed
    return result


def _file_metrics_list(modules: list[FileModule]) -> list[dict[str, Any]]:
    out = []
    for m in modules:
        cx_values = [fn.complexity for fn in m.functions]
        avg_cx = round(sum(cx_values) / len(cx_values), 2) if cx_values else 0.0
        max_cx = max(cx_values) if cx_values else 0
        tag_counter = Counter()
        for fn in m.functions:
            for t in fn.tags:
                tag_counter[t] += 1
        layer = _layer_for_path(m.path)
        out.append(
            {
                "path": m.path,
                "file_hash": m.file_hash,
                "loc": m.loc,
                "function_count": len(m.functions),
                "class_count": len(m.classes),
                "avg_function_complexity": avg_cx,
                "max_function_complexity": max_cx,
                "tags": sorted(tag_counter.keys()),
                "layer": layer,
                "entrypoint": m.entrypoint,
            }
        )
    return out


def _layer_map(file_metrics: list[dict[str, Any]]) -> dict[str, list[str]]:
    lm = defaultdict(list)
    for fm in file_metrics:
        if fm.get("layer"):
            lm[fm["layer"]].append(fm["path"])
    return {k: sorted(v) for k, v in lm.items()}


def _service_candidates(
    file_metrics: list[dict[str, Any]], file_sources: dict[str, str]
) -> list[str]:
    cands = []
    for fm in file_metrics:
        path = fm["path"]
        code = file_sources.get(path, "")
        if _service_candidate(path, code):
            cands.append(path)
    return sorted(list(set(cands)))


# --------------------------------------------------------------------------------------
# Public API: build_index
# --------------------------------------------------------------------------------------


def build_index(
    root: str = ".", internal_prefixes: tuple[str, ...] | None = None
) -> dict[str, Any]:
    """
    توليد فهرس هيكلي محسّن.
    متوافق مع واجهة الإصدار السابق ويضيف حقولاً متقدمة.
    """
    t0 = time.time()
    if internal_prefixes is None:
        internal_prefixes = CONFIG["INTERNAL_PREFIXES"]

    # Collect files
    files, skipped_large = _collect_python_files(root)
    file_sources: dict[str, str] = {}

    cache_data = _load_cache(CONFIG["CACHE_DIR"])
    prior_files_map = cache_data.get("files", {}) if cache_data else {}
    modules: list[FileModule] = []
    cached_files = 0
    changed_files = 0

    # Decide concurrency
    threads = CONFIG["THREADS"]
    parse_start = time.time()

    def process(path: str) -> FileModule:
        prev = prior_files_map.get(path)
        current_file_hash = _file_hash(path)
        if CONFIG["CACHE_ENABLE"] and prev and prev.get("file_hash") == current_file_hash:
            # Rehydrate from cache
            nonlocal cached_files
            cached_files += 1
            fm = FileModule(
                path=path,
                functions=[FunctionInfo(**f) for f in prev.get("functions", [])],
                classes=[ClassInfo(**c) for c in prev.get("classes", [])],
                imports=prev.get("imports", []),
                call_names=prev.get("call_names", {}),
                file_hash=current_file_hash,
                error=prev.get("error"),
                entrypoint=prev.get("entrypoint", False),
                loc=prev.get("loc", 0),
            )
            code = _read_file(path) if not CONFIG["CACHE_ENABLE"] else ""
            if CONFIG["CACHE_ENABLE"]:
                # Avoid loading big code into memory unless needed for service candidate detection later.
                pass
            file_sources[path] = code
            return fm
        # Parse fresh
        fm = _parse_single_file(path)
        nonlocal changed_files
        changed_files += 1
        file_sources[path] = _read_file(path)
        return fm

    if threads and threads > 1:
        with ThreadPoolExecutor(max_workers=threads) as ex:
            futures = {ex.submit(process, f): f for f in files}
            for fut in as_completed(futures):
                modules.append(fut.result())
    else:
        for f in files:
            modules.append(process(f))

    parse_end = time.time()

    # Aggregations
    agg_start = time.time()
    # Dependencies
    dependencies = _build_dependencies(modules, internal_prefixes)
    # Call graph
    call_edges, call_freq = _build_call_graph(modules)
    # Global metrics
    gmetrics = _aggregate_metrics(modules)
    # Duplicates
    dup_groups = _collect_dup_groups(modules)
    # File metrics
    fmetrics = _file_metrics_list(modules)
    # Layer map
    layers = _layer_map(fmetrics)
    # Service candidates
    svc_cands = _service_candidates(fmetrics, file_sources)
    # Build modules (convert dataclasses to plain dict)
    module_entries = []
    for m in modules:
        module_entries.append(
            {
                "path": m.path,
                "functions": [asdict(fn) for fn in m.functions],
                "classes": [asdict(c) for c in m.classes],
                "imports": m.imports,
                "call_names": m.call_names,
                "error": m.error,
                "file_hash": m.file_hash,
                "entrypoint": m.entrypoint,
                "loc": m.loc,
            }
        )

    agg_end = time.time()

    # Compose index
    index = {
        "files_scanned": len(files),
        "modules": module_entries,
        "dependencies": dependencies,
        "functions": [
            {
                "file": m.path,
                **{
                    k: v for k, v in asdict(fn).items() if k != "calls_out"
                },  # keep backward compatibility
            }
            for m in modules
            for fn in m.functions
        ],
        "function_call_frequency_top50": (
            call_freq.most_common(50) if call_freq else call_freq.most_common(0)
        ),
        "complexity_hotspots_top50": gmetrics["hotspots"],
        "duplicate_function_bodies": dup_groups,
        "index_version": "ast-deep-v2",
        # NEW FIELDS
        "file_metrics": fmetrics,
        "layers": layers,
        "service_candidates": svc_cands,
        "entrypoints": sorted([m.path for m in modules if m.entrypoint]),
        "global_metrics": {
            "total_functions": gmetrics["total_functions"],
            "avg_function_complexity": gmetrics["avg_function_complexity"],
            "std_function_complexity": gmetrics["std_function_complexity"],
            "max_function_complexity": gmetrics["max_function_complexity"],
            "max_function_complexity_ref": gmetrics["max_function_complexity_ref"],
            "total_loc": gmetrics["total_loc"],
        },
        "call_graph_edges_sample": [
            {"file": f, "function": fn, "callee": cal, "resolved": res}
            for (f, fn, cal, res) in call_edges
        ],
        "cache_used": bool(CONFIG["CACHE_ENABLE"]),
        "cached_files": cached_files,
        "changed_files": changed_files,
        "skipped_large_files": skipped_large,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": CONFIG,
        "version_details": {
            "impl": "ultra_deep_indexer_v2",
            "python": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
        },
    }

    # Optional time profile
    if CONFIG["TIME_PROFILE"]:
        index["time_profile_ms"] = {
            "collect_parse": round((parse_end - parse_start) * 1000, 2),
            "aggregation": round((agg_end - agg_start) * 1000, 2),
            "total": round((time.time() - t0) * 1000, 2),
        }

    # Save cache representation
    if CONFIG["CACHE_ENABLE"]:
        cache_repr = {
            "files": {
                m["path"]: {
                    "functions": [
                        {
                            k: v
                            for k, v in fn.items()
                            if k
                            in (
                                "name",
                                "lineno",
                                "end_lineno",
                                "loc",
                                "hash",
                                "complexity",
                                "recursive",
                                "tags",
                            )
                        }
                        for fn in m["functions"]
                    ],
                    "classes": [
                        {
                            k: v
                            for k, v in c.items()
                            if k in ("name", "lineno", "end_lineno", "loc", "bases")
                        }
                        for c in m["classes"]
                    ],
                    "imports": m["imports"],
                    "call_names": m["call_names"],
                    "file_hash": m["file_hash"],
                    "error": m["error"],
                    "entrypoint": m["entrypoint"],
                    "loc": m["loc"],
                }
                for m in module_entries
            },
            "version_details": index["version_details"],
        }
        _save_cache(CONFIG["CACHE_DIR"], cache_repr)

    return index


# --------------------------------------------------------------------------------------
# Summary Builder
# --------------------------------------------------------------------------------------


def summarize_for_prompt(index: dict[str, Any], max_len: int = 6000) -> str:
    """
    يبني ملخصاً نصياً مضغوطاً متعدد الأقسام لاستخدامه داخل الـ LLM.
    يحافظ على بساطة التوقيع القديم، ويضيف أقسام عند تفعيل SUMMARY_EXTRA.
    """
    lines: list[str] = []
    push = lines.append

    push(f"FILES_SCANNED={index.get('files_scanned')}")
    gm = index.get("global_metrics", {})
    if gm:
        push(
            f"GLOBAL: funcs={gm.get('total_functions')} avg_cx={gm.get('avg_function_complexity')} "
            f"std={gm.get('std_function_complexity')} max_cx={gm.get('max_function_complexity')}"
        )
    # Hotspots
    hotspots = index.get("complexity_hotspots_top50", []) or index.get("complexity_hotspots", [])
    if hotspots:
        push("HOTSPOTS:")
        for h in hotspots[:12]:
            push(f"- {h['file']}::{h['name']} loc={h['loc']} cx={h['complexity']}")

    # Duplicates
    dupes = index.get("duplicate_function_bodies", {})
    if dupes:
        push("DUPLICATES:")
        c = 0
        for h, items in dupes.items():
            push(f"- hash {h} -> {len(items)} funcs")
            c += 1
            if c >= 10:
                break

    # Top calls
    freq = index.get("function_call_frequency_top50", [])
    if freq:
        push("TOP_CALLS:")
        for name, cnt in freq[:12]:
            push(f"- {name}:{cnt}")

    # Dependencies
    deps = index.get("dependencies", {})
    if deps:
        push("DEPENDENCIES_SAMPLE:")
        for i, (k, v) in enumerate(deps.items()):
            push(f"- {k} -> {len(v)} internal_refs")
            if i >= 10:
                break

    if CONFIG["SUMMARY_EXTRA"]:
        # Layers
        layers = index.get("layers", {})
        if layers:
            push("LAYERS:")
            for i, (layer, flist) in enumerate(layers.items()):
                push(f"- {layer}: {len(flist)} files")
                if i >= 8:
                    break
        # Services
        svc = index.get("service_candidates", [])
        if svc:
            push("SERVICE_CANDIDATES:")
            for s in svc[:10]:
                push(f"- {s}")
        # Entrypoints
        # (keep same block)
        entry = index.get("entrypoints", [])
        if entry:
            push("ENTRYPOINTS:")
            for e in entry[:5]:
                push(f"- {e}")
        # Call graph sample
        cges = index.get("call_graph_edges_sample", [])
        if cges:
            push("CALL_GRAPH_SAMPLE:")
            for edge in cges[:12]:
                fr = edge["file"]
                fn = edge["function"]
                cal = edge["callee"]
                res = edge.get("resolved") or ""
                push(f"- {fn}@{os.path.basename(fr)} -> {cal}{(' ('+res+')') if res else ''}")

    text = "\n".join(lines)
    if len(text) > max_len:
        return text[:max_len] + "\n[TRUNCATED]"
    return text


# --------------------------------------------------------------------------------------
# CLI (Manual Testing)
# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Ultra Deep Indexer v2")
    ap.add_argument("--root", default=".", help="Root directory")
    ap.add_argument("--summary", action="store_true", help="Print summary only")
    ap.add_argument("--json", action="store_true", help="Print full JSON (truncated)")
    ap.add_argument("--max-len", type=int, default=6000)
    args = ap.parse_args()

    idx = build_index(args.root)
    if args.summary:
        print("---- PROMPT SUMMARY ----")
        print(summarize_for_prompt(idx, max_len=args.max_len))
    if args.json:
        raw = json.dumps(idx, ensure_ascii=False)
        print("---- JSON (TRUNCATED 12000) ----")
        print(raw[:12000])
    if not args.summary and not args.json:
        # default behavior: both short stats + summary
        print(
            f"Scanned: {idx['files_scanned']} files | Functions: {idx['global_metrics']['total_functions']}"
        )
        print(summarize_for_prompt(idx, max_len=2000))
