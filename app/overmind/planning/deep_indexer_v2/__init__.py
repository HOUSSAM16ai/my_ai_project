"""
Deep Indexer V2 - The Eye of Overmind.
Scans the codebase to produce a concise 'Cognitive Map' (summary).
"""
import os
import ast
from typing import List, Dict

IGNORED_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "node_modules", "dist", "build", "migrations"
}
IGNORED_FILES = {
    "poetry.lock", "package-lock.json", ".DS_Store"
}

def build_index(root: str = ".", internal_prefixes=("app",)) -> Dict:
    """
    Scans the directory tree and builds a structural index.
    Returns a dictionary representing the codebase structure.
    """
    index = {
        "files": [],
        "classes": [],
        "functions": [],
        "stats": {"py_files": 0, "total_lines": 0}
    }

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter directories
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        for f in filenames:
            if f in IGNORED_FILES:
                continue

            path = os.path.join(dirpath, f)
            rel_path = os.path.relpath(path, root)

            if f.endswith(".py"):
                index["stats"]["py_files"] += 1
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        content = file.read()
                        lines = content.splitlines()
                        index["stats"]["total_lines"] += len(lines)

                        # AST Analysis
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                index["classes"].append(f"{rel_path}::{node.name}")
                            elif isinstance(node, ast.FunctionDef):
                                # Only top-level or method (simple heuristic)
                                index["functions"].append(f"{rel_path}::{node.name}")

                    index["files"].append(f"{rel_path} ({len(lines)} lines)")
                except Exception:
                    index["files"].append(f"{rel_path} (error reading)")
            else:
                index["files"].append(rel_path)

    return index

def summarize_for_prompt(index: Dict, max_len: int = 4000) -> str:
    """
    Converts the index dictionary into a text summary suitable for LLM context.
    """
    summary = []
    summary.append(f"Stats: {index['stats']['py_files']} Python files, {index['stats']['total_lines']} LoC.")

    summary.append("\nCore Modules:")
    # Prioritize 'app/core' and 'app/services'
    core_files = [f for f in index["files"] if "app/core" in f][:15]
    service_files = [f for f in index["files"] if "app/services" in f][:15]

    summary.extend([f"- {f}" for f in core_files])
    summary.extend([f"- {f}" for f in service_files])

    summary.append("\nKey Classes:")
    # Pick first 20 classes
    summary.extend([f"- {c}" for c in index["classes"][:20]])

    result = "\n".join(summary)
    if len(result) > max_len:
        return result[:max_len] + "\n...(truncated)"
    return result
