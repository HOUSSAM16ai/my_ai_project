#!/usr/bin/env python3
"""
اختبارات تحقق تحمي تجربة Codespaces من الأعطال المتكررة.

تؤكد هذه الوحدة أن ملفات الواجهة والنصوص المساندة تتضمن آليات التكيف
ومراقبة الأداء والتنظيف الوقائي بما يمنع استنزاف الموارد في البيئات
السحابية.
"""

import re
import sys
from pathlib import Path
from typing import Iterable


def _scan_patterns(content: str, checks: Iterable[tuple[str, str]], *, flags: int = 0) -> tuple[int, int]:
    """
    يجري مطابقة تعبيرات نمطية على نص محدد ويعيد عدد النتائج الإيجابية والسلبية.

    Args:
        content: النص المراد فحصه.
        checks: أزواج (اسم الفحص، النمط) لتوثيق النتائج.
        flags: أعلام إضافية لتمريرها إلى محرك التعبيرات النمطية.

    Returns:
        عدد العناصر التي تم العثور عليها وعدد العناصر الغائبة على التوالي.
    """

    passed = 0
    failed = 0

    for name, pattern in checks:
        if re.search(pattern, content, flags):
            print(f"  ✅ {name} found")
            passed += 1
        else:
            print(f"  ❌ {name} NOT found")
            failed += 1

    return passed, failed


def _validate_performance_monitor() -> tuple[int, int]:
    """يتحقق من آليات تنظيف الموارد في performance-monitor.js."""

    print("🧪 Testing performance-monitor.js...")

    content = Path("app/static/performance-monitor.js").read_text()

    checks: list[tuple[str, str]] = [
        ("intervals array", r"intervals:\s*\[\]"),
        ("destroy method", r"destroy:\s*function\s*\(\)"),
        ("beforeunload listener", r"window\.addEventListener\('beforeunload'"),
        ("Codespaces detection", r"isCodespaces"),
        ("interval tracking", r"this\.state\.intervals\.push"),
        ("interval cleanup", r"clearInterval\(intervalId\)"),
    ]

    return _scan_patterns(content, checks)

def _validate_index_html() -> tuple[int, int]:
    """يتأكد من تكيّف index.html مع بيئات Codespaces والسحابة."""

    print("\n🧪 Testing index.html...")

    content = Path("app/static/index.html").read_text()

    checks: list[tuple[str, str]] = [
        ("IS_CODESPACES constant", r"const IS_CODESPACES\s*="),
        ("IS_CLOUD_ENV constant", r"const IS_CLOUD_ENV\s*="),
        ("Adaptive MAX_MESSAGES", r"MAX_MESSAGES\s*=\s*IS_CLOUD_ENV\s*\?"),
        ("Adaptive STREAM_UPDATE_THROTTLE", r"STREAM_UPDATE_THROTTLE\s*=\s*IS_CLOUD_ENV\s*\?"),
        ("Adaptive STREAM_MICRO_DELAY", r"STREAM_MICRO_DELAY\s*=\s*IS_CLOUD_ENV\s*\?"),
        ("Memory exhaustion check", r"percentUsed\s*>\s*95"),
        ("Health monitoring", r"fetch\('/health'"),
        ("Startup diagnostics", r"Startup Diagnostics"),
        ("Environment logging", r"Environment:.*CODESPACES"),
    ]

    return _scan_patterns(content, checks, flags=re.DOTALL)

def _validate_supervisor_script() -> tuple[int, int]:
    """يفحص تضمين معالجات Codespaces داخل supervisor.sh."""

    print("\n🧪 Testing supervisor.sh...")

    content = Path(".devcontainer/supervisor.sh").read_text()

    checks: list[tuple[str, str]] = [
        ("Codespaces detection", r"CODESPACES"),
        ("Extended stabilization", r"sleep 5"),
        ("PORT_TIMEOUT variable", r"PORT_TIMEOUT"),
        ("HEALTH_TIMEOUT variable", r"HEALTH_TIMEOUT"),
        ("Codespaces longer timeouts", r"PORT_TIMEOUT=90"),
    ]

    return _scan_patterns(content, checks)

def _validate_diagnostic_script() -> tuple[int, int]:
    """يتحقق من جاهزية وتشغيلية نص التشخيص Codespaces."""

    print("\n🧪 Testing diagnostic script...")

    script_path = Path("scripts/codespaces_diagnostic.sh")

    if not script_path.exists():
        print("  ❌ Diagnostic script does NOT exist")
        return 0, 1

    print("  ✅ Diagnostic script exists")

    content = script_path.read_text()

    checks: list[tuple[str, str]] = [
        ("Environment detection", r"ENVIRONMENT DETECTION"),
        ("System resources check", r"SYSTEM RESOURCES"),
        ("Process check", r"APPLICATION PROCESSES"),
        ("Health check", r"APPLICATION HEALTH"),
        ("uvicorn check", r"uvicorn"),
    ]

    passed = 1  # For existence
    failed = 0

    found, missing = _scan_patterns(content, checks)
    passed += found
    failed += missing

    import os

    if os.access(script_path, os.X_OK):
        print("  ✅ Script is executable")
        passed += 1
    else:
        print("  ❌ Script is NOT executable")
        failed += 1

    return passed, failed


def test_performance_monitor():
    """يتأكد من تفعيل مسارات تنظيف الأداء في مراقب الواجهة."""

    passed, failed = _validate_performance_monitor()
    assert failed == 0, f"performance-monitor.js missing {failed} safeguards"


def test_index_html():
    """يتحقق من إعدادات التكيف مع البيئات السحابية في index.html."""

    passed, failed = _validate_index_html()
    assert failed == 0, f"index.html missing {failed} adaptive features"


def test_supervisor():
    """يفرض وجود معالجات Codespaces في مشرف الحاوية."""

    passed, failed = _validate_supervisor_script()
    assert failed == 0, f"supervisor.sh missing {failed} Codespaces handlers"


def test_diagnostic_script():
    """يضمن سلامة نص التشخيص الخاص بـ Codespaces."""

    passed, failed = _validate_diagnostic_script()
    assert failed == 0, f"codespaces_diagnostic.sh missing {failed} diagnostics"

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     Codespaces Crash Fix - Verification Tests                   ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    passed, failed = _validate_performance_monitor()
    total_passed += passed
    total_failed += failed

    passed, failed = _validate_index_html()
    total_passed += passed
    total_failed += failed

    passed, failed = _validate_supervisor_script()
    total_passed += passed
    total_failed += failed

    passed, failed = _validate_diagnostic_script()
    total_passed += passed
    total_failed += failed
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"📊 Total:  {total_passed + total_failed}")
    print()
    
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED! The fix is complete.")
        print()
        print("Next steps:")
        print("  1. Deploy to GitHub Codespaces")
        print("  2. Run: bash scripts/codespaces_diagnostic.sh")
        print("  3. Test the application for 15+ minutes")
        print("  4. Monitor memory usage in browser console")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
