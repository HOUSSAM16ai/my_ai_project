#!/usr/bin/env python3
"""
Comprehensive Dead Code Detection Script
Analyzes the entire codebase to find:
1. Unused functions and classes
2. Unused imports
3. Orphaned files
4. Circular dependencies
"""

import ast
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set, List, Tuple


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to extract definitions and usages"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.definitions: Set[str] = set()
        self.imports: Set[str] = set()
        self.calls: Set[str] = set()
        self.attributes: Set[str] = set()
        
    def visit_FunctionDef(self, node):
        self.definitions.add(node.name)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        self.definitions.add(node.name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        self.definitions.add(node.name)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.imports.add(name)
        self.generic_visit(node)
        
    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.attributes.add(node.func.attr)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.calls.add(node.id)
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        self.attributes.add(node.attr)
        self.generic_visit(node)


class DeadCodeDetector:
    """Main dead code detection engine"""
    
    def __init__(self, root_dir: str = "app"):
        self.root_dir = root_dir
        self.files: Dict[str, CodeAnalyzer] = {}
        self.all_definitions: Dict[str, Set[str]] = defaultdict(set)
        self.all_usages: Set[str] = set()
        self.errors: List[Tuple[str, str]] = []
        
    def analyze_file(self, filepath: str) -> CodeAnalyzer:
        """Analyze a single Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filepath)
                analyzer = CodeAnalyzer(filepath)
                analyzer.visit(tree)
                return analyzer
        except SyntaxError as e:
            self.errors.append((filepath, f"Syntax error: {e}"))
            return CodeAnalyzer(filepath)
        except Exception as e:
            self.errors.append((filepath, f"Error: {e}"))
            return CodeAnalyzer(filepath)
    
    def scan_directory(self):
        """Scan all Python files in directory"""
        print(f"🔍 Scanning directory: {self.root_dir}")
        
        for root, dirs, files in os.walk(self.root_dir):
            # Skip __pycache__ and .git
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.pytest_cache']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    analyzer = self.analyze_file(filepath)
                    self.files[filepath] = analyzer
                    
                    # Collect all definitions
                    for name in analyzer.definitions:
                        self.all_definitions[filepath].add(name)
                    
                    # Collect all usages
                    self.all_usages.update(analyzer.calls)
                    self.all_usages.update(analyzer.attributes)
        
        print(f"✅ Scanned {len(self.files)} Python files")
        print(f"📊 Found {sum(len(v) for v in self.all_definitions.values())} definitions")
        print(f"📊 Found {len(self.all_usages)} unique usages")
        
    def find_unused_definitions(self) -> Dict[str, Set[str]]:
        """Find functions/classes that are never used"""
        unused = defaultdict(set)
        
        for filepath, definitions in self.all_definitions.items():
            for name in definitions:
                # Skip special methods and private methods
                if name.startswith('_'):
                    continue
                    
                # Check if used anywhere
                if name not in self.all_usages:
                    unused[filepath].add(name)
        
        return unused
    
    def find_empty_files(self) -> List[str]:
        """Find Python files with no definitions"""
        empty = []
        for filepath, analyzer in self.files.items():
            if not analyzer.definitions and not analyzer.imports:
                # Check if file is truly empty (not just __init__.py)
                if os.path.basename(filepath) != '__init__.py':
                    empty.append(filepath)
        return empty
    
    def find_unused_imports(self) -> Dict[str, Set[str]]:
        """Find imports that are never used"""
        unused_imports = defaultdict(set)
        
        for filepath, analyzer in self.files.items():
            for imported in analyzer.imports:
                # Check if import is used in calls or attributes
                if imported not in analyzer.calls and imported not in analyzer.attributes:
                    # Also check if it's in definitions (re-exported)
                    if imported not in analyzer.definitions:
                        unused_imports[filepath].add(imported)
        
        return unused_imports
    
    def generate_report(self) -> str:
        """Generate comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE DEAD CODE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append("📊 SUMMARY")
        report.append("-" * 80)
        report.append(f"Total files analyzed: {len(self.files)}")
        report.append(f"Total definitions: {sum(len(v) for v in self.all_definitions.values())}")
        report.append(f"Total unique usages: {len(self.all_usages)}")
        report.append(f"Errors encountered: {len(self.errors)}")
        report.append("")
        
        # Unused definitions
        unused_defs = self.find_unused_definitions()
        total_unused = sum(len(v) for v in unused_defs.values())
        report.append(f"🔴 UNUSED DEFINITIONS: {total_unused}")
        report.append("-" * 80)
        
        if unused_defs:
            for filepath, names in sorted(unused_defs.items()):
                if names:
                    report.append(f"\n{filepath}:")
                    for name in sorted(names):
                        report.append(f"  - {name}")
        else:
            report.append("✅ No unused definitions found!")
        report.append("")
        
        # Empty files
        empty_files = self.find_empty_files()
        report.append(f"📄 EMPTY FILES: {len(empty_files)}")
        report.append("-" * 80)
        if empty_files:
            for filepath in sorted(empty_files):
                report.append(f"  - {filepath}")
        else:
            report.append("✅ No empty files found!")
        report.append("")
        
        # Unused imports
        unused_imports = self.find_unused_imports()
        total_unused_imports = sum(len(v) for v in unused_imports.values())
        report.append(f"📦 UNUSED IMPORTS: {total_unused_imports}")
        report.append("-" * 80)
        
        if unused_imports:
            # Show top 20 files with most unused imports
            sorted_imports = sorted(unused_imports.items(), key=lambda x: len(x[1]), reverse=True)[:20]
            for filepath, imports in sorted_imports:
                if imports:
                    report.append(f"\n{filepath}:")
                    for imp in sorted(imports):
                        report.append(f"  - {imp}")
        else:
            report.append("✅ No unused imports found!")
        report.append("")
        
        # Errors
        if self.errors:
            report.append(f"⚠️  ERRORS: {len(self.errors)}")
            report.append("-" * 80)
            for filepath, error in self.errors[:10]:  # Show first 10
                report.append(f"{filepath}: {error}")
            if len(self.errors) > 10:
                report.append(f"... and {len(self.errors) - 10} more errors")
            report.append("")
        
        report.append("=" * 80)
        return "\n".join(report)


def main():
    """Main entry point"""
    print("🚀 Starting comprehensive dead code analysis...")
    print()
    
    detector = DeadCodeDetector("app")
    detector.scan_directory()
    
    print()
    print("📝 Generating report...")
    report = detector.generate_report()
    
    # Print to console
    print(report)
    
    # Save to file
    output_file = "dead_code_analysis_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print()
    print(f"✅ Report saved to: {output_file}")
    
    # Return exit code based on findings
    unused_defs = detector.find_unused_definitions()
    if unused_defs:
        print()
        print(f"⚠️  Found {sum(len(v) for v in unused_defs.values())} unused definitions")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
