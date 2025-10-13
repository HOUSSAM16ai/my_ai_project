# app/cli/graph.py - The Code Structure Analyzer

from __future__ import annotations

import ast
import re
from pathlib import Path


def list_py_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*.py"):
        if any(
            part in {".git", ".venv", "venv", "__pycache__", "node_modules"} for part in p.parts
        ):
            continue
        files.append(p)
    return files


def find_symbol(root: Path, name: str) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for p in list_py_files(root):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name == name
            ):
                hits.append((p, node.lineno, type(node).__name__))
    return hits


def import_graph(root: Path) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = {}
    for p in list_py_files(root):
        mod = str(p.with_suffix("")).replace(str(root) + "/", "").replace("/", ".")
        graph.setdefault(mod, [])
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    graph[mod].append(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    graph[mod].append(node.module.split(".")[0])
    return graph


def find_routes(root: Path) -> list[tuple[str, str, str]]:
    routes: list[tuple[str, str, str]] = []
    patterns = [
        r"@(?:[a-zA-Z_][\w\.]*)\.route\(['\"]([^'\"]+)['\"].*?\)\s*def\s+([a-zA-Z_]\w*)",
        r"@(?:[a-zA-Z_][\w\.]*)\.(get|post|put|patch|delete)\(['\"]([^'\"]+)['\"].*?\)\s*def\s+([a-zA-Z_]\w*)",
    ]
    regexes = [re.compile(p, re.S) for p in patterns]
    for p in list_py_files(root):
        try:
            src = p.read_text(encoding="utf-8")
        except Exception:
            continue
        for rx in regexes:
            for m in rx.finditer(src):
                if "route" in rx.pattern:
                    routes.append(("FLASK", m.group(1), f"{p}:{m.group(2)}"))
                else:
                    routes.append((m.group(1).upper(), m.group(2), f"{p}:{m.group(3)}"))
    return routes
