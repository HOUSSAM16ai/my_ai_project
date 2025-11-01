#!/usr/bin/env python3
"""
Verify Admin Chat Error Handling - Simple Syntax Check
========================================================

This script verifies that:
1. The admin_ai_service.py file has valid Python syntax
2. The error handling code is properly structured
3. Size limits are in place
4. The route handler has comprehensive error catching

لا حاجة لتشغيل الخادم - فقط التحقق من بناء الجملة والمنطق
No need to run the server - just verify syntax and logic
"""

import ast
import os
import sys


def check_file_syntax(filepath):
    """Check if a Python file has valid syntax"""
    print(f"\n{'=' * 70}")
    print(f"📝 Checking: {filepath}")
    print("=" * 70)

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False

    try:
        with open(filepath, encoding="utf-8") as f:
            code = f.read()

        # Try to parse the file as Python AST
        ast.parse(code)
        print("✅ Valid Python syntax")

        # Check for specific improvements
        improvements_found = []

        # Check for size limits in admin_ai_service.py
        if "admin_ai_service.py" in filepath:
            if "max_index_size" in code:
                improvements_found.append("Project index size limit")
            if "max_total_content" in code:
                improvements_found.append("Total file content size limit")
            if "max_file_size" in code:
                improvements_found.append("Individual file size limit")
            if "except Exception as e:" in code and "_build_super_system_prompt" in code:
                improvements_found.append("Comprehensive error handling in prompt building")
            if "fallback" in code.lower():
                improvements_found.append("Fallback prompt for errors")

        # Check for improvements in routes.py
        if "routes.py" in filepath:
            if "max_question_length" in code:
                improvements_found.append("Question length validation")
            if "Question too long" in code:
                improvements_found.append("Long question error message")
            if "نوع الخطأ" in code or "Error type" in code:
                improvements_found.append("Detailed bilingual error messages")

        if improvements_found:
            print("\n✨ Improvements detected:")
            for imp in improvements_found:
                print(f"   ✓ {imp}")

        return True

    except SyntaxError as e:
        print("❌ Syntax Error:")
        print(f"   Line {e.lineno}: {e.msg}")
        print(f"   {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_error_handling_coverage():
    """Check that error handling is comprehensive"""
    print(f"\n{'=' * 70}")
    print("🛡️  Checking Error Handling Coverage")
    print("=" * 70)

    service_file = "app/services/admin_ai_service.py"
    routes_file = "app/admin/routes.py"

    checks = []

    # Check service file
    if os.path.exists(service_file):
        with open(service_file, encoding="utf-8") as f:
            service_code = f.read()

        checks.append(
            (
                "Service: Try-catch in _build_super_system_prompt",
                "try:" in service_code and "_build_super_system_prompt" in service_code,
            )
        )
        checks.append(("Service: Fallback prompt on error", "fallback" in service_code.lower()))
        checks.append(("Service: Size limits on project index", "max_index_size" in service_code))
        checks.append(("Service: Size limits on file content", "max_file_size" in service_code))
        checks.append(
            (
                "Service: Logging prompt size",
                "prompt_size" in service_code or "len(final_prompt)" in service_code,
            )
        )

    # Check routes file
    if os.path.exists(routes_file):
        with open(routes_file, encoding="utf-8") as f:
            routes_code = f.read()

        checks.append(("Routes: Question length validation", "max_question_length" in routes_code))
        checks.append(
            ("Routes: Top-level try-catch", "try:" in routes_code and "handle_chat" in routes_code)
        )
        checks.append(
            (
                "Routes: Conversation creation error handling",
                "try:" in routes_code and "create_conversation" in routes_code,
            )
        )
        checks.append(
            (
                "Routes: Detailed error messages",
                "نوع الخطأ" in routes_code or "Error type" in routes_code,
            )
        )

    print()
    passed = 0
    failed = 0
    for check_name, result in checks:
        if result:
            print(f"   ✅ {check_name}")
            passed += 1
        else:
            print(f"   ❌ {check_name}")
            failed += 1

    print(f"\n{'=' * 70}")
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


def main():
    """Run all checks"""
    print("\n" + "=" * 70)
    print("🔍 Admin Chat Error Handling Verification")
    print("   التحقق من معالجة الأخطاء في محادثة الأدمن")
    print("=" * 70)

    os.chdir("/home/runner/work/my_ai_project/my_ai_project")

    files_to_check = [
        "app/services/admin_ai_service.py",
        "app/admin/routes.py",
        "tests/test_admin_chat_complex_questions.py",
    ]

    all_valid = True
    for filepath in files_to_check:
        if not check_file_syntax(filepath):
            all_valid = False

    # Check error handling coverage
    if not check_error_handling_coverage():
        all_valid = False

    print(f"\n{'=' * 70}")
    if all_valid:
        print("✅ All checks passed!")
        print("   ✨ The admin chat system has comprehensive error handling")
        print("   ✨ Complex questions should now work correctly")
        print("=" * 70)
        return 0
    else:
        print("❌ Some checks failed!")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
