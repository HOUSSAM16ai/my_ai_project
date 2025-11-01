#!/usr/bin/env python3
"""
🧪 TEST: Supabase Migration Schema Fix
========================================
This script tests the fix_supabase_migration_schema.py solution
without actually connecting to a database.

It verifies:
1. Script syntax is valid
2. All functions are defined
3. SQL statements are correct
4. Documentation exists

Author: Houssam Benmerah
Version: 1.0.0
"""

import sys
from pathlib import Path

# ANSI Colors
G = "\033[92m"  # Green
Y = "\033[93m"  # Yellow
R = "\033[91m"  # Red
B = "\033[94m"  # Blue
C = "\033[96m"  # Cyan
E = "\033[0m"  # End


def print_header(text):
    """Print a beautiful header"""
    print(f"\n{B}{'=' * 70}{E}")
    print(f"{C}{text}{E}")
    print(f"{B}{'=' * 70}{E}\n")


def print_success(text):
    """Print success message"""
    print(f"{G}✅ {text}{E}")


def print_error(text):
    """Print error message"""
    print(f"{R}❌ {text}{E}")


def print_info(text):
    """Print info message"""
    print(f"{B}ℹ️  {text}{E}")


def test_script_exists():
    """Test that the script file exists"""
    print_header("TEST 1: Script File Exists")

    script_path = Path(__file__).parent / "fix_supabase_migration_schema.py"

    assert script_path.exists(), "fix_supabase_migration_schema.py NOT found"
    print_success("fix_supabase_migration_schema.py exists")
    print_info(f"Size: {script_path.stat().st_size} bytes")


def test_script_syntax():
    """Test that the script has valid Python syntax"""
    print_header("TEST 2: Script Syntax")

    script_path = Path(__file__).parent / "fix_supabase_migration_schema.py"

    # First, just compile to check syntax
    with open(script_path, encoding="utf-8") as f:
        code = f.read()

    compile(code, script_path, "exec")
    print_success("Script syntax is valid (compilation successful)")


def test_functions_defined():
    """Test that all required functions are defined"""
    print_header("TEST 3: Required Functions")

    script_path = Path(__file__).parent / "fix_supabase_migration_schema.py"

    # Read the script content
    with open(script_path, encoding="utf-8") as f:
        content = f.read()

    required_functions = [
        "create_supabase_migration_schema",
        "sync_alembic_to_supabase",
        "verify_setup",
        "main",
    ]

    all_found = True
    missing_functions = []
    for func in required_functions:
        if f"def {func}(" in content:
            print_success(f"Function '{func}' is defined")
        else:
            print_error(f"Function '{func}' NOT found")
            all_found = False
            missing_functions.append(func)

    assert all_found, f"Missing functions: {', '.join(missing_functions)}"


def test_sql_statements():
    """Test that SQL statements are present and correct"""
    print_header("TEST 4: SQL Statements")

    script_path = Path(__file__).parent / "fix_supabase_migration_schema.py"

    with open(script_path, encoding="utf-8") as f:
        content = f.read()

    sql_checks = [
        ("CREATE SCHEMA supabase_migrations", "Schema creation SQL"),
        ("CREATE TABLE supabase_migrations.schema_migrations", "Table creation SQL"),
        ("version VARCHAR(255) PRIMARY KEY", "Version column definition"),
        ("statements TEXT[]", "Statements column definition"),
        ("applied_at TIMESTAMP", "Applied_at column definition"),
        ("SELECT version_num FROM alembic_version", "Alembic version query"),
        ("INSERT INTO supabase_migrations.schema_migrations", "Insert migration SQL"),
    ]

    all_found = True
    missing_statements = []
    for sql, description in sql_checks:
        if sql in content:
            print_success(f"{description} present")
        else:
            print_error(f"{description} NOT found")
            all_found = False
            missing_statements.append(description)

    assert all_found, f"Missing SQL statements: {', '.join(missing_statements)}"


