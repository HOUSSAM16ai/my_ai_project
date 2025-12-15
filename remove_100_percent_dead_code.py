#!/usr/bin/env python3
"""
Remove 100% Dead Code
Safely removes only functions with 100% certainty
"""

import ast
import os
import subprocess
from typing import Set, List, Tuple, Dict


class FunctionRemover(ast.NodeTransformer):
    """AST transformer to remove specific functions"""
    
    def __init__(self, functions_to_remove: Set[str]):
        self.functions_to_remove = functions_to_remove
        self.removed_count = 0
        
    def visit_FunctionDef(self, node):
        if node.name in self.functions_to_remove:
            self.removed_count += 1
            return None  # Remove this node
        return self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        if node.name in self.functions_to_remove:
            self.removed_count += 1
            return None
        return self.generic_visit(node)


def remove_functions_from_file(filepath: str, functions: Set[str]) -> Tuple[bool, int]:
    """Remove specific functions from a file using AST"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse and transform
        tree = ast.parse(source, filepath)
        remover = FunctionRemover(functions)
        new_tree = remover.visit(tree)
        
        if remover.removed_count > 0:
            # Convert back to source
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


def load_100_percent_dead(report_file: str = "100_percent_dead_code_report.txt") -> Dict[str, Set[str]]:
    """Load 100% dead functions from report"""
    dead_functions = {}
    current_file = None
    
    with open(report_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Match file lines
            if line.startswith('app/') and ' dead):' in line:
                current_file = line.split(' (')[0]
                dead_functions[current_file] = set()
            
            # Match function lines
            elif line.startswith('✅ ') and current_file:
                function_name = line.split('✅ ')[1].strip()
                dead_functions[current_file].add(function_name)
    
    return dead_functions


def run_tests() -> Tuple[bool, str]:
    """Run test suite"""
    try:
        result = subprocess.run(
            ['pytest', 'tests/', '-q', '--tb=no', '-x'],
            capture_output=True,
            text=True,
            timeout=300
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def main():
    print("🚀 Removing 100% Dead Code")
    print("=" * 80)
    print()
    
    # Check astor
    try:
        import astor
    except ImportError:
        print("❌ Error: 'astor' package required")
        print("   Install: pip install astor")
        return 1
    
    # Load dead functions
    if not os.path.exists("100_percent_dead_code_report.txt"):
        print("❌ Error: 100_percent_dead_code_report.txt not found")
        print("   Run: python ultra_conservative_dead_code_filter.py")
        return 1
    
    dead_functions = load_100_percent_dead()
    total_files = len(dead_functions)
    total_functions = sum(len(v) for v in dead_functions.values())
    
    print(f"📊 Found {total_functions} functions in {total_files} files")
    print()
    
    # Confirm
    print("⚠️  This will remove 100% confirmed dead code")
    response = input(f"Remove {total_functions} functions? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted")
        return 0
    
    print()
    print("🔧 Removing dead code...")
    print()
    
    files_modified = 0
    total_removed = 0
    
    for filepath, functions in dead_functions.items():
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue
        
        print(f"Processing {filepath}...", end=" ")
        
        modified, count = remove_functions_from_file(filepath, functions)
        if modified:
            files_modified += 1
            total_removed += count
            print(f"✅ Removed {count} functions")
        else:
            print("⚠️  No changes")
    
    print()
    print("=" * 80)
    print(f"✅ Files modified: {files_modified}")
    print(f"✅ Functions removed: {total_removed}")
    print("=" * 80)
    print()
    
    # Run tests
    print("🧪 Running test suite...")
    print("   This may take a few minutes...")
    print()
    
    success, output = run_tests()
    
    if success:
        print("✅ ALL TESTS PASSED!")
        print()
        print("🎉 Dead code removal successful!")
        return 0
    else:
        print("⚠️  Some tests failed")
        print()
        print("Output (last 50 lines):")
        print("-" * 80)
        lines = output.split('\n')
        for line in lines[-50:]:
            print(line)
        print("-" * 80)
        print()
        print("⚠️  Review the changes and fix any issues")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
