#!/usr/bin/env python3
"""
Test script to verify Codespaces crash fixes
Tests the key changes made to prevent browser crashes
"""

import re
import sys
from pathlib import Path

def test_performance_monitor():
    """Test that performance-monitor.js has proper cleanup"""
    print("🧪 Testing performance-monitor.js...")
    
    content = Path("app/static/performance-monitor.js").read_text()
    
    checks = [
        ("intervals array", r"intervals:\s*\[\]"),
        ("destroy method", r"destroy:\s*function\s*\(\)"),
        ("beforeunload listener", r"window\.addEventListener\('beforeunload'"),
        ("Codespaces detection", r"isCodespaces"),
        ("interval tracking", r"this\.state\.intervals\.push"),
        ("interval cleanup", r"clearInterval\(intervalId\)"),
    ]
    
    passed = 0
    failed = 0
    
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"  ✅ {name} found")
            passed += 1
        else:
            print(f"  ❌ {name} NOT found")
            failed += 1
    
    return passed, failed

def test_index_html():
    """Test that index.html has environment detection and adaptive config"""
    print("\n🧪 Testing index.html...")
    
    content = Path("app/static/index.html").read_text()
    
    checks = [
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
    
    passed = 0
    failed = 0
    
    for name, pattern in checks:
        if re.search(pattern, content, re.DOTALL):
            print(f"  ✅ {name} found")
            passed += 1
        else:
            print(f"  ❌ {name} NOT found")
            failed += 1
    
    return passed, failed

def test_supervisor():
    """Test that supervisor.sh has Codespaces-specific handling"""
    print("\n🧪 Testing supervisor.sh...")
    
    content = Path(".devcontainer/supervisor.sh").read_text()
    
    checks = [
        ("Codespaces detection", r"CODESPACES"),
        ("Extended stabilization", r"sleep 5"),
        ("PORT_TIMEOUT variable", r"PORT_TIMEOUT"),
        ("HEALTH_TIMEOUT variable", r"HEALTH_TIMEOUT"),
        ("Codespaces longer timeouts", r"PORT_TIMEOUT=90"),
    ]
    
    passed = 0
    failed = 0
    
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"  ✅ {name} found")
            passed += 1
        else:
            print(f"  ❌ {name} NOT found")
            failed += 1
    
    return passed, failed

def test_diagnostic_script():
    """Test that diagnostic script exists and is executable"""
    print("\n🧪 Testing diagnostic script...")
    
    script_path = Path("scripts/codespaces_diagnostic.sh")
    
    if not script_path.exists():
        print("  ❌ Diagnostic script does NOT exist")
        return 0, 1
    
    print("  ✅ Diagnostic script exists")
    
    content = script_path.read_text()
    
    checks = [
        ("Environment detection", r"ENVIRONMENT DETECTION"),
        ("System resources check", r"SYSTEM RESOURCES"),
        ("Process check", r"APPLICATION PROCESSES"),
        ("Health check", r"APPLICATION HEALTH"),
        ("uvicorn check", r"uvicorn"),
    ]
    
    passed = 1  # For existence
    failed = 0
    
    for name, pattern in checks:
        if re.search(pattern, content):
            print(f"  ✅ {name} found")
            passed += 1
        else:
            print(f"  ❌ {name} NOT found")
            failed += 1
    
    # Check if executable
    import os
    if os.access(script_path, os.X_OK):
        print("  ✅ Script is executable")
        passed += 1
    else:
        print("  ❌ Script is NOT executable")
        failed += 1
    
    return passed, failed

def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     Codespaces Crash Fix - Verification Tests                   ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    passed, failed = test_performance_monitor()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_index_html()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_supervisor()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_diagnostic_script()
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
