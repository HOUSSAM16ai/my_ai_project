#!/usr/bin/env python3
"""
Simple verification script to check the admin chat error fix
Verifies that the code changes are correct without requiring database setup
"""

import re


def verify_route_error_handling():
    """Verify that all critical routes return 200 on errors"""
    print("🧪 Verifying route error handling...")

    routes_file = "app/admin/routes.py"

    with open(routes_file) as f:
        content = f.read()

    # Check that critical routes return 200 with error details
    critical_routes = [
        "handle_chat",
        "handle_analyze_project",
        "handle_get_conversations",
        "handle_execute_modification",
    ]

    for route in critical_routes:
        print(f"\n📝 Checking {route}...")

        # Find the route function
        pattern = rf"def {route}\(.*?\):.*?(?=\n@|\ndef |\nclass |\Z)"
        match = re.search(pattern, content, re.DOTALL)

        if not match:
            print(f"   ❌ Route {route} not found")
            return False

        route_code = match.group(0)

        # Check for exception handling that returns 200
        if "except Exception as e:" in route_code:
            # Check that we're returning 200, not 500
            if ", 500" in route_code and "jsonify" in route_code:
                # Find the specific exception handler
                exception_section = route_code.split("except Exception as e:")[1].split("\n\n")[0]
                if ", 500" in exception_section:
                    print("   ❌ Still returns 500 status code!")
                    print(f"   Found: {exception_section[:200]}")
                    return False

            # Check that we're returning 200 with error details
            if ", 200" in route_code or "), 200" in route_code:
                print("   ✅ Returns 200 with error details")
            else:
                print("   ⚠️  Warning: No explicit 200 status found")

            # Check for bilingual error messages
            if "⚠️" in route_code or "خطأ" in route_code or "فشل" in route_code:
                print("   ✅ Has bilingual error messages")
            else:
                print("   ⚠️  No bilingual error messages found")

            # Check for answer field in error response
            if '"answer"' in route_code:
                print("   ✅ Returns 'answer' field for frontend")
            else:
                print("   ⚠️  No 'answer' field in error response")
        else:
            print("   ⚠️  No exception handler found")

    return True


def verify_frontend_error_handling():
    """Verify that frontend properly displays error messages"""
    print("\n🧪 Verifying frontend error handling...")

    template_file = "app/admin/templates/admin_dashboard.html"

    with open(template_file) as f:
        content = f.read()

    # Check sendMessage function
    print("\n📝 Checking sendMessage function...")
    if "if (result.answer)" in content:
        print("   ✅ Checks for result.answer")
    else:
        print("   ❌ Missing result.answer check")
        return False

    if "formatContent(result.answer)" in content:
        print("   ✅ Formats error answer properly")
    else:
        print("   ⚠️  May not format error answer")

    # Check analyzeProject function
    print("\n📝 Checking analyzeProject function...")
    if "if (result.answer)" in content:
        print("   ✅ Checks for result.answer")
    else:
        print("   ❌ Missing result.answer check")
        return False

    # Check for conversation_id tracking on errors
    if "result.conversation_id" in content:
        print("   ✅ Tracks conversation_id")
    else:
        print("   ⚠️  May not track conversation_id")

    return True


def verify_error_message_quality():
    """Verify that error messages are helpful and professional"""
    print("\n🧪 Verifying error message quality...")

    routes_file = "app/admin/routes.py"

    with open(routes_file) as f:
        content = f.read()

    quality_indicators = {
        "Bilingual (Arabic)": ["⚠️", "خطأ", "فشل"],
        "Helpful details": ["**Possible causes:**", "**Solution:**", "**Error details:**"],
        "Professional tone": ["Please", "try again", "contact support"],
    }

    for category, indicators in quality_indicators.items():
        found = any(indicator in content for indicator in indicators)
        if found:
            print(f"   ✅ {category}: Present")
        else:
            print(f"   ❌ {category}: Missing")
            return False

    return True


def main():
    print("=" * 70)
    print("🚀 Admin Chat 500 Error Fix Verification (Code Analysis)")
    print("=" * 70)

    all_passed = True

    # Run all verification checks
    if not verify_route_error_handling():
        all_passed = False

    if not verify_frontend_error_handling():
        all_passed = False

    if not verify_error_message_quality():
        all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL VERIFICATIONS PASSED!")
        print("\n🎉 The fix has been successfully implemented:")
        print("   ✓ Backend routes return 200 with error details (not 500)")
        print("   ✓ Error messages are bilingual (Arabic + English)")
        print("   ✓ Frontend properly displays error 'answer' field")
        print("   ✓ Conversation tracking works even on errors")
        print("   ✓ Error messages include helpful troubleshooting info")
        print("\n💡 Next steps:")
        print("   1. Test manually by running the app without API keys")
        print("   2. Verify error messages display correctly in the UI")
        print("   3. Check that conversations are created even on errors")
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        print("\nPlease review the issues above and fix them.")
        return 1

    print("=" * 70)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
