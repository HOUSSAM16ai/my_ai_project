from typing import Any


def summarize_for_prompt(index_result: Any, max_len: int = 4000) -> str:
    """
    Produces a condensed summary of the index specifically for the LLM System Prompt.
    Focuses on:
    - Global Metrics (LOC, Complexity)
    - Top 5 largest files
    - Top 5 most complex functions
    - Layer Architecture hints
    """
    if isinstance(index_result, dict):
        idx = index_result
        files_scanned = idx.get("files_scanned", 0)
        g = idx.get("global_metrics", {})
        file_metrics = idx.get("file_metrics", [])
        layers = idx.get("layers", {})
        hotspots = idx.get("complexity_hotspots_top50", [])
    else:
        files_scanned = index_result.files_scanned
        g = index_result.global_metrics
        file_metrics = index_result.file_metrics
        layers = index_result.layers
        hotspots = index_result.complexity_hotspots_top50

    # Global stats
    total_loc = g.get("total_loc", 0) if isinstance(g, dict) else g.total_loc
    total_functions = g.get("total_functions", 0) if isinstance(g, dict) else g.total_functions

    avg_cx = (
        g.get("avg_function_complexity", 0) if isinstance(g, dict) else g.avg_function_complexity
    )
    max_cx = (
        g.get("max_function_complexity", 0) if isinstance(g, dict) else g.max_function_complexity
    )

    summary_lines = [
        "### Project Stats",
        f"FILES_SCANNED={files_scanned}",
        f"GLOBAL: funcs={total_functions}",
        f"- LOC={total_loc}",
        f"- Complexity: avg={avg_cx}, max={max_cx}",
        "",
        "### Top Files (by LOC)",
    ]

    if file_metrics and isinstance(file_metrics, list) and len(file_metrics) > 0:
        if isinstance(file_metrics[0], dict):
            sorted_files = sorted(file_metrics, key=lambda x: x["loc"], reverse=True)[:5]
            for f in sorted_files:
                summary_lines.append(f"- {f['path']} (loc={f['loc']})")
        else:
            sorted_files = sorted(file_metrics, key=lambda x: x.loc, reverse=True)[:5]
            for f in sorted_files:
                summary_lines.append(f"- {f.path} (loc={f.loc})")

    summary_lines.append("")
    summary_lines.append("### Architecture Layers")
    for layer, files in layers.items():
        if files:
            summary_lines.append(f"- {layer.title()}: {len(files)} files")

    summary_lines.append("")
    summary_lines.append("### Complexity Hotspots")
    if hotspots and isinstance(hotspots, list) and len(hotspots) > 0:
        if isinstance(hotspots[0], dict):
            for h in hotspots[:5]:
                summary_lines.append(f"- {h['file']}::{h['name']}")
        else:
            for h in hotspots[:5]:
                summary_lines.append(f"- {h.file}::{h.name}")

    return "\n".join(summary_lines)


def _format_function_signature(func_node: Any) -> str:
    """Extracts a simple signature string."""
    return "func(...)"
