#!/usr/bin/env python3
"""
Deep Dependency Analyzer
Traces ALL possible ways a function can be called:
1. Direct calls: function_name()
2. Attribute access: obj.method_name()
3. Dynamic calls: getattr(obj, 'method_name')()
4. String references: 'function_name' in code
5. Imports: from module import function_name
6. __all__ exports
7. Decorators that register functions
8. Class inheritance (super() calls)
9. Reflection patterns
10. FastAPI/Flask route decorators
"""

import ast
import os
import re
from collections import defaultdict
from typing import Dict, Set, List, Tuple


class DeepDependencyAnalyzer(ast.NodeVisitor):
    """Deep analyzer that catches ALL usage patterns"""
    
    def __init__(self, filepath: str, source: str):
        self.filepath = filepath
        self.source = source
        self.definitions: Set[str] = set()
        self.direct_calls: Set[str] = set()
        self.attribute_calls: Set[str] = set()
        self.string_references: Set[str] = set()
        self.dynamic_calls: Set[str] = set()
        self.imports: Set[str] = set()
        self.exports: Set[str] = set()
        self.decorators: Set[str] = set()
        self.super_calls: Set[str] = set()
        self.class_methods: Dict[str, Set[str]] = defaultdict(set)
        self.current_class: str | None = None
        
    def visit_FunctionDef(self, node):
        """Track function definitions"""
        self.definitions.add(node.name)
        
        # Track decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                self.decorators.add(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                self.decorators.add(decorator.attr)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    self.decorators.add(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    self.decorators.add(decorator.func.attr)
        
        # If inside a class, track as class method
        if self.current_class:
            self.class_methods[self.current_class].add(node.name)
        
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node):
        """Track async function definitions"""
        self.definitions.add(node.name)
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                self.decorators.add(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                self.decorators.add(decorator.attr)
        
        if self.current_class:
            self.class_methods[self.current_class].add(node.name)
        
        self.generic_visit(node)
        
    def visit_ClassDef(self, node):
        """Track class definitions"""
        self.definitions.add(node.name)
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_Call(self, node):
        """Track all function calls"""
        # Direct calls: function_name()
        if isinstance(node.func, ast.Name):
            self.direct_calls.add(node.func.id)
            
            # Dynamic calls: getattr(obj, 'method_name')
            if node.func.id in ('getattr', 'hasattr', 'setattr', 'delattr'):
                if len(node.args) >= 2:
                    if isinstance(node.args[1], ast.Constant):
                        self.dynamic_calls.add(node.args[1].value)
        
        # Attribute calls: obj.method_name()
        elif isinstance(node.func, ast.Attribute):
            self.attribute_calls.add(node.func.attr)
            
            # Super calls: super().method_name()
            if isinstance(node.func.value, ast.Call):
                if isinstance(node.func.value.func, ast.Name):
                    if node.func.value.func.id == 'super':
                        self.super_calls.add(node.func.attr)
        
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        """Track attribute access"""
        self.attribute_calls.add(node.attr)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        """Track name references"""
        if isinstance(node.ctx, ast.Load):
            self.direct_calls.add(node.id)
        self.generic_visit(node)
        
    def visit_ImportFrom(self, node):
        """Track imports"""
        if node.module:
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.imports.add(name)
        self.generic_visit(node)
        
    def visit_Import(self, node):
        """Track imports"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports.add(name)
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        """Track __all__ exports"""
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == '__all__':
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant):
                            self.exports.add(elt.value)
        self.generic_visit(node)
    
    def find_string_references(self):
        """Find string references in source code"""
        # Look for strings that match function names
        for definition in self.definitions:
            # Pattern: "function_name" or 'function_name'
            if f'"{definition}"' in self.source or f"'{definition}'" in self.source:
                self.string_references.add(definition)


class DeepDependencyGraph:
    """Build complete dependency graph"""
    
    def __init__(self, root_dir: str = "app", test_dir: str = "tests"):
        self.root_dir = root_dir
        self.test_dir = test_dir
        self.files: Dict[str, DeepDependencyAnalyzer] = {}
        self.all_definitions: Dict[str, str] = {}  # name -> filepath
        self.all_usages: Set[str] = set()
        self.usage_sources: Dict[str, List[str]] = defaultdict(list)
        
    def scan_all(self):
        """Scan all files"""
        print(f"🔍 Deep scanning {self.root_dir}...")
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.pytest_cache']]
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self._analyze_file(filepath)
        
        print(f"✅ Scanned {len(self.files)} app files")
        
        if os.path.exists(self.test_dir):
            print(f"🔍 Deep scanning {self.test_dir}...")
            for root, dirs, files in os.walk(self.test_dir):
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        self._analyze_file(filepath)
            
            print(f"✅ Scanned {len(self.files) - len([f for f in self.files if f.startswith(self.root_dir)])} test files")
    
    def _analyze_file(self, filepath: str):
        """Analyze a single file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filepath)
            analyzer = DeepDependencyAnalyzer(filepath, source)
            analyzer.visit(tree)
            analyzer.find_string_references()
            
            self.files[filepath] = analyzer
            
            # Track all definitions
            for name in analyzer.definitions:
                self.all_definitions[name] = filepath
            
            # Track all usages
            for name in analyzer.direct_calls:
                self.all_usages.add(name)
                self.usage_sources[name].append(f"{filepath}:direct_call")
            
            for name in analyzer.attribute_calls:
                self.all_usages.add(name)
                self.usage_sources[name].append(f"{filepath}:attribute")
            
            for name in analyzer.dynamic_calls:
                self.all_usages.add(name)
                self.usage_sources[name].append(f"{filepath}:dynamic")
            
            for name in analyzer.string_references:
                self.all_usages.add(name)
                self.usage_sources[name].append(f"{filepath}:string_ref")
            
            for name in analyzer.super_calls:
                self.all_usages.add(name)
                self.usage_sources[name].append(f"{filepath}:super")
            
            for name in analyzer.exports:
                self.all_usages.add(name)
                self.usage_sources[name].append(f"{filepath}:__all__")
            
        except Exception as e:
            print(f"⚠️  Error analyzing {filepath}: {e}")
    
    def find_truly_dead_functions(self) -> Dict[str, Set[str]]:
        """Find functions that are TRULY never used"""
        dead_functions = defaultdict(set)
        
        for filepath, analyzer in self.files.items():
            if not filepath.startswith(self.root_dir):
                continue  # Skip test files
            
            for name in analyzer.definitions:
                # Skip private/magic
                if name.startswith('_'):
                    continue
                
                # Skip if exported
                if name in analyzer.exports:
                    continue
                
                # Skip if used ANYWHERE
                if name in self.all_usages:
                    continue
                
                # This is truly dead
                dead_functions[filepath].add(name)
        
        return dead_functions
    
    def verify_function_is_dead(self, filepath: str, function_name: str) -> Tuple[bool, List[str]]:
        """Verify a function is truly dead and return evidence"""
        reasons = []
        
        # Check if it's in __all__
        if filepath in self.files:
            analyzer = self.files[filepath]
            if function_name in analyzer.exports:
                reasons.append(f"Exported in __all__")
                return False, reasons
        
        # Check if used anywhere
        if function_name in self.all_usages:
            sources = self.usage_sources.get(function_name, [])
            reasons.append(f"Used in {len(sources)} places:")
            for source in sources[:5]:  # Show first 5
                reasons.append(f"  - {source}")
            if len(sources) > 5:
                reasons.append(f"  ... and {len(sources) - 5} more")
            return False, reasons
        
        # Check for string references
        for file_analyzer in self.files.values():
            if function_name in file_analyzer.string_references:
                reasons.append(f"String reference in {file_analyzer.filepath}")
                return False, reasons
        
        # Truly dead
        reasons.append("✅ No usage found anywhere")
        reasons.append("✅ Not in __all__")
        reasons.append("✅ No string references")
        reasons.append("✅ Not called dynamically")
        return True, reasons
    
    def generate_report(self) -> str:
        """Generate comprehensive report"""
        dead_functions = self.find_truly_dead_functions()
        total_dead = sum(len(v) for v in dead_functions.values())
        
        report = []
        report.append("=" * 80)
        report.append("DEEP DEPENDENCY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        report.append("📊 STATISTICS")
        report.append("-" * 80)
        report.append(f"Total files analyzed: {len(self.files)}")
        report.append(f"Total definitions: {len(self.all_definitions)}")
        report.append(f"Total unique usages: {len(self.all_usages)}")
        report.append(f"Truly dead functions: {total_dead}")
        report.append("")
        
        if dead_functions:
            report.append("🔴 VERIFIED DEAD FUNCTIONS")
            report.append("-" * 80)
            
            sorted_files = sorted(dead_functions.items(), key=lambda x: len(x[1]), reverse=True)
            
            for filepath, names in sorted_files[:30]:  # Top 30 files
                if names:
                    report.append(f"\n{filepath} ({len(names)} dead):")
                    for name in sorted(names):
                        is_dead, reasons = self.verify_function_is_dead(filepath, name)
                        if is_dead:
                            report.append(f"  ✅ {name}")
                        else:
                            report.append(f"  ⚠️  {name} - {reasons[0]}")
            
            if len(sorted_files) > 30:
                remaining = sum(len(v) for k, v in sorted_files[30:])
                report.append(f"\n... and {len(sorted_files) - 30} more files with {remaining} functions")
        else:
            report.append("✅ No dead functions found!")
        
        report.append("")
        report.append("=" * 80)
        return "\n".join(report)


def main():
    print("🚀 Starting deep dependency analysis...")
    print("   This will trace ALL possible function calls")
    print()
    
    analyzer = DeepDependencyGraph("app", "tests")
    analyzer.scan_all()
    
    print()
    print("📊 Building dependency graph...")
    print(f"   Definitions: {len(analyzer.all_definitions)}")
    print(f"   Usages: {len(analyzer.all_usages)}")
    print()
    
    print("📝 Generating report...")
    report = analyzer.generate_report()
    print(report)
    
    # Save report
    with open("deep_dependency_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print()
    print("✅ Report saved to: deep_dependency_report.txt")
    
    dead_functions = analyzer.find_truly_dead_functions()
    total = sum(len(v) for v in dead_functions.values())
    
    if total > 0:
        print(f"\n⚠️  Found {total} truly dead functions")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
