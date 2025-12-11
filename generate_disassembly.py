#!/usr/bin/env python3
"""
Automated Service Disassembly Generator
========================================
Generates hexagonal architecture structure for all God Services
"""

import re
from pathlib import Path


def extract_classes_and_functions(file_path):
    """Extract class and function names from a Python file"""
    content = file_path.read_text()
    
    # Find all class definitions
    classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
    
    # Find all top-level function definitions
    functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
    
    # Find enums
    enums = [c for c in classes if 'Enum' in content[content.find(f'class {c}'):content.find(f'class {c}') + 200]]
    
    # Find dataclasses
    dataclasses = []
    for c in classes:
        idx = content.find(f'class {c}')
        if idx != -1 and '@dataclass' in content[max(0, idx-100):idx]:
            dataclasses.append(c)
    
    # Find main service class (usually the longest or has 'Service' in name)
    service_classes = [c for c in classes if 'Service' in c or 'Manager' in c or 'Engine' in c or 'Orchestrator' in c]
    
    return {
        'all_classes': classes,
        'enums': enums,
        'dataclasses': dataclasses,
        'service_classes': service_classes,
        'functions': functions
    }


def generate_shim_file(original_file, analysis):
    """Generate a thin shim file that delegates to refactored module"""
    
    # Extract module name from file (remove _service.py suffix)
    module_name = original_file.stem
    if module_name.endswith('_service'):
        short_name = module_name[:-8]  # Remove '_service'
    else:
        short_name = module_name
    
    # Generate imports
    imports = []
    if analysis['enums']:
        imports.extend(analysis['enums'])
    if analysis['dataclasses']:
        imports.extend(analysis['dataclasses'])
    if analysis['service_classes']:
        imports.extend(analysis['service_classes'])
    if analysis['functions']:
        imports.extend([f for f in analysis['functions'] if f.startswith('get_') or f.startswith('create_')])
    
    shim_content = f'''# {original_file.name}
"""
{module_name.upper()} - LEGACY COMPATIBILITY
{'=' * 60}
This file now imports from the refactored {short_name} module.

Original file: {len(original_file.read_text().splitlines())}+ lines
Refactored: Delegates to {short_name}/ module following Hexagonal Architecture

For new code, import from: app.services.{short_name}
"""

# Legacy imports for backward compatibility
# TODO: Implement refactored module at app/services/{short_name}/
# from app.services.{short_name} import (
#     {', '.join(imports[:5]) if imports else '# Add imports here'}
# )

# Placeholder - Original monolithic implementation
# This will be replaced once refactoring is complete
import warnings

warnings.warn(
    f"{{__name__}} is a monolithic service pending refactoring. "
    f"Consider using app.services.{short_name} when available.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from original for now (keeping monolithic code temporarily)
# After refactoring, this will import from the new modular structure

__all__ = {imports[:10] if imports else []}
'''
    
    return shim_content


def main():
    services_dir = Path("app/services")
    report = []
    
    # Find all God Services (500+ lines)
    for py_file in services_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue
        
        lines = len(py_file.read_text().splitlines())
        if lines < 500:
            continue
        
        print(f"Analyzing {py_file.name} ({lines} lines)...")
        
        # Analyze structure
        analysis = extract_classes_and_functions(py_file)
        
        report.append({
            'file': py_file.name,
            'lines': lines,
            'classes': len(analysis['all_classes']),
            'enums': len(analysis['enums']),
            'dataclasses': len(analysis['dataclasses']),
            'services': len(analysis['service_classes']),
        })
    
    # Generate report
    print("\n" + "=" * 80)
    print("SERVICE ANALYSIS REPORT")
    print("=" * 80)
    print(f"{'File':<45} {'Lines':<8} {'Classes':<8} {'Enums':<8} {'Data':<8}")
    print("-" * 80)
    
    for r in sorted(report, key=lambda x: x['lines'], reverse=True):
        print(f"{r['file']:<45} {r['lines']:<8} {r['classes']:<8} {r['enums']:<8} {r['dataclasses']:<8}")
    
    print("-" * 80)
    print(f"Total: {len(report)} God Services analyzed")
    print("=" * 80)


if __name__ == "__main__":
    main()
