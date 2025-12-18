from collections import Counter, defaultdict

from .config import CONFIG
from .models import FileModule


def build_call_graph(
    modules: list[FileModule],
) -> tuple[list[tuple[str, str, str, str]], Counter]:
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


def build_dependencies(
    modules: list[FileModule], internal_prefixes: tuple[str, ...]
) -> dict[str, list[str]]:
    dep_graph = defaultdict(set)
    for m in modules:
        for imp in m.imports:
            if imp.startswith(internal_prefixes):
                dep_graph[m.path].add(imp)
    return {k: sorted(v) for k, v in dep_graph.items()}
