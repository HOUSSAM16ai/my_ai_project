import os
from typing import Any

from .config import CONFIG


def summarize_for_prompt(index: dict[str, Any], max_len: int = 6000) -> str:
    """
    Builds a compressed text summary for LLM consumption.
    """
    lines: list[str] = []
    push = lines.append

    push(f"FILES_SCANNED={index.get('files_scanned')}")

    # Global Metrics including LOC
    gm = index.get("global_metrics", {})
    if gm:
        push(
            f"GLOBAL: LOC={gm.get('total_loc', '?')} funcs={gm.get('total_functions')} "
            f"avg_cx={gm.get('avg_function_complexity')} max_cx={gm.get('max_function_complexity')}"
        )

    # Top Files by LOC (Size/Importance)
    fmetrics = index.get("file_metrics", [])
    if fmetrics:
        sorted_files = sorted(fmetrics, key=lambda x: x.get("loc", 0), reverse=True)
        push("LARGEST_FILES:")
        for f in sorted_files[:10]:
            push(f"- {f['path']} loc={f['loc']} funcs={f['function_count']}")

    # Hotspots
    hotspots = index.get("complexity_hotspots_top50", []) or index.get("complexity_hotspots", [])
    if hotspots:
        push("HOTSPOTS (High Complexity):")
        for h in hotspots[:10]:
            push(f"- {h['file']}::{h['name']} loc={h['loc']} cx={h['complexity']}")

    # Duplicates
    dupes = index.get("duplicate_function_bodies", {})
    if dupes:
        push("DUPLICATES:")
        for c, (h, items) in enumerate(dupes.items()):
            push(f"- hash {h[:8]}... -> {len(items)} funcs")
            if c >= 5:
                break

    # Dependencies
    deps = index.get("dependencies", {})
    if deps:
        push("DEPENDENCIES_SAMPLE:")
        for i, (k, v) in enumerate(deps.items()):
            if v:
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
                if i >= 5:
                    break

        # Service Candidates
        svc = index.get("service_candidates", [])
        if svc:
            push("SERVICE_CANDIDATES:")
            for s in svc[:10]:
                push(f"- {s}")

    text = "\n".join(lines)
    if len(text) > max_len:
        return text[:max_len] + "\n[TRUNCATED]"
    return text
