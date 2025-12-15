#!/usr/bin/env python3
"""
Advanced Dead Code Detector
Filters out false positives:
- Public API functions (exported in __all__)
- Functions used in tests
- Functions used dynamically (getattr, etc.)
- Protocol/ABC methods
"""

import ast
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set, List


class AdvancedAnalyzer(ast.NodeVisitor):
    """Enhanced AST visitor"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.definitions: Set[str] = set()
        self.imports: Set[str] = set()
        self.calls: Set[str] = set()
        self.attributes: Set[str] = set()
        self.exported: Set[str] = set()  # __all__ exports
        self.is_abstract: Set[str] = set()  # ABC methods
        self.is_protocol: Set[str] = set()  # Protocol methods
        self.dynamic_usage: Set[str] = set()  # getattr, etc.
        
    def visit_FunctionDef(self, node):
        self.definitions.add(node.name)
        # Check for ABC decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ('abstractmethod', 'abstractproperty'):
                    self.is_abstract.add(node.name)
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        self.definitions.add(node.name)
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ('abstractmethod', 'abstractproperty'):
                    self.is_abstract.add(node.name)
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        self.definitions.add(node.name)
        # Check if it's a Protocol
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'Protocol':
                # All methods in Protocol are considered used
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.is_protocol.add(item.name)
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        # Check for __all__ = [...]
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '__all__':
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant):
                            self.exported.add(elt.value)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        # Track getattr, hasattr, etc. (dynamic usage)
        if isinstance(node.func, ast.Name):
            if node.func.id in ('getattr', 'hasattr', 'setattr', 'delattr'):
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    self.dynamic_usage.add(node.args[1].value)
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


class SmartDeadCodeDetector:
    """Smart detector that filters false positives"""
    
    def __init__(self, root_dir: str = "app", test_dir: str = "tests"):
        self.root_dir = root_dir
        self.test_dir = test_dir
        self.app_files: Dict[str, AdvancedAnalyzer] = {}
        self.test_files: Dict[str, AdvancedAnalyzer] = {}
        self.all_usages: Set[str] = set()
        self.test_usages: Set[str] = set()
        
    def analyze_file(self, filepath: str) -> AdvancedAnalyzer:
        """Analyze a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filepath)
                analyzer = AdvancedAnalyzer(filepath)
                analyzer.visit(tree)
                return analyzer
        except:
            return AdvancedAnalyzer(filepath)
    
    def scan_all(self):
        """Scan both app and test directories"""
        print(f"🔍 Scanning {self.root_dir}...")
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    analyzer = self.analyze_file(filepath)
                    self.app_files[filepath] = analyzer
                    self.all_usages.update(analyzer.calls)
                    self.all_usages.update(analyzer.attributes)
                    self.all_usages.update(analyzer.dynamic_usage)
        
        print(f"✅ Scanned {len(self.app_files)} app files")
        
        if os.path.exists(self.test_dir):
            print(f"🔍 Scanning {self.test_dir}...")
            for root, dirs, files in os.walk(self.test_dir):
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        analyzer = self.analyze_file(filepath)
                        self.test_files[filepath] = analyzer
                        self.test_usages.update(analyzer.calls)
                        self.test_usages.update(analyzer.attributes)
            
            print(f"✅ Scanned {len(self.test_files)} test files")
    
    def find_truly_dead_code(self) -> Dict[str, Set[str]]:
        """Find code that is truly dead (not false positives)"""
        dead_code = defaultdict(set)
        
        # Combine all usages (app + tests)
        all_usages = self.all_usages | self.test_usages
        
        for filepath, analyzer in self.app_files.items():
            for name in analyzer.definitions:
                # Skip private/magic methods
                if name.startswith('_'):
                    continue
                
                # Skip if exported in __all__
                if name in analyzer.exported:
                    continue
                
                # Skip abstract methods
                if name in analyzer.is_abstract:
                    continue
                
                # Skip protocol methods
                if name in analyzer.is_protocol:
                    continue
                
                # Skip if used anywhere
                if name in all_usages:
                    continue
                
                # This is truly dead code
                dead_code[filepath].add(name)
        
        return dead_code
    
    def generate_report(self) -> str:
        """Generate detailed report"""
        dead_code = self.find_truly_dead_code()
        total_dead = sum(len(v) for v in dead_code.values())
        
        report = []
        report.append("=" * 80)
        report.append("SMART DEAD CODE ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        report.append("📊 SUMMARY")
        report.append("-" * 80)
        report.append(f"App files analyzed: {len(self.app_files)}")
        report.append(f"Test files analyzed: {len(self.test_files)}")
        report.append(f"Total usages found: {len(self.all_usages | self.test_usages)}")
        report.append(f"Truly dead definitions: {total_dead}")
        report.append("")
        
        if dead_code:
            report.append("🔴 TRULY DEAD CODE (excluding false positives)")
            report.append("-" * 80)
            
            # Sort by number of dead items
            sorted_files = sorted(dead_code.items(), key=lambda x: len(x[1]), reverse=True)
            
            for filepath, names in sorted_files[:50]:  # Top 50
                if names:
                    report.append(f"\n{filepath} ({len(names)} dead):")
                    for name in sorted(names):
                        report.append(f"  - {name}")
            
            if len(sorted_files) > 50:
                remaining = sum(len(v) for k, v in sorted_files[50:])
                report.append(f"\n... and {len(sorted_files) - 50} more files with {remaining} dead definitions")
        else:
            report.append("✅ No truly dead code found!")
        
        report.append("")
        report.append("=" * 80)
        return "\n".join(report)


def main():
    print("🚀 Starting smart dead code analysis...")
    print()
    
    detector = SmartDeadCodeDetector("app", "tests")
    detector.scan_all()
    
    print()
    print("📝 Generating report...")
    report = detector.generate_report()
    
    print(report)
    
    # Save report
    with open("smart_dead_code_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print()
    print("✅ Report saved to: smart_dead_code_report.txt")
    
    dead_code = detector.find_truly_dead_code()
    if dead_code:
        print(f"⚠️  Found {sum(len(v) for v in dead_code.values())} truly dead definitions")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
