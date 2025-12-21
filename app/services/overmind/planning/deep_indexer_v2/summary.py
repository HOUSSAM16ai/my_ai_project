from typing import Any


def _normalize_input(index_result: Any) -> dict[str, Any]:
    """Helper to normalize input to a dictionary structure."""
    if isinstance(index_result, dict):
        return index_result

    # Assuming object with attributes
    return {
        "files_scanned": getattr(index_result, "files_scanned", 0),
        "global_metrics": getattr(index_result, "global_metrics", {}),
        "file_metrics": getattr(index_result, "file_metrics", []),
        "layers": getattr(index_result, "layers", {}),
        "complexity_hotspots_top50": getattr(index_result, "complexity_hotspots_top50", []),
    }


def _get_project_stats(files_scanned: int, global_metrics: Any) -> list[str]:
    """Extracts project statistics."""
    # Handle global_metrics being dict or object
    if isinstance(global_metrics, dict):
        total_loc = global_metrics.get("total_loc", 0)
        total_functions = global_metrics.get("total_functions", 0)
        avg_cx = global_metrics.get("avg_function_complexity", 0)
        max_cx = global_metrics.get("max_function_complexity", 0)
    else:
        total_loc = getattr(global_metrics, "total_loc", 0)
        total_functions = getattr(global_metrics, "total_functions", 0)
        avg_cx = getattr(global_metrics, "avg_function_complexity", 0)
        max_cx = getattr(global_metrics, "max_function_complexity", 0)

    return [
        "### Project Stats",
        f"FILES_SCANNED={files_scanned}",
        f"GLOBAL: funcs={total_functions}",
        f"- LOC={total_loc}",
        f"- Complexity: avg={avg_cx}, max={max_cx}",
        "",
    ]


def _get_top_files(file_metrics: list[Any]) -> list[str]:
    """Extracts top files by LOC."""
    lines = ["### Top Files (by LOC)"]

    if not file_metrics:
        return lines

    # Determine how to access loc and path
    is_dict = isinstance(file_metrics[0], dict)

    def get_loc(x):
        return x["loc"] if is_dict else getattr(x, "loc", 0)

    def get_path(x):
        return x["path"] if is_dict else getattr(x, "path", "")

    sorted_files = sorted(file_metrics, key=get_loc, reverse=True)[:5]

    for f in sorted_files:
        lines.append(f"- {get_path(f)} (loc={get_loc(f)})")

    return lines


def _get_architecture_layers(layers: dict[str, Any]) -> list[str]:
    """Extracts architecture layer info."""
    lines = ["", "### Architecture Layers"]
    for layer, files in layers.items():
        if files:
            lines.append(f"- {layer.title()}: {len(files)} files")
    return lines


def _get_complexity_hotspots(hotspots: list[Any]) -> list[str]:
    """Extracts complexity hotspots."""
    lines = ["", "### Complexity Hotspots"]

    if not hotspots:
        return lines

    is_dict = isinstance(hotspots[0], dict)

    def get_file(x):
        return x["file"] if is_dict else getattr(x, "file", "")

    def get_name(x):
        return x["name"] if is_dict else getattr(x, "name", "")

    for h in hotspots[:5]:
        lines.append(f"- {get_file(h)}::{get_name(h)}")

    return lines


def summarize_for_prompt(index_result: Any, max_len: int = 4000) -> str:
    """
    Produces a condensed summary of the index specifically for the LLM System Prompt.
    Focuses on:
    - Global Metrics (LOC, Complexity)
    - Top 5 largest files
    - Top 5 most complex functions
    - Layer Architecture hints
    """
    idx = _normalize_input(index_result)

    summary_lines = []

    # 1. Project Stats
    summary_lines.extend(
        _get_project_stats(idx.get("files_scanned", 0), idx.get("global_metrics", {}))
    )

    # 2. Top Files
    summary_lines.extend(_get_top_files(idx.get("file_metrics", [])))

    # 3. Architecture Layers
    summary_lines.extend(_get_architecture_layers(idx.get("layers", {})))

    # 4. Complexity Hotspots
    summary_lines.extend(_get_complexity_hotspots(idx.get("complexity_hotspots_top50", [])))

    return "\n".join(summary_lines)


def _format_function_signature(func_node: Any) -> str:  # noqa: unused variable
    """Extracts a simple signature string."""
    return "func(...)"
