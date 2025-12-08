import glob
import math
import os
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .analysis import (
    detect_entrypoint,
    file_hash,
    layer_for_path,
    parse_ast_safely,
    read_file,
    service_candidate,
)
from .config import CONFIG
from .graph import build_call_graph, build_dependencies
from .models import FileMetric, FileModule, GlobalMetrics, IndexResult
from .visitor import DeepIndexVisitor


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
        return any(part in exclude_dirs for part in dp.replace("\\", "/").split("/"))

    for dirpath, _dirnames, filenames in os.walk(root):
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


def _process_ast(path: str, code: str, file_sha: str, tree: Any) -> FileModule:
    lines = code.splitlines()
    entrypoint = detect_entrypoint(code, lines)

    visitor = DeepIndexVisitor(lines)
    visitor.visit(tree)

    return FileModule(
        path=path,
        functions=visitor.functions,
        classes=visitor.classes,
        imports=visitor.imports,
        call_names=dict(visitor.call_counter),
        file_hash=file_sha,
        entrypoint=entrypoint,
        loc=len(lines),
    )


def _parse_single_file(path: str) -> FileModule:
    code = read_file(path)
    file_sha = file_hash(path)

    if not code:
        return FileModule(path, [], [], [], {}, file_sha, "empty_or_unreadable")

    result = parse_ast_safely(code)
    if isinstance(result, str):
        return FileModule(path, [], [], [], {}, file_sha, result)

    return _process_ast(path, code, file_sha, result)


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
                    {
                        "file": m.path,
                        "name": fn.name,
                        "loc": fn.loc,
                        "complexity": fn.complexity,
                    }
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


def _collect_dup_groups(modules: list[FileModule]) -> dict[str, list[dict[str, Any]]]:
    dup_map = defaultdict(list)
    for m in modules:
        for fn in m.functions:
            dup_map[fn.hash].append(
                {
                    "file": m.path,
                    "name": fn.name,
                    "loc": fn.loc,
                    "complexity": fn.complexity,
                }
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


def _file_metrics_list(modules: list[FileModule]) -> list[FileMetric]:
    out = []
    for m in modules:
        cx_values = [fn.complexity for fn in m.functions]
        avg_cx = round(sum(cx_values) / len(cx_values), 2) if cx_values else 0.0
        max_cx = max(cx_values) if cx_values else 0
        tag_counter = Counter()
        for fn in m.functions:
            for t in fn.tags:
                tag_counter[t] += 1
        layer = layer_for_path(m.path)
        out.append(
            FileMetric(
                path=m.path,
                file_hash=m.file_hash,
                loc=m.loc,
                function_count=len(m.functions),
                class_count=len(m.classes),
                avg_function_complexity=avg_cx,
                max_function_complexity=max_cx,
                tags=sorted(tag_counter.keys()),
                layer=layer,
                entrypoint=m.entrypoint,
            )
        )
    return out


def _layer_map(file_metrics: list[FileMetric]) -> dict[str, list[str]]:
    lm = defaultdict(list)
    for fm in file_metrics:
        if fm.layer:
            lm[fm.layer].append(fm.path)
    return {k: sorted(v) for k, v in lm.items()}


def _service_candidates(file_metrics: list[FileMetric], file_sources: dict[str, str]) -> list[str]:
    cands = []
    for fm in file_metrics:
        path = fm.path
        code = file_sources.get(path, "")
        if service_candidate(path, code):
            cands.append(path)
    return sorted(set(cands))


def build_index(root: str = ".", internal_prefixes: tuple[str, ...] | None = None) -> IndexResult:
    if internal_prefixes is None:
        internal_prefixes = CONFIG["INTERNAL_PREFIXES"]

    # Collect files
    files, _skipped_large = _collect_python_files(root)
    file_sources: dict[str, str] = {}

    modules: list[FileModule] = []

    threads = CONFIG["THREADS"]

    def process(path: str) -> FileModule:
        fm = _parse_single_file(path)
        file_sources[path] = read_file(path)
        return fm

    if threads and threads > 1:
        with ThreadPoolExecutor(max_workers=threads) as ex:
            futures = {ex.submit(process, f): f for f in files}
            for fut in as_completed(futures):
                modules.append(fut.result())
    else:
        for f in files:
            modules.append(process(f))

    # Aggregations
    dependencies = build_dependencies(modules, internal_prefixes)
    # call_edges, call_freq = build_call_graph(modules) # Unused in IndexResult for now
    _call_edges, _call_freq = build_call_graph(modules)
    gmetrics_dict = _aggregate_metrics(modules)
    # dup_groups = _collect_dup_groups(modules) # Unused in minimal IndexResult
    fmetrics = _file_metrics_list(modules)
    layers = _layer_map(fmetrics)
    svc_cands = _service_candidates(fmetrics, file_sources)

    global_metrics = GlobalMetrics(
        total_functions=gmetrics_dict["total_functions"],
        avg_function_complexity=gmetrics_dict["avg_function_complexity"],
        std_function_complexity=gmetrics_dict["std_function_complexity"],
        max_function_complexity=gmetrics_dict["max_function_complexity"],
        max_function_complexity_ref=gmetrics_dict["max_function_complexity_ref"],
        total_loc=gmetrics_dict["total_loc"],
        hotspots=gmetrics_dict["hotspots"],
    )

    return IndexResult(
        files_scanned=len(files),
        global_metrics=global_metrics,
        file_metrics=fmetrics,
        layers=layers,
        service_candidates=svc_cands,
        dependencies=dependencies,
    )
