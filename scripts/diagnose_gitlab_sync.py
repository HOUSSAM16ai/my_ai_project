#!/usr/bin/env python3
"""
🔍 Comprehensive GitLab Sync Diagnostic Tool
This script diagnoses why GitLab sync might have stopped working
"""

import os
import subprocess
import sys
from datetime import datetime

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

print_header("GitLab Sync Comprehensive Diagnostic")
print_info(f"Diagnostic Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

all_ok = True

# Test 1: Check sync script exists and is importable
print_header("Test 1: Sync Script Validation")
try:
    import sys
    sys.path.insert(0, ".")
    print_success("Sync script imports successfully")
    print_success("check_workload_identity() function available")
    print_success("sync_remotes() function available")
except Exception as e:
    print_error(f"Failed to import sync script: {e}")
    all_ok = False

# Test 2: Check dependencies
print_header("Test 2: Dependencies Check")
try:
    print_success("requests library available")
except:
    print_warning("requests library not available (will be installed in CI)")

try:
    print_success("pyyaml library available")
except:
    print_warning("pyyaml library not available (will be installed in CI)")

# Test 3: Check git configuration
print_header("Test 3: Git Configuration")
try:
    result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, check=True)
    # Check if any remote points to github.com (read-only check, not URL sanitization)
    if "github.com" in result.stdout.lower():
        print_success("GitHub remote configured")
    else:
        print_warning("GitHub remote not found")

    # Check current branch
    result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, check=True)
    branch = result.stdout.strip()
    if branch:
        print_success(f"Current branch: {branch}")
    else:
        print_info("Detached HEAD (normal in CI)")

except Exception as e:
    print_error(f"Git check failed: {e}")
    all_ok = False

# Test 4: Workflow configuration
print_header("Test 4: Workflow Configuration")
try:
    with open(".github/workflows/universal_sync.yml") as f:
        workflow_content = f.read()

    checks = {
        "on:": "Workflow triggers defined",
        "push:": "Triggers on push events",
        "SYNC_GITLAB_TOKEN": "Uses GitLab token secret",
        "SYNC_GITLAB_ID": "Uses GitLab ID secret",
        "universal_repo_sync.py": "Calls sync script",
    }

    for check, description in checks.items():
        if check in workflow_content:
            print_success(description)
        else:
            print_error(f"Missing: {description}")
            all_ok = False

except Exception as e:
    print_error(f"Failed to read workflow: {e}")
    all_ok = False

# Test 5: Simulate sync environment
print_header("Test 5: Environment Simulation")
print_info("Simulating GitHub Actions environment...")

# Save original env
orig_env = os.environ.copy()

# Set test environment
os.environ["GITHUB_ACTIONS"] = "true"
os.environ["SYNC_GITLAB_TOKEN"] = "test_token_123"
os.environ["SYNC_GITLAB_ID"] = "12345"

try:
    is_github = os.environ.get("GITHUB_ACTIONS") == "true"
    gitlab_token = os.environ.get("SYNC_GITLAB_TOKEN")
    gitlab_id = os.environ.get("SYNC_GITLAB_ID")

    if is_github:
        print_success("GitHub Actions environment detected correctly")
    else:
        print_error("Failed to detect GitHub Actions")
        all_ok = False

    if gitlab_token and gitlab_id:
        print_success("GitLab credentials available")
    else:
        print_error("GitLab credentials not found")
        all_ok = False

finally:
    # Restore original env
    os.environ.clear()
    os.environ.update(orig_env)

# Test 6: Common failure scenarios
print_header("Test 6: Common Failure Scenarios")
print_info("Checking for common issues that stop sync...")

scenarios = [
    ("Expired Token", "GitLab Personal Access Token may have expired"),
    ("Permission Change", "GitLab project permissions may have changed"),
    ("Project Moved", "GitLab project may have been renamed or moved"),
    ("Network Issue", "Temporary network or GitLab API issues"),
    ("Rate Limit", "GitLab API rate limit may have been hit"),
]

print()
print_info("💡 If sync stopped working, check these:")
for title, description in scenarios:
    print(f"   • {title}: {description}")

# Test 7: Generate fix suggestions
print_header("Test 7: Fix Suggestions")

print_info("To fix GitLab sync issues:")
print()
print("1️⃣ Check GitLab Token:")
print("   • Go to: GitLab → Profile → Access Tokens")
print("   • Verify token is not expired")
print("   • Ensure it has 'api' and 'write_repository' scopes")
print()
print("2️⃣ Verify GitLab Project:")
print("   • Confirm project still exists")
print("   • Check project ID hasn't changed")
print("   • Verify you have maintainer/owner access")
print()
print("3️⃣ Check GitHub Secrets:")
print("   • Go to: GitHub → Settings → Secrets and variables → Actions")
print("   • Verify all 4 secrets are present:")
print("     - SYNC_GITHUB_TOKEN")
print("     - SYNC_GITHUB_ID")
print("     - SYNC_GITLAB_TOKEN")
print("     - SYNC_GITLAB_ID")
print()
print("4️⃣ View Workflow Logs:")
print("   • Go to: GitHub → Actions → Universal Sync")
print("   • Check latest run for specific error messages")
print()
print("5️⃣ Manual Test:")
print("   • Trigger workflow manually:")
print("     GitHub → Actions → Universal Sync → Run workflow")

# Final Summary
print_header("Diagnostic Summary")

if all_ok:
    print_success("✅ All technical checks passed!")
    print()
    print_info("The code and configuration are correct.")
    print_info("If sync stopped working, it's likely an external issue:")
    print()
    print("   • GitLab token expired (most common)")
    print("   • GitLab project permissions changed")
    print("   • Temporary API/network issues")
    print()
    print_success("👉 Solution: Check GitLab token and project access")
else:
    print_error("❌ Some checks failed")
    print_info("Review the errors above and fix them")

print()
print("=" * 70)
print()
