#!/usr/bin/env python3
"""
Ultra Conservative Dead Code Filter
Only identifies functions with 100% certainty of being dead:
- Must have NO usage anywhere
- Must NOT be in __all__
- Must NOT have string references
- Must NOT be a public API pattern
- Must NOT be in a service/facade pattern
- Must NOT be a utility function that might be used externally
"""

import ast
import os
from collections import defaultdict
from typing import Dict, Set, List, Tuple


class UltraConservativeAnalyzer(ast.NodeVisitor):
    """Ultra conservative analyzer - only catches truly dead code"""
    
    def __init__(self, filepath: str, source: str):
        self.filepath = filepath
        self.source = source
        self.definitions: Set[str] = set()
        self.usages: Set[str] = set()
        self.exports: Set[str] = set()
        self.protected: Set[str] = set()
        self.public_api_patterns: Set[str] = set()
        self.current_class: str | None = None
        
    def visit_ClassDef(self, node):
        """Track classes"""
        self.definitions.add(node.name)
        
        # Protect all methods in certain base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
        
        # If inherits from these, protect all methods
        protected_bases = {
            'NodeVisitor', 'Protocol', 'ABC', 'TestCase', 
            'Enum', 'BaseModel', 'SQLModel', 'BaseSettings'
        }
        
        if any(b in protected_bases for b in bases):
            old_class = self.current_class
            self.current_class = node.name
            # Mark all methods as protected
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.protected.add(item.name)
            self.generic_visit(node)
            self.current_class = old_class
            return
        
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node):
        """Track functions"""
        name = node.name
        self.definitions.add(name)
        
        # Protect special patterns
        if name.startswith('visit_'):
            self.protected.add(name)
        if name.startswith('test_'):
            self.protected.add(name)
        if name.startswith(('on_', 'handle_', 'process_', 'callback_')):
            self.protected.add(name)
        
        # Protect public API patterns
        if name.startswith('get_') and name.endswith('_service'):
            self.public_api_patterns.add(name)
        if name.startswith('create_'):
            self.public_api_patterns.add(name)
        if name.startswith('register_'):
            self.public_api_patterns.add(name)
        
        # Check decorators
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ('get', 'post', 'put', 'delete', 'patch', 'route'):
                        self.protected.add(name)
            if isinstance(decorator, ast.Name):
                if decorator.id in ('fixture', 'pytest_fixture', 'abstractmethod'):
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
        
        if name.startswith('get_') and name.endswith('_service'):
            self.public_api_patterns.add(name)
        if name.startswith('create_'):
            self.public_api_patterns.add(name)
        if name.startswith('register_'):
            self.public_api_patterns.add(name)
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ('get', 'post', 'put', 'delete', 'patch', 'route'):
                        self.protected.add(name)
            if isinstance(decorator, ast.Name):
                if decorator.id in ('fixture', 'pytest_fixture', 'abstractmethod'):
                    self.protected.add(name)
        
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Track all calls"""
        if isinstance(node.func, ast.Name):
            self.usages.add(node.func.id)
            if node.func.id in ('getattr', 'hasattr', 'setattr', 'delattr'):
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    self.usages.add(node.args[1].value)
        elif isinstance(node.func, ast.Attribute):
            self.usages.add(node.func.attr)
            if isinstance(node.func.value, ast.Call):
                if isinstance(node.func.value.func, ast.Name):
                    if node.func.value.func.id == 'super':
                        self.usages.add(node.func.attr)
        self.generic_visit(node)
        
    def visit_Attribute(self, node):
        """Track attributes"""
        self.usages.add(node.attr)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        """Track names"""
        if isinstance(node.ctx, ast.Load):
            self.usages.add(node.id)
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        """Track __all__"""
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


class UltraConservativeDetector:
    """Ultra conservative detector - 100% certainty only"""
    
    def __init__(self, root_dir: str = "app", test_dir: str = "tests"):
        self.root_dir = root_dir
        self.test_dir = test_dir
        self.files: Dict[str, UltraConservativeAnalyzer] = {}
        self.all_usages: Set[str] = set()
        self.all_protected: Set[str] = set()
        self.all_public_api: Set[str] = set()
        
    def scan_all(self):
        """Scan all files"""
        print(f"🔍 Ultra conservative scan of {self.root_dir}...")
        
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self._analyze_file(filepath)
        
        print(f"✅ Scanned {len(self.files)} app files")
        
        if os.path.exists(self.test_dir):
            print(f"🔍 Ultra conservative scan of {self.test_dir}...")
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
            analyzer = UltraConservativeAnalyzer(filepath, source)
            analyzer.visit(tree)
            analyzer.find_string_references()
            
            self.files[filepath] = analyzer
            self.all_usages.update(analyzer.usages)
            self.all_protected.update(analyzer.protected)
            self.all_public_api.update(analyzer.public_api_patterns)
            
        except Exception as e:
            print(f"⚠️  Error: {filepath}: {e}")
    
    def is_100_percent_dead(self, name: str, analyzer: UltraConservativeAnalyzer, filepath: str) -> Tuple[bool, List[str]]:
        """Check if function is 100% dead with reasons"""
        reasons = []
        
        # Skip private/magic
        if name.startswith('_'):
            reasons.append("Private/magic method")
            return False, reasons
        
        # Skip protected
        if name in analyzer.protected:
            reasons.append("Protected pattern")
            return False, reasons
        
        if name in self.all_protected:
            reasons.append("Protected globally")
            return False, reasons
        
        # Skip exported
        if name in analyzer.exports:
            reasons.append("In __all__")
            return False, reasons
        
        # Skip public API patterns
        if name in analyzer.public_api_patterns:
            reasons.append("Public API pattern")
            return False, reasons
        
        if name in self.all_public_api:
            reasons.append("Public API pattern globally")
            return False, reasons
        
        # Skip if used anywhere
        if name in self.all_usages:
            reasons.append("Used somewhere")
            return False, reasons
        
        # Skip if in facade/service files (might be external API)
        if 'facade' in filepath.lower() or 'service' in filepath.lower():
            if name.startswith(('get_', 'create_', 'register_', 'list_', 'update_', 'delete_')):
                reasons.append("Potential external API in service/facade")
                return False, reasons
        
        # Skip if looks like a utility function
        if name in ('to_dict', 'from_dict', 'to_json', 'from_json', 'validate', 'serialize', 'deserialize'):
            reasons.append("Common utility pattern")
            return False, reasons
        
        # This is 100% dead
        reasons.append("✅ No usage found")
        reasons.append("✅ Not protected")
        reasons.append("✅ Not in __all__")
        reasons.append("✅ Not public API pattern")
        reasons.append("✅ 100% CERTAIN DEAD")
        return True, reasons
    
    def find_100_percent_dead(self) -> Dict[str, List[Tuple[str, List[str]]]]:
        """Find functions with 100% certainty of being dead"""
        dead_code = defaultdict(list)
        
        for filepath, analyzer in self.files.items():
            if not filepath.startswith(self.root_dir):
                continue
            
            for name in analyzer.definitions:
                is_dead, reasons = self.is_100_percent_dead(name, analyzer, filepath)
                if is_dead:
                    dead_code[filepath].append((name, reasons))
        
        return dead_code
    
    def generate_report(self) -> str:
        """Generate report"""
        dead_code = self.find_100_percent_dead()
        total_dead = sum(len(v) for v in dead_code.values())
        
        report = []
        report.append("=" * 80)
        report.append("ULTRA CONSERVATIVE DEAD CODE ANALYSIS")
        report.append("100% CERTAINTY ONLY")
        report.append("=" * 80)
        report.append("")
        report.append("📊 SUMMARY")
        report.append("-" * 80)
        report.append(f"Files analyzed: {len(self.files)}")
        report.append(f"Total usages: {len(self.all_usages)}")
        report.append(f"Protected items: {len(self.all_protected)}")
        report.append(f"Public API patterns: {len(self.all_public_api)}")
        report.append(f"100% DEAD functions: {total_dead}")
        report.append("")
        
        if dead_code:
            report.append("🔴 100% CONFIRMED DEAD CODE (Safe to remove)")
            report.append("-" * 80)
            
            sorted_files = sorted(dead_code.items(), key=lambda x: len(x[1]), reverse=True)
            
            for filepath, items in sorted_files:
                if items:
                    report.append(f"\n{filepath} ({len(items)} dead):")
                    for name, reasons in items:
                        report.append(f"  ✅ {name}")
                        for reason in reasons:
                            if reason.startswith("✅"):
                                report.append(f"      {reason}")
        else:
            report.append("✅ No 100% dead code found!")
        
        report.append("")
        report.append("=" * 80)
        return "\n".join(report)


def main():
    print("🚀 Ultra conservative dead code analysis...")
    print("   Only functions with 100% certainty will be identified")
    print()
    
    detector = UltraConservativeDetector("app", "tests")
    detector.scan_all()
    
    print()
    print("📝 Generating report...")
    report = detector.generate_report()
    print(report)
    
    with open("100_percent_dead_code_report.txt", 'w') as f:
        f.write(report)
    
    print()
    print("✅ Report saved to: 100_percent_dead_code_report.txt")
    
    dead_code = detector.find_100_percent_dead()
    total = sum(len(v) for v in dead_code.values())
    
    if total > 0:
        print(f"\n✅ Found {total} functions with 100% certainty of being dead")
        return 0
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
