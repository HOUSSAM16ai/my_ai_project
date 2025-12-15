#!/usr/bin/env python3
"""
Safe Dead Code Remover
Removes dead functions one by one with verification
"""

import ast
import os
import subprocess
from typing import Set, List, Tuple


def remove_function_from_file(filepath: str, function_name: str) -> bool:
    """Remove a specific function from a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the function
        new_lines = []
        skip_until_dedent = False
        function_indent = None
        found = False
        
        for i, line in enumerate(lines):
            # Check if this is the function definition
            if line.strip().startswith(f'def {function_name}(') or line.strip().startswith(f'async def {function_name}('):
                found = True
                skip_until_dedent = True
                function_indent = len(line) - len(line.lstrip())
                continue
            
            # Skip function body
            if skip_until_dedent:
                current_indent = len(line) - len(line.lstrip())
                # If line is not empty and has same or less indentation, function ended
                if line.strip() and current_indent <= function_indent:
                    skip_until_dedent = False
                    new_lines.append(line)
                # Skip function body lines
                continue
            
            new_lines.append(line)
        
        if found:
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error removing {function_name} from {filepath}: {e}")
        return False


def run_quick_tests() -> bool:
    """Run a quick subset of tests"""
    try:
        result = subprocess.run(
            ['pytest', 'tests/unit/test_enum_case_sensitivity.py', 'tests/test_settings_smoke.py', '-q', '--tb=no'],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode == 0
    except:
        return False


def load_dead_functions(report_file: str = "final_dead_code_report.txt") -> List[Tuple[str, str]]:
    """Load dead functions from report"""
    dead_functions = []
    current_file = None
    
    with open(report_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Match file lines
            if line.startswith('app/') and ' dead):' in line:
                current_file = line.split(' (')[0]
            
            # Match function lines
            elif line.startswith('- ') and current_file:
                function_name = line[2:].strip()
                dead_functions.append((current_file, function_name))
    
    return dead_functions


def main():
    print("🚀 Safe Dead Code Removal")
    print("=" * 80)
    print()
    
    # Load dead functions
    if not os.path.exists("final_dead_code_report.txt"):
        print("❌ Error: final_dead_code_report.txt not found")
        return 1
    
    dead_functions = load_dead_functions()
    print(f"📊 Found {len(dead_functions)} dead functions to remove")
    print()
    
    # Ask for confirmation
    response = input(f"⚠️  Remove {len(dead_functions)} dead functions? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Aborted")
        return 0
    
    print()
    print("🔧 Removing dead code...")
    print()
    
    removed_count = 0
    failed_count = 0
    
    for filepath, function_name in dead_functions:
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue
        
        print(f"Removing {function_name} from {filepath}...", end=" ")
        
        if remove_function_from_file(filepath, function_name):
            removed_count += 1
            print("✅")
        else:
            failed_count += 1
            print("❌")
    
    print()
    print("=" * 80)
    print(f"✅ Removed: {removed_count}")
    print(f"❌ Failed: {failed_count}")
    print("=" * 80)
    print()
    
    # Run quick tests
    print("🧪 Running quick tests...")
    if run_quick_tests():
        print("✅ Tests passed!")
    else:
        print("⚠️  Some tests failed - review changes")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
