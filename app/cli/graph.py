# app/cli/graph.py - The Code Structure Analyzer

from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
import ast
import re

def list_py_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob("*.py"):
        if any(part in {".git", ".venv", "venv", "__pycache__", "node_modules"} for part in p.parts):
            continue
        files.append(p)
    return files

def find_symbol(root: Path, name: str) -> List[Tuple[Path, int, str]]:
    hits: List[Tuple[Path, int, str]] = []
    for p in list_py_files(root):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
                hits.append((p, node.lineno, type(node).__name__))
    return hits

def import_graph(root: Path) -> Dict[str, List[str]]:
    graph: Dict[str, List[str]] = {}
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

def find_routes(root: Path) -> List[Tuple[str, str, str]]:
    routes: List[Tuple[str, str, str]] = []
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