#!/usr/bin/env python3
"""
أداة اكتشاف الكود الميت والملفات غير المستخدمة
Dead Code and Unused Files Detector

⚠️ CRITICAL: لا تلمس ملفات البيئة والـ DevContainer!
"""

import ast
from collections import defaultdict
from pathlib import Path

# ⚠️ PROTECTED FILES - DO NOT TOUCH!
PROTECTED_PATTERNS = [
    ".devcontainer",
    ".gitpod",
    "docker-compose",
    "Dockerfile",
    ".env",
    "entrypoint.sh",
    "setup_dev.sh",
    ".github/workflows",
    ".vscode",
    "requirements",
]


def is_protected(filepath: Path) -> bool:
    """Check if file is protected (dev environment related)."""
    path_str = str(filepath)
    return any(pattern in path_str for pattern in PROTECTED_PATTERNS)


class ImportAnalyzer(ast.NodeVisitor):
    """Analyze imports in a file."""

    def __init__(self):
        self.imports = set()
        self.from_imports = defaultdict(set)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.from_imports[node.module].add(alias.name)
        self.generic_visit(node)


class FunctionAnalyzer(ast.NodeVisitor):
    """Analyze function definitions."""

    def __init__(self):
        self.functions = set()
        self.classes = set()
        self.called_functions = set()

    def visit_FunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.classes.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        # Track function calls
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.called_functions.add(node.func.attr)
        self.generic_visit(node)


def analyze_file(filepath: Path) -> tuple[set, set, set]:
    """
    Analyze a Python file for defined and used functions.

    Returns:
        (defined_functions, called_functions, classes)
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))
        analyzer = FunctionAnalyzer()
        analyzer.visit(tree)

        return analyzer.functions, analyzer.called_functions, analyzer.classes

    except Exception:
        return set(), set(), set()


def find_dead_code():
    """Find dead code in the project."""

    app_dir = Path("app")
    tests_dir = Path("tests")

    print("🔍 Analyzing code for dead functions and files...\n")
    print("⚠️  PROTECTED: DevContainer and environment files are safe!\n")
    print("=" * 70)

    # Analyze all Python files
    all_defined = defaultdict(set)
    all_called = set()
    all_files = []

    for directory in [app_dir, tests_dir]:
        if not directory.exists():
            continue

        for filepath in directory.rglob("*.py"):
            if is_protected(filepath):
                continue

            all_files.append(filepath)
            defined, called, _classes = analyze_file(filepath)

            all_defined[filepath] = defined
            all_called.update(called)

    # Find dead functions (defined but never called)
    print("\n🪦 DEAD FUNCTIONS (defined but never called):")
    print("=" * 70)

    dead_functions = []
    for filepath, defined in all_defined.items():
        dead = defined - all_called
        # Exclude special methods and tests
        dead = {f for f in dead if not f.startswith("_") and not f.startswith("test_")}

        if dead:
            dead_functions.append((filepath, dead))

    if dead_functions:
        for filepath, funcs in sorted(dead_functions):
            print(f"\n📁 {filepath}")
            for func in sorted(funcs):
                print(f"   ❌ {func}()")
    else:
        print("✅ No dead functions found!")

    # Find potentially unused test files
    print("\n\n🧪 POTENTIALLY UNUSED TEST FILES:")
    print("=" * 70)

    test_files = list(tests_dir.rglob("*.py")) if tests_dir.exists() else []
    empty_tests = []

    for test_file in test_files:
        if is_protected(test_file):
            continue

        defined, _, _ = analyze_file(test_file)
        test_funcs = {f for f in defined if f.startswith("test_")}

        if not test_funcs:
            empty_tests.append(test_file)

    if empty_tests:
        for filepath in sorted(empty_tests):
            print(f"   ❌ {filepath} (no test functions)")
    else:
        print("✅ All test files have test functions!")

    # Find duplicate/redundant documentation files
    print("\n\n📄 REDUNDANT DOCUMENTATION FILES:")
    print("=" * 70)

    doc_files = list(Path(".").glob("*.md"))

    # Group by topic
    doc_topics = defaultdict(list)
    redundant_patterns = [
        "BROWSER_CRASH_FIX",
        "CODESPACES_",
        "IMPLEMENTATION_",
        "PHASE",
        "WAVE",
    ]

    for doc in doc_files:
        for pattern in redundant_patterns:
            if pattern in doc.name:
                doc_topics[pattern].append(doc)

    for topic, files in doc_topics.items():
        if len(files) > 1:
            print(f"\n📚 {topic}* files ({len(files)} files):")
            for f in sorted(files):
                print(f"   ⚠️  {f}")

    # Summary
    print("\n\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total files analyzed: {len(all_files)}")
    print(f"Dead functions found: {sum(len(funcs) for _, funcs in dead_functions)}")
    print(f"Empty test files: {len(empty_tests)}")
    print(f"Redundant doc groups: {len([g for g in doc_topics.values() if len(g) > 1])}")
    print("\n💡 TIP: Review these carefully before deleting!")
    print("=" * 70)

    return dead_functions, empty_tests


if __name__ == "__main__":
    find_dead_code()
