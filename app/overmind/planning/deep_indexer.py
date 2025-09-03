import os, ast, hashlib, json
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter

# تكوينات قابلة للتعديل لاحقاً
EXCLUDE_DIRS = {".git", "__pycache__", "venv", "env", ".venv", "node_modules", "migrations", "dist", "build"}
MAX_FILE_BYTES = 300_000
PY_EXT = (".py",)

def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""

def _hash_norm(code: str) -> str:
    # إزالة التعليقات والمسافات غير اللازمة لإنشاء توقيع (hash) لكود الدالة
    lines = []
    for ln in code.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        lines.append(ln)
    norm = " ".join(lines)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]

def _estimate_complexity(node: ast.AST) -> int:
    """
    تقدير بسيط للتعقيد الدوراني (Cyclomatic Approx):
    زيادة العداد عند وجود if/for/while/try/with/except/BooleanOps
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor, ast.AsyncWith)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(1, len(getattr(child, "values", [])) - 1)
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
    return complexity

def _categorize(func_src: str) -> Set[str]:
    tags = set()
    lower = func_src.lower()
    if "for " in func_src or "while " in func_src:
        tags.add("iterative")
    if "import math" in lower or "math." in lower:
        tags.add("numeric")
    if "re." in func_src:
        tags.add("regex")
    if "requests." in func_src or "httpx." in func_src:
        tags.add("network")
    if "flask" in lower or "fastapi" in lower:
        tags.add("web")
    if "os." in func_src or "subprocess" in func_src:
        tags.add("system")
    if any(x in lower for x in ["sklearn", "torch", "tensorflow"]):
        tags.add("ml")
    if any(x in lower for x in ["openai", "anthropic", "gemini"]):
        tags.add("llm")
    return tags

def collect_python_files(root: str = ".") -> List[str]:
    out: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # استثناء مجلدات
        if any(part in EXCLUDE_DIRS for part in dirpath.split(os.sep)):
            continue
        for fn in filenames:
            if fn.endswith(PY_EXT):
                full = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(full) <= MAX_FILE_BYTES:
                        out.append(full)
                except Exception:
                    pass
    return sorted(out)

def parse_file(path: str) -> Dict[str, Any]:
    code = _read_file(path)
    if not code:
        return {"path": path, "error": "empty_or_unreadable"}
    try:
        tree = ast.parse(code)
    except Exception as e:
        return {"path": path, "error": f"parse_error:{e}"}

    rel = path
    functions = []
    classes = []
    imports = []
    calls = Counter()
    lines = code.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            slice_src = "\n".join(lines[start-1:end])
            h = _hash_norm(slice_src)
            complexity = _estimate_complexity(node)
            is_recursive = any(
                isinstance(ch, ast.Call) and isinstance(ch.func, ast.Name) and ch.func.id == node.name
                for ch in ast.walk(node)
            )
            tags = list(_categorize(slice_src))
            functions.append({
                "name": node.name,
                "lineno": start,
                "end_lineno": end,
                "loc": (end - start + 1),
                "hash": h,
                "complexity": complexity,
                "recursive": is_recursive,
                "tags": tags
            })
        elif isinstance(node, ast.ClassDef):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            classes.append({
                "name": node.name,
                "lineno": start,
                "end_lineno": end,
                "loc": (end - start + 1),
                "bases": [getattr(b, "id", getattr(getattr(b, "attr", None), "__str__", lambda: "")()) for b in node.bases]
            })
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = []
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mods.append(alias.name)
            else:
                if node.module:
                    mods.append(node.module)
            for m in mods:
                imports.append(m)
        elif isinstance(node, ast.Call):
            fn_name = None
            if isinstance(node.func, ast.Name):
                fn_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                fn_name = node.func.attr
            if fn_name:
                calls[fn_name] += 1

    return {
        "path": rel,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "call_names": dict(calls)
    }

def build_index(root: str = ".", internal_prefixes: Tuple[str, ...] = ("app",)) -> Dict[str, Any]:
    files = collect_python_files(root)
    module_entries = []
    dep_edges = []
    call_freq_global = Counter()
    func_catalog = []
    complexity_hotspots = []
    hash_dupes = defaultdict(list)

    for f in files:
        data = parse_file(f)
        module_entries.append(data)
        if "error" in data:
            continue
        for imp in data["imports"]:
            # تبعية داخلية بدائية
            if imp.startswith(internal_prefixes):
                dep_edges.append((data["path"], imp))
        for fn in data["functions"]:
            func_catalog.append({"file": data["path"], **fn})
            hash_dupes[fn["hash"]].append((data["path"], fn["name"]))
            if fn["complexity"] >= 12 or fn["loc"] >= 120:
                complexity_hotspots.append({
                    "file": data["path"],
                    "name": fn["name"],
                    "loc": fn["loc"],
                    "complexity": fn["complexity"]
                })
        for name, cnt in data.get("call_names", {}).items():
            call_freq_global[name] += cnt

    duplicates = {h: v for h, v in hash_dupes.items() if len(v) > 1}

    graph = defaultdict(set)
    for src, dst in dep_edges:
        graph[src].add(dst)

    return {
        "files_scanned": len(files),
        "modules": module_entries,
        "dependencies": {k: sorted(v) for k, v in graph.items()},
        "functions": func_catalog,
        "function_call_frequency_top50": call_freq_global.most_common(50),
        "complexity_hotspots_top50": complexity_hotspots[:50],
        "duplicate_function_bodies": duplicates,
        "index_version": "ast-deep-v1"
    }

def summarize_for_prompt(index: Dict[str, Any], max_len: int = 3800) -> str:
    """
    يبني ملخصاً مضغوطاً يُمرر للـ LLM (لا نرسل كل شيء لتجنب الضخامة).
    """
    lines = []
    lines.append(f"FILES_SCANNED={index.get('files_scanned')}")
    hotspots = index.get("complexity_hotspots_top50", [])
    if hotspots:
        lines.append("HOTSPOTS:")
        for h in hotspots[:12]:
            lines.append(f"- {h['file']}::{h['name']} loc={h['loc']} cx={h['complexity']}")
    dupes = index.get("duplicate_function_bodies", {})
    if dupes:
        lines.append("DUPLICATES:")
        c = 0
        for h, items in dupes.items():
            lines.append(f"- hash {h} -> {len(items)} funcs")
            c += 1
            if c >= 8:
                break
    freq = index.get("function_call_frequency_top50", [])
    if freq:
        lines.append("TOP_CALLS:")
        for name, cnt in freq[:12]:
            lines.append(f"- {name}:{cnt}")
    deps = index.get("dependencies", {})
    if deps:
        lines.append("DEPENDENCIES:")
        sel = list(deps.items())[:10]
        for k, v in sel:
            lines.append(f"- {k} -> {len(v)} internal refs")
    text = "\n".join(lines)
    if len(text) > max_len:
        return text[: max_len] + "\n[TRUNCATED]"
    return text

if __name__ == "__main__":
    idx = build_index(".")
    print(json.dumps(idx, ensure_ascii=False)[:8000])
    print("---- PROMPT SUMMARY ----")
    print(summarize_for_prompt(idx))