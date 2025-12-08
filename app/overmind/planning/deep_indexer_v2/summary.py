from typing import Any

from app.overmind.planning.deep_indexer_v2.core import IndexResult


def summarize_for_prompt(index_result: IndexResult, max_len: int = 4000) -> str:
    """
    Produces a condensed summary of the index specifically for the LLM System Prompt.
    Focuses on:
    - Global Metrics (LOC, Complexity)
    - Top 5 largest files
    - Top 5 most complex functions
    - Layer Architecture hints
    """
    g = index_result.global_metrics
    summary_lines = [
        "### Project Stats",
        f"- Total Files: {index_result.files_scanned}",
        f"- LOC={g.total_loc}, funcs={g.total_functions}, classes={g.total_classes}",
        f"- Complexity: avg={g.avg_function_complexity:.1f}, max={g.max_function_complexity}",
        "",
        "### Top Files (by LOC)",
    ]

    # Sort files by LOC desc
    sorted_files = sorted(index_result.file_metrics, key=lambda x: x.loc, reverse=True)[:5]
    for f in sorted_files:
        summary_lines.append(f"- {f.path} (loc={f.loc})")

    summary_lines.append("")
    summary_lines.append("### Architecture Layers")
    for layer, files in index_result.layers.items():
        if files:
            # Show just counts per layer
            summary_lines.append(f"- {layer.title()}: {len(files)} files")

    return "\n".join(summary_lines)


def _format_function_signature(func_node: Any) -> str:
    """Extracts a simple signature string."""
    # This is a placeholder. DeepIndexVisitor stores raw AST nodes usually,
    # or we might have stored name/args.
    # For now, let's assume we just print the name if we had it.
    return "func(...)"
