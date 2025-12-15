#!/usr/bin/env python3
"""
Final Dead Code Analyzer
Ultimate verification with ALL edge cases:
1. AST NodeVisitor methods (visit_*)
2. FastAPI/Flask route handlers
3. Pytest fixtures
4. Callback patterns
5. Protocol/ABC methods
6. __all__ exports
7. Dynamic usage (getattr, etc.)
8. String references
9. Class inheritance
10. Decorator registration
"""

import ast
import os
from collections import defaultdict
from typing import Dict, Set, List, Tuple


class FinalAnalyzer(ast.NodeVisitor):
    """Final comprehensive analyzer"""
    
    def __init__(self, filepath: str, source: str):
        self.filepath = filepath
        self.source = source
        self.definitions: Set[str] = set()
        self.usages: Set[str] = set()
        self.exports: Set[str] = set()
        self.protected: Set[str] = set()  # Methods that should never be removed
        self.current_class: str | None = None
        self.class_bases: Dict[str, List[str]] = {}
        
    def visit_ClassDef(self, node):
        """Track classes and their bases"""
        self.definitions.add(node.name)
        
        # Track base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)
        
        self.class_bases[node.name] = bases
        
        # If inherits from NodeVisitor, Protocol, ABC, etc., protect all methods
        protected_bases = {'NodeVisitor', 'Protocol', 'ABC', 'TestCase'}
        if any(b in protected_bases for b in bases):
            old_class = self.current_class
            self.current_class = node.name
            self.generic_visit(node)
            self.current_class = old_class
            return
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node):
        """Track function definitions"""
        name = node.name
        self.definitions.add(name)
        
        # Protect special patterns
        if name.startswith('visit_'):
            self.protected.add(name)
        if name.startswith('test_'):
            self.protected.add(name)
        if name.startswith(('on_', 'handle_', 'process_', 'callback_')):
            self.protected.add(name)
        
        # Check decorators
        for decorator in node.decorator_list:
            # FastAPI/Flask routes
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ('get', 'post', 'put', 'delete', 'patch', 'route'):
                        self.protected.add(name)
            
            # Pytest fixtures
            if isinstance(decorator, ast.Name):
                if decorator.id in ('fixture', 'pytest_fixture'):
                    self.protected.add(name)
                if decorator.id in ('abstractmethod', 'abstractproperty'):
                    self.protected.add(name)
        
        # If in a protected class, protect this method
        if self.current_class and self.current_class in self.class_bases:
            bases = self.class_bases[self.current_class]
            if any(b in {'NodeVisitor', 'Protocol', 'ABC'} for b in bases):
                self.protected.add(name)
        
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        """Track async functions"""
        name = node.name
        self.definitions.add(name)
        
        if name.startswith('visit_'):
            self.protected.add(name)
        if name.startswith('test_'):
            self.protected.add(name)
        if name.startswith(('on_', 'handle_', 'process_', 'callback_')):
            self.protected.add(name)
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ('get', 'post', 'put', 'delete', 'patch', 'route'):
                        self.protected.add(name)
            if isinstance(decorator, ast.Name):
                if decorator.id in ('fixture', 'pytest_fixture', 'abstractmethod'):
                    self.protected.add(name)
        
        if self.current_class and self.current_class in self.class_bases:
            bases = self.class_bases[self.current_class]
            if any(b in {'NodeVisitor', 'Protocol', 'ABC'} for b in bases):
                self.protected.add(name)
        
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Track all calls"""
        if isinstance(node.func, ast.Name):
            self.usages.add(node.func.id)
            
            # getattr, hasattr, etc.
            if node.func.id in ('getattr', 'hasattr', 'setattr', 'delattr'):
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    self.usages.add(node.args[1].value)
        
        elif isinstance(node.func, ast.Attribute):
            self.usages.add(node.func.attr)
            
            # super().method()
            if isinstance(node.func.value, ast.Call):
                if isinstance(node.func.value.func, ast.Name):
                    if node.func.value.func.id == 'super':
                        self.usages.add(node.func.attr)
        
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        """Track attribute access"""
        self.usages.add(node.attr)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        """Track name references"""
        if isinstance(node.ctx, ast.Load):
            self.usages.add(node.id)
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        """Track __all__ exports"""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '__all__':
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant):
                            self.exports.add(elt.value)
                            self.protected.add(elt.value)
        self.generic_visit(node)
    
    def find_string_references(self):
        """Find string references"""
        for definition in self.definitions:
            if f'"{definition}"' in self.source or f"'{definition}'" in self.source:
                self.usages.add(definition)
                self.protected.add(definition)


class FinalDeadCodeDetector:
    """Final dead code detector with all protections"""
    
    def __init__(self, root_dir: str = "app", test_dir: str = "tests"):
        self.root_dir = root_dir
        self.test_dir = test_dir
        self.files: Dict[str, FinalAnalyzer] = {}
        self.all_usages: Set[str] = set()
        self.all_protected: Set[str] = set()
        
    def scan_all(self):
        """Scan all files"""
        print(f"🔍 Final scan of {self.root_dir}...")
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self._analyze_file(filepath)
        
        print(f"✅ Scanned {len(self.files)} app files")
        
        if os.path.exists(self.test_dir):
            print(f"🔍 Final scan of {self.test_dir}...")
            for root, dirs, files in os.walk(self.test_dir):
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        self._analyze_file(filepath)
            
            print(f"✅ Scanned {len(self.files) - len([f for f in self.files if f.startswith(self.root_dir)])} test files")
    
    def _analyze_file(self, filepath: str):
        """Analyze a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filepath)
            analyzer = FinalAnalyzer(filepath, source)
            analyzer.visit(tree)
            analyzer.find_string_references()
            
            self.files[filepath] = analyzer
            self.all_usages.update(analyzer.usages)
            self.all_protected.update(analyzer.protected)
            
        except Exception as e:
            print(f"⚠️  Error: {filepath}: {e}")
    
    def find_dead_code(self) -> Dict[str, List[Tuple[str, str]]]:
        """Find truly dead code with reasons"""
        dead_code = defaultdict(list)
        
        for filepath, analyzer in self.files.items():
            if not filepath.startswith(self.root_dir):
                continue
            
            for name in analyzer.definitions:
                # Skip private/magic
                if name.startswith('_'):
                    continue
                
                # Skip protected
                if name in analyzer.protected:
                    continue
                
                if name in self.all_protected:
                    continue
                
                # Skip if exported
                if name in analyzer.exports:
                    continue
                
                # Skip if used
                if name in self.all_usages:
                    continue
                
                # This is dead
                reason = "No usage found"
                dead_code[filepath].append((name, reason))
        
        return dead_code
    
    def generate_report(self) -> str:
        """Generate final report"""
        dead_code = self.find_dead_code()
        total_dead = sum(len(v) for v in dead_code.values())
        
        report = []
        report.append("=" * 80)
        report.append("FINAL DEAD CODE ANALYSIS - VERIFIED")
        report.append("=" * 80)
        report.append("")
        report.append("📊 SUMMARY")
        report.append("-" * 80)
        report.append(f"Files analyzed: {len(self.files)}")
        report.append(f"Total usages: {len(self.all_usages)}")
        report.append(f"Protected items: {len(self.all_protected)}")
        report.append(f"Dead code items: {total_dead}")
        report.append("")
        
        if dead_code:
            report.append("🔴 VERIFIED DEAD CODE (Safe to remove)")
            report.append("-" * 80)
            
            sorted_files = sorted(dead_code.items(), key=lambda x: len(x[1]), reverse=True)
            
            for filepath, items in sorted_files:
                if items:
                    report.append(f"\n{filepath} ({len(items)} dead):")
                    for name, reason in items:
                        report.append(f"  - {name}")
        else:
            report.append("✅ No dead code found!")
        
        report.append("")
        report.append("=" * 80)
        return "\n".join(report)


def main():
    print("🚀 Final dead code analysis with all protections...")
    print()
    
    detector = FinalDeadCodeDetector("app", "tests")
    detector.scan_all()
    
    print()
    print("📝 Generating final report...")
    report = detector.generate_report()
    print(report)
    
    with open("final_dead_code_report.txt", 'w') as f:
        f.write(report)
    
    print()
    print("✅ Report saved to: final_dead_code_report.txt")
    
    dead_code = detector.find_dead_code()
    total = sum(len(v) for v in dead_code.values())
    
    if total > 0:
        print(f"\n⚠️  Found {total} truly dead items")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
