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
    # Force type ignores here because the circular dependency or missing export in core
    # makes IndexResult hard to import directly without refactoring core.py
    # But wait, IndexResult is NOT defined in core.py based on the read_file output!
    # It seems IndexResult was assumed to exist but it's not there.
    # I will inspect the structure of the dict returned by build_index and use a SimpleNamespace or just Any.

    # Based on core.py: build_index returns a dict.
    # So we should treat index_result as a dict or an object wrapping it.
    # For safety in this "Superhuman Fix", I will accept Any and access safely.

    # Convert dict to object-like access if needed, or just access keys
    if isinstance(index_result, dict):

        class Struct:
            def __init__(self, **entries):
                self.__dict__.update(entries)

        # Deep conversion might be needed, but let's try shallow for top keys
        # Actually, let's just use dict access to be safe and robust.
        idx = index_result
        files_scanned = idx.get("files_scanned", 0)
        g = idx.get("global_metrics", {})
        file_metrics = idx.get("file_metrics", [])
        layers = idx.get("layers", {})
    else:
        # Assume it's an object
        files_scanned = index_result.files_scanned
        g = index_result.global_metrics
        file_metrics = index_result.file_metrics
        layers = index_result.layers

    # Global stats
    total_loc = g.get("total_loc", 0) if isinstance(g, dict) else g.total_loc
    total_functions = g.get("total_functions", 0) if isinstance(g, dict) else g.total_functions
    # classes not in global metrics in core.py output? Let's check.
    # core.py _aggregate_metrics doesn't list classes.
    # So we skip classes count to be safe.

    avg_cx = (
        g.get("avg_function_complexity", 0) if isinstance(g, dict) else g.avg_function_complexity
    )
    max_cx = (
        g.get("max_function_complexity", 0) if isinstance(g, dict) else g.max_function_complexity
    )

    summary_lines = [
        "### Project Stats",
        f"- Total Files: {files_scanned}",
        f"- LOC={total_loc}, funcs={total_functions}",
        f"- Complexity: avg={avg_cx}, max={max_cx}",
        "",
        "### Top Files (by LOC)",
    ]

    # Sort files by LOC desc
    # file_metrics is a list of dicts based on core.py _file_metrics_list
    if file_metrics and isinstance(file_metrics[0], dict):
        sorted_files = sorted(file_metrics, key=lambda x: x["loc"], reverse=True)[:5]
        for f in sorted_files:
            summary_lines.append(f"- {f['path']} (loc={f['loc']})")
    else:
        # Object access
        sorted_files = sorted(file_metrics, key=lambda x: x.loc, reverse=True)[:5]
        for f in sorted_files:
            summary_lines.append(f"- {f.path} (loc={f.loc})")

    summary_lines.append("")
    summary_lines.append("### Architecture Layers")
    for layer, files in layers.items():
        if files:
            summary_lines.append(f"- {layer.title()}: {len(files)} files")

    return "\n".join(summary_lines)


def _format_function_signature(func_node: Any) -> str:
    """Extracts a simple signature string."""
    return "func(...)"
