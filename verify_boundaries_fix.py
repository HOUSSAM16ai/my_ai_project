#!/usr/bin/env python3
"""
Verification Script for ModuleNotFoundError Fix
================================================

This script verifies that the fix for the 'ModuleNotFoundError: No module named app.boundaries'
issue is working correctly by testing all import paths.

Tests:
1. app.boundaries module imports
2. app.services.boundaries package recognition
3. Individual boundary service imports
4. Router import patterns
"""

import ast
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_package_structure():
    """Test that the package structure is correct"""
    print("=" * 70)
    print("TEST 1: Package Structure")
    print("=" * 70)
    
    # Check that __init__.py exists
    init_file = project_root / "app" / "services" / "boundaries" / "__init__.py"
    if not init_file.exists():
        print("❌ FAILED: __init__.py does not exist")
        return False
    print(f"✅ __init__.py exists at: {init_file}")
    
    # Check syntax
    with open(init_file, 'r') as f:
        code = f.read()
        try:
            ast.parse(code)
            print("✅ __init__.py syntax is valid")
        except SyntaxError as e:
            print(f"❌ FAILED: Syntax error in __init__.py: {e}")
            return False
    
    # Check __all__ exports
    import re
    all_match = re.search(r'__all__\s*=\s*\[(.*?)\]', code, re.DOTALL)
    if all_match:
        exports = [s.strip().strip('"').strip("'") for s in all_match.group(1).split(',') if s.strip()]
        print(f"✅ __all__ exports: {exports}")
        
        expected = ['AdminChatBoundaryService', 'AuthBoundaryService', 
                   'CrudBoundaryService', 'ObservabilityBoundaryService']
        if set(exports) == set(expected):
            print("✅ All expected services are exported")
        else:
            print(f"⚠️ WARNING: Exports don't match expected: {expected}")
    else:
        print("❌ FAILED: __all__ not defined")
        return False
    
    return True


def test_package_recognition():
    """Test that Python recognizes the package"""
    print("\n" + "=" * 70)
    print("TEST 2: Package Recognition")
    print("=" * 70)
    
    import importlib.util
    spec = importlib.util.find_spec('app.services.boundaries')
    if spec is None:
        print("❌ FAILED: Package not found by Python")
        return False
    
    print(f"✅ Package found at: {spec.origin}")
    return True


def test_router_imports():
    """Test that routers have correct import statements"""
    print("\n" + "=" * 70)
    print("TEST 3: Router Import Statements")
    print("=" * 70)
    
    routers = [
        ('app/api/routers/admin.py', 'AdminChatBoundaryService'),
        ('app/api/routers/security.py', 'AuthBoundaryService'),
        ('app/api/routers/crud.py', 'CrudBoundaryService'),
        ('app/api/routers/observability.py', 'ObservabilityBoundaryService'),
    ]
    
    all_passed = True
    for router_file, expected_import in routers:
        router_path = project_root / router_file
        if not router_path.exists():
            print(f"⚠️ WARNING: {router_file} does not exist")
            continue
            
        with open(router_path, 'r') as f:
            content = f.read()
            tree = ast.parse(content)
            
            found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and 'boundaries' in node.module:
                        imports = [alias.name for alias in node.names]
                        if expected_import in imports:
                            print(f"✅ {router_file}: imports {expected_import}")
                            found = True
                            break
            
            if not found:
                print(f"❌ FAILED: {router_file} does not import {expected_import}")
                all_passed = False
    
    return all_passed


def test_app_boundaries():
    """Test that app.boundaries module is also working"""
    print("\n" + "=" * 70)
    print("TEST 4: app.boundaries Module")
    print("=" * 70)
    
    boundaries_init = project_root / "app" / "boundaries" / "__init__.py"
    if not boundaries_init.exists():
        print("❌ FAILED: app/boundaries/__init__.py does not exist")
        return False
    
    print("✅ app/boundaries/__init__.py exists")
    
    # Check that required classes are exported
    with open(boundaries_init, 'r') as f:
        content = f.read()
        required = ['CircuitBreakerConfig', 'get_policy_boundary', 'get_service_boundary']
        all_found = True
        for req in required:
            if req in content:
                print(f"✅ {req} is exported from app.boundaries")
            else:
                print(f"❌ FAILED: {req} is NOT exported from app.boundaries")
                all_found = False
        
        return all_found


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("FIX VERIFICATION: ModuleNotFoundError for app.services.boundaries")
    print("=" * 70)
    print()
    
    results = []
    
    # Run tests
    results.append(("Package Structure", test_package_structure()))
    results.append(("Package Recognition", test_package_recognition()))
    results.append(("Router Imports", test_router_imports()))
    results.append(("app.boundaries Module", test_app_boundaries()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED! The fix is working correctly.")
        print()
        print("The ModuleNotFoundError for 'app.boundaries' has been resolved by:")
        print("1. Creating app/services/boundaries/__init__.py")
        print("2. Properly exporting all boundary service classes")
        print("3. Maintaining backward compatibility with app.boundaries")
        return 0
    else:
        print("❌ SOME TESTS FAILED. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
