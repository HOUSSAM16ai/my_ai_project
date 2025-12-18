#!/usr/bin/env python3
"""
Documentation Verification Tool
Ensures every file, class, and function has clear purpose documentation.
"""
import ast
import json
from pathlib import Path
from typing import Any


def check_file_documentation(filepath: Path) -> dict[str, Any]:
    """Check if file has proper documentation."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(filepath))

        # Check module docstring
        module_docstring = ast.get_docstring(tree)
        
        # Find all classes and functions
        classes = []
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "has_docstring": bool(ast.get_docstring(node)),
                    "docstring": ast.get_docstring(node) or "",
                })
            elif isinstance(node, ast.FunctionDef):
                # Skip nested functions
                if node.col_offset == 0 or any(
                    isinstance(parent, ast.ClassDef) 
                    for parent in ast.walk(tree) 
                    if node in ast.walk(parent)
                ):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "has_docstring": bool(ast.get_docstring(node)),
                        "docstring": ast.get_docstring(node) or "",
                    })

        return {
            "file": str(filepath),
            "has_module_docstring": bool(module_docstring),
            "module_docstring": module_docstring or "",
            "classes": classes,
            "functions": functions,
            "total_classes": len(classes),
            "total_functions": len(functions),
            "classes_with_docstrings": sum(1 for c in classes if c["has_docstring"]),
            "functions_with_docstrings": sum(1 for f in functions if f["has_docstring"]),
        }
    except Exception as e:
        return {
            "file": str(filepath),
            "error": str(e),
        }


def verify_documentation(root_dir: str = "app") -> dict[str, Any]:
    """Verify documentation across entire codebase."""
    results = {
        "total_files": 0,
        "files_with_module_docstring": 0,
        "files_without_module_docstring": [],
        "total_classes": 0,
        "classes_with_docstrings": 0,
        "classes_without_docstrings": [],
        "total_functions": 0,
        "functions_with_docstrings": 0,
        "functions_without_docstrings": [],
        "files": [],
    }

    root_path = Path(root_dir)
    for py_file in sorted(root_path.rglob("*.py")):
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue

        file_result = check_file_documentation(py_file)
        results["files"].append(file_result)
        results["total_files"] += 1

        if file_result.get("has_module_docstring"):
            results["files_with_module_docstring"] += 1
        else:
            results["files_without_module_docstring"].append(str(py_file))

        results["total_classes"] += file_result.get("total_classes", 0)
        results["classes_with_docstrings"] += file_result.get("classes_with_docstrings", 0)

        results["total_functions"] += file_result.get("total_functions", 0)
        results["functions_with_docstrings"] += file_result.get("functions_with_docstrings", 0)

        # Track items without docstrings
        for cls in file_result.get("classes", []):
            if not cls["has_docstring"]:
                results["classes_without_docstrings"].append({
                    "file": str(py_file),
                    "class": cls["name"],
                    "line": cls["line"],
                })

        for func in file_result.get("functions", []):
            if not func["has_docstring"]:
                results["functions_without_docstrings"].append({
                    "file": str(py_file),
                    "function": func["name"],
                    "line": func["line"],
                })

    return results


def main():
    """Main execution."""
    print("📚 Documentation Verification")
    print("=" * 80)

    results = verify_documentation("app")

    # Calculate percentages
    module_doc_pct = (results["files_with_module_docstring"] / results["total_files"] * 100) if results["total_files"] > 0 else 0
    class_doc_pct = (results["classes_with_docstrings"] / results["total_classes"] * 100) if results["total_classes"] > 0 else 0
    func_doc_pct = (results["functions_with_docstrings"] / results["total_functions"] * 100) if results["total_functions"] > 0 else 0

    print(f"\n📊 Files: {results['total_files']}")
    print(f"  With module docstring: {results['files_with_module_docstring']} ({module_doc_pct:.1f}%)")
    print(f"  Without module docstring: {len(results['files_without_module_docstring'])}")

    print(f"\n🏛️  Classes: {results['total_classes']}")
    print(f"  With docstrings: {results['classes_with_docstrings']} ({class_doc_pct:.1f}%)")
    print(f"  Without docstrings: {len(results['classes_without_docstrings'])}")

    print(f"\n⚙️  Functions: {results['total_functions']}")
    print(f"  With docstrings: {results['functions_with_docstrings']} ({func_doc_pct:.1f}%)")
    print(f"  Without docstrings: {len(results['functions_without_docstrings'])}")

    # Overall documentation score
    total_items = results["total_files"] + results["total_classes"] + results["total_functions"]
    documented_items = (
        results["files_with_module_docstring"] +
        results["classes_with_docstrings"] +
        results["functions_with_docstrings"]
    )
    doc_score = (documented_items / total_items * 100) if total_items > 0 else 0

    print(f"\n🎯 Overall Documentation Score: {doc_score:.1f}%")

    if results["files_without_module_docstring"]:
        print(f"\n⚠️  Files without module docstring (showing first 10):")
        for filepath in results["files_without_module_docstring"][:10]:
            print(f"  - {filepath}")

    # Save report
    output_file = "documentation_report.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed report saved to: {output_file}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    main()
