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
        for c, (h, items) in enumerate(dupes.items()):
            push(f"- hash {h} -> {len(items)} funcs")
            if c >= 9:  # Stop after 10 items (0-9)
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
                push(f"- {fn}@{os.path.basename(fr)} -> {cal}{(' (' + res + ')') if res else ''}")

    text = "\n".join(lines)
    if len(text) > max_len:
        return text[:max_len] + "\n[TRUNCATED]"
    return text
