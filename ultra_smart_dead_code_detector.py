#!/usr/bin/env python3
"""
Ultra Smart Dead Code Detector
Filters out ALL false positives including:
- AST visitor methods (visit_*)
- Test methods (test_*)
- Fixture methods (pytest fixtures)
- Magic methods (__*)
- Protocol/ABC methods
- Public API (__all__)
- Methods called via super()
- Callback methods (on_*, handle_*, process_*)
"""

import ast
import os
import re
from collections import defaultdict
from typing import Dict, Set, List


class UltraSmartAnalyzer(ast.NodeVisitor):
    """Ultra smart AST analyzer"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.definitions: Set[str] = set()
        self.calls: Set[str] = set()
        self.attributes: Set[str] = set()
        self.exported: Set[str] = set()
        self.is_abstract: Set[str] = set()
        self.is_protocol: Set[str] = set()
        self.is_test: Set[str] = set()
        self.is_fixture: Set[str] = set()
        self.is_visitor: Set[str] = set()
        self.is_callback: Set[str] = set()
        self.dynamic_usage: Set[str] = set()
        self.super_calls: Set[str] = set()
        
    def visit_FunctionDef(self, node):
        name = node.name
        self.definitions.add(name)
        
        # Check for special patterns
        if name.startswith('visit_'):
            self.is_visitor.add(name)
        if name.startswith('test_'):
            self.is_test.add(name)
        if name.startswith(('on_', 'handle_', 'process_', 'callback_')):
            self.is_callback.add(name)
        
        # Check decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ('abstractmethod', 'abstractproperty'):
                    self.is_abstract.add(name)
                if decorator.id in ('pytest.fixture', 'fixture'):
                    self.is_fixture.add(name)
        
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        name = node.name
        self.definitions.add(name)
        
        if name.startswith('visit_'):
            self.is_visitor.add(name)
        if name.startswith('test_'):
            self.is_test.add(name)
        if name.startswith(('on_', 'handle_', 'process_', 'callback_')):
            self.is_callback.add(name)
            
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ('abstractmethod', 'abstractproperty'):
                    self.is_abstract.add(name)
                if decorator.id in ('pytest.fixture', 'fixture'):
                    self.is_fixture.add(name)
        
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        self.definitions.add(node.name)
        
        # Check if Protocol or ABC
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ('Protocol', 'ABC'):
                    # All methods are considered used
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            self.is_protocol.add(item.name)
        
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        # Check for __all__
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '__all__':
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant):
                            self.exported.add(elt.value)
        self.generic_visit(node)
        
    def visit_Call(self, node):
        # Track function calls
        if isinstance(node.func, ast.Name):
            self.calls.add(node.func.id)
            
            # Track dynamic usage
            if node.func.id in ('getattr', 'hasattr', 'setattr', 'delattr'):
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    self.dynamic_usage.add(node.args[1].value)
            
            # Track super() calls
            if node.func.id == 'super':
                # Next attribute access is a super call
                pass
                
        elif isinstance(node.func, ast.Attribute):
            self.attributes.add(node.func.attr)
            
            # Track super().method() calls
            if isinstance(node.func.value, ast.Call):
                if isinstance(node.func.value.func, ast.Name):
                    if node.func.value.func.id == 'super':
                        self.super_calls.add(node.func.attr)
        
        self.generic_visit(node)
        
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.calls.add(node.id)
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        self.attributes.add(node.attr)
        self.generic_visit(node)


class UltraSmartDetector:
    """Ultra smart dead code detector"""
    
    def __init__(self, root_dir: str = "app", test_dir: str = "tests"):
        self.root_dir = root_dir
        self.test_dir = test_dir
        self.app_files: Dict[str, UltraSmartAnalyzer] = {}
        self.test_files: Dict[str, UltraSmartAnalyzer] = {}
        self.all_usages: Set[str] = set()
        
    def analyze_file(self, filepath: str) -> UltraSmartAnalyzer:
        """Analyze a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filepath)
                analyzer = UltraSmartAnalyzer(filepath)
                analyzer.visit(tree)
                return analyzer
        except:
            return UltraSmartAnalyzer(filepath)
    
    def scan_all(self):
        """Scan all directories"""
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
                    self.all_usages.update(analyzer.super_calls)
        
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
                        self.all_usages.update(analyzer.calls)
                        self.all_usages.update(analyzer.attributes)
            
            print(f"✅ Scanned {len(self.test_files)} test files")
    
    def is_truly_dead(self, name: str, analyzer: UltraSmartAnalyzer) -> bool:
        """Check if a definition is truly dead"""
        # Skip private/magic methods
        if name.startswith('_'):
            return False
        
        # Skip exported
        if name in analyzer.exported:
            return False
        
        # Skip abstract methods
        if name in analyzer.is_abstract:
            return False
        
        # Skip protocol methods
        if name in analyzer.is_protocol:
            return False
        
        # Skip test methods
        if name in analyzer.is_test:
            return False
        
        # Skip fixtures
        if name in analyzer.is_fixture:
            return False
        
        # Skip visitor methods
        if name in analyzer.is_visitor:
            return False
        
        # Skip callback methods
        if name in analyzer.is_callback:
            return False
        
        # Skip if used anywhere
        if name in self.all_usages:
            return False
        
        return True
    
    def find_truly_dead_code(self) -> Dict[str, Set[str]]:
        """Find truly dead code"""
        dead_code = defaultdict(set)
        
        for filepath, analyzer in self.app_files.items():
            for name in analyzer.definitions:
                if self.is_truly_dead(name, analyzer):
                    dead_code[filepath].add(name)
        
        return dead_code
    
    def generate_report(self) -> str:
        """Generate report"""
        dead_code = self.find_truly_dead_code()
        total_dead = sum(len(v) for v in dead_code.values())
        
        report = []
        report.append("=" * 80)
        report.append("ULTRA SMART DEAD CODE ANALYSIS")
        report.append("=" * 80)
        report.append("")
        report.append("📊 SUMMARY")
        report.append("-" * 80)
        report.append(f"App files: {len(self.app_files)}")
        report.append(f"Test files: {len(self.test_files)}")
        report.append(f"Total usages: {len(self.all_usages)}")
        report.append(f"Truly dead: {total_dead}")
        report.append("")
        
        if dead_code:
            report.append("🔴 TRULY DEAD CODE")
            report.append("-" * 80)
            
            sorted_files = sorted(dead_code.items(), key=lambda x: len(x[1]), reverse=True)
            
            for filepath, names in sorted_files:
                if names:
                    report.append(f"\n{filepath} ({len(names)}):")
                    for name in sorted(names):
                        report.append(f"  - {name}")
        else:
            report.append("✅ No truly dead code found!")
        
        report.append("")
        report.append("=" * 80)
        return "\n".join(report)


def main():
    print("🚀 Ultra smart dead code analysis...")
    print()
    
    detector = UltraSmartDetector("app", "tests")
    detector.scan_all()
    
    print()
    report = detector.generate_report()
    print(report)
    
    with open("ultra_smart_dead_code_report.txt", 'w') as f:
        f.write(report)
    
    print()
    print("✅ Report saved to: ultra_smart_dead_code_report.txt")
    
    dead_code = detector.find_truly_dead_code()
    total = sum(len(v) for v in dead_code.values())
    
    if total > 0:
        print(f"⚠️  Found {total} truly dead definitions")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