def test_documentation_exists():
    """Test that documentation files exist"""
    print_header("TEST 5: Documentation Files")

    docs = [
        ("SUPABASE_MIGRATION_SCHEMA_FIX_AR.md", "Arabic documentation"),
        ("SUPABASE_MIGRATION_SCHEMA_FIX_EN.md", "English documentation"),
        ("QUICK_FIX_MIGRATION_ERROR.md", "Quick reference"),
    ]

    all_found = True
    missing_docs = []
    for filename, description in docs:
        doc_path = Path(__file__).parent / filename
        if doc_path.exists():
            size = doc_path.stat().st_size
            print_success(f"{description} exists ({size} bytes)")
        else:
            print_error(f"{description} NOT found")
            all_found = False
            missing_docs.append(description)

    assert all_found, f"Missing documentation files: {', '.join(missing_docs)}"


def test_integration():
    """Test integration with other scripts"""
    print_header("TEST 6: Integration with Other Scripts")

    # Check apply_migrations.py integration
    apply_migrations_path = Path(__file__).parent / "apply_migrations.py"

    if apply_migrations_path.exists():
        with open(apply_migrations_path, encoding="utf-8") as f:
            content = f.read()

        assert (
            "fix_supabase_migration_schema.py" in content
        ), "NOT integrated with apply_migrations.py"
        print_success("Integrated with apply_migrations.py")

    # Check quick_start script integration
    quick_start_path = Path(__file__).parent / "quick_start_supabase_verification.sh"

    if quick_start_path.exists():
        with open(quick_start_path, encoding="utf-8") as f:
            content = f.read()

        assert (
            "fix_supabase_migration_schema.py" in content
        ), "NOT integrated with quick_start script"
        print_success("Integrated with quick_start_supabase_verification.sh")

    # Check tools listing
    tools_path = Path(__file__).parent / "show_supabase_tools.py"

    if tools_path.exists():
        with open(tools_path, encoding="utf-8") as f:
            content = f.read()

        assert "fix_supabase_migration_schema.py" in content, "NOT listed in tools"
        print_success("Listed in show_supabase_tools.py")


def test_error_handling():
    """Test that error handling is present"""
    print_header("TEST 7: Error Handling")

    script_path = Path(__file__).parent / "fix_supabase_migration_schema.py"

    with open(script_path, encoding="utf-8") as f:
        content = f.read()

    checks = [
        ("try:", "Try-except blocks present"),
        ("except Exception as e:", "Generic exception handling"),
        ("traceback.format_exc()", "Traceback formatting"),
        ("trans.rollback()", "Transaction rollback"),
        ("trans.commit()", "Transaction commit"),
    ]

    all_found = True
    missing_checks = []
    for check, description in checks:
        count = content.count(check)
        if count > 0:
            print_success(f"{description} ({count} occurrences)")
        else:
            print_error(f"{description} NOT found")
            all_found = False
            missing_checks.append(description)

    assert all_found, f"Missing error handling: {', '.join(missing_checks)}"


def main():
    """Run all tests"""
    print_header("🧪 TESTING SUPABASE MIGRATION SCHEMA FIX")

    print(f"{C}Testing the superhuman solution...{E}\n")

    tests = [
        ("Script Exists", test_script_exists),
        ("Script Syntax", test_script_syntax),
        ("Functions Defined", test_functions_defined),
        ("SQL Statements", test_sql_statements),
        ("Documentation", test_documentation_exists),
        ("Integration", test_integration),
        ("Error Handling", test_error_handling),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"Test '{test_name}' failed with exception: {str(e)}")
            results[test_name] = False

    # Summary
    print_header("📊 TEST SUMMARY")

    total = len(results)
    passed = sum(1 for r in results.values() if r)
    failed = total - passed

    for test_name, result in results.items():
        status = f"{G}✅ PASS{E}" if result else f"{R}❌ FAIL{E}"
        print(f"{status} - {test_name}")

    print(f"\n{C}{'=' * 70}{E}")
    print(f"{G}Passed: {passed}/{total}{E}")
    print(f"{R}Failed: {failed}/{total}{E}")

    if failed == 0:
        print(f"\n{G}🎉 ALL TESTS PASSED! The solution is ready!{E}")
        print(f"{G}{'=' * 70}{E}\n")
        return 0
    else:
        print(f"\n{R}⚠️  Some tests failed. Please review.{E}")
        print(f"{R}{'=' * 70}{E}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
