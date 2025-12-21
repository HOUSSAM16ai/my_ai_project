# app/services/duplication_buster.py
"""
SUPERHUMAN DUPLICATION BUSTER SERVICE
=====================================
Target 2: Code Duplication Solver.
Detects, Reports, and Suggests Unification for code duplicates.
"""

import ast
import hashlib
from collections import defaultdict
from pathlib import Path


class DuplicationBuster:
    def __init__(self, root: str = "app"):
        self.root = Path(root)
        self.hashes = defaultdict(list)

    def scan(self):
        """Scans the codebase for duplicate function bodies."""
        for path in self.root.rglob("*.py"):
            self._analyze_file(path)
        return self._generate_report()

    def _analyze_file(self, path: Path):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Normalize function name to ignore signature differences in name
                    # We want to catch identical bodies even if named differently
                    original_name = node.name
                    node.name = "placeholder"

                    # Hash the body to find structural duplicates
                    body_source = ast.unparse(node)
                    # Normalize whitespace
                    norm_source = "".join(body_source.split())
                    h = hashlib.md5(norm_source.encode()).hexdigest()
                    self.hashes[h].append((str(path), original_name))
        except Exception:
            pass

    def _generate_report(self):
        duplicates = {k: v for k, v in self.hashes.items() if len(v) > 1}
        report = []
        for h, occurences in duplicates.items():
            report.append(
                {
                    "hash": h,
                    "count": len(occurences),
                    "locations": occurences,
                    "suggestion": f"Refactor {occurences[0][1]} into a shared utility.",
                }
            )
        return sorted(report, key=lambda x: x["count"], reverse=True)


if __name__ == "__main__":
    buster = DuplicationBuster()
    results = buster.scan()
    print(f"Found {len(results)} duplication patterns.")
    for r in results[:5]:
        print(f"Pattern {r['hash'][:8]}: {r['count']} times")
        for loc in r["locations"]:
            print(f"  - {loc[0]}::{loc[1]}")
