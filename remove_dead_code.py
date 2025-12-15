#!/usr/bin/env python3
"""
Automated Dead Code Removal Script
Removes truly dead functions and classes from the codebase
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple


class DeadCodeRemover(ast.NodeTransformer):
    """AST transformer to remove dead code"""
    
    def __init__(self, dead_names: Set[str]):
        self.dead_names = dead_names
        self.removed_count = 0
        
    def visit_FunctionDef(self, node):
        if node.name in self.dead_names and not node.name.startswith('_'):
            self.removed_count += 1
            return None  # Remove this node
        return self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        if node.name in self.dead_names and not node.name.startswith('_'):
            self.removed_count += 1
            return None
        return self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        if node.name in self.dead_names and not node.name.startswith('_'):
            self.removed_count += 1
            return None
        return self.generic_visit(node)


def load_dead_code_report(report_file: str = "smart_dead_code_report.txt") -> Dict[str, Set[str]]:
    """Parse the dead code report"""
    dead_code = {}
    current_file = None
    
    with open(report_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Match file lines like: "app/some/file.py (10 dead):"
            if line.startswith('app/') and ' dead):' in line:
                current_file = line.split(' (')[0]
                dead_code[current_file] = set()
            
            # Match function/class lines like: "  - function_name"
            elif line.startswith('- ') and current_file:
                name = line[2:].strip()
                dead_code[current_file].add(name)
    
    return dead_code


def remove_dead_code_from_file(filepath: str, dead_names: Set[str]) -> Tuple[bool, int]:
    """Remove dead code from a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the file
        tree = ast.parse(source, filepath)
        
        # Remove dead code
        remover = DeadCodeRemover(dead_names)
        new_tree = remover.visit(tree)
        
        if remover.removed_count > 0:
            # Convert back to source code
            import astor
            new_source = astor.to_source(new_tree)
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_source)
            
            return True, remover.removed_count
        
        return False, 0
        
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False, 0


def main():
    """Main entry point"""
    print("🚀 Starting automated dead code removal...")
    print()
    
    # Check if astor is available
    try:
        import astor
    except ImportError:
        print("❌ Error: 'astor' package is required")
        print("   Install it with: pip install astor")
        return 1
    
    # Load dead code report
    if not os.path.exists("smart_dead_code_report.txt"):
        print("❌ Error: smart_dead_code_report.txt not found")
        print("   Run advanced_dead_code_detector.py first")
        return 1
    
    print("📖 Loading dead code report...")
    dead_code = load_dead_code_report()
    
    total_files = len(dead_code)
    total_dead = sum(len(v) for v in dead_code.values())
    
    print(f"✅ Found {total_dead} dead definitions in {total_files} files")
    print()
    
    # Ask for confirmation
    response = input(f"⚠️  This will remove {total_dead} definitions. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted by user")
        return 0
    
    print()
    print("🔧 Removing dead code...")
    
    files_modified = 0
    total_removed = 0
    
    for filepath, dead_names in dead_code.items():
        if os.path.exists(filepath):
            modified, count = remove_dead_code_from_file(filepath, dead_names)
            if modified:
                files_modified += 1
                total_removed += count
                print(f"✅ {filepath}: removed {count} definitions")
    
    print()
    print("=" * 80)
    print(f"✅ REMOVAL COMPLETE")
    print(f"   Files modified: {files_modified}")
    print(f"   Definitions removed: {total_removed}")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
