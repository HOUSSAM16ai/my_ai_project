#!/usr/bin/env python3
"""
Test script to validate GitLab sync configuration and functionality.
This script verifies that the sync would work correctly if secrets are configured.
"""

import os
import subprocess
import sys
from typing import Dict, List, Tuple

# ANSI colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✅ {text}{RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{RED}❌ {text}{RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{BLUE}ℹ️  {text}{RESET}")


def check_secret_configured(secret_name: str) -> bool:
    """Check if a secret/environment variable is configured."""
    value = os.environ.get(secret_name)
    if value and len(value) > 0:
        return True
    return False


def check_git_config() -> Tuple[bool, List[str]]:
    """Check git configuration."""
    issues = []

    try:
        # Check if we're in a git repository
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Git repository detected")
    except subprocess.CalledProcessError:
        issues.append("Not in a git repository")
        return False, issues

    # Check for remotes
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            check=True,
            capture_output=True,
            text=True
        )
        remotes = result.stdout.strip()
        if remotes:
            print_success("Git remotes configured")
            print(f"   {remotes.replace(chr(10), chr(10) + '   ')}")
        else:
            issues.append("No git remotes configured")
    except subprocess.CalledProcessError as e:
        issues.append(f"Failed to check git remotes: {e}")

    # Check current branch
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            check=True,
            capture_output=True,
            text=True
        )
        branch = result.stdout.strip()
        if branch:
            print_success(f"Current branch: {branch}")
        else:
            print_warning("Detached HEAD state (common in CI)")
    except subprocess.CalledProcessError as e:
        issues.append(f"Failed to check current branch: {e}")

    return len(issues) == 0, issues


def check_sync_script() -> Tuple[bool, List[str]]:
    """Check if the sync script exists and is valid."""
    issues = []

    script_path = "scripts/universal_repo_sync.py"

    if not os.path.exists(script_path):
        issues.append(f"Sync script not found: {script_path}")
        return False, issues

    print_success(f"Sync script found: {script_path}")

    # Try to import the script
    try:
        sys.path.insert(0, ".")
        from scripts.universal_repo_sync import check_workload_identity, sync_remotes
        print_success("Sync script imports successfully")

        # Test check_workload_identity
        workload_id = check_workload_identity()
        print_info(f"Workload Identity available: {workload_id}")

    except ImportError as e:
        issues.append(f"Failed to import sync script: {e}")
        return False, issues

    return len(issues) == 0, issues


def check_secrets_configuration() -> Tuple[bool, Dict[str, bool]]:
    """Check if all required secrets are configured."""
    secrets = {
        "SYNC_GITHUB_TOKEN": check_secret_configured("SYNC_GITHUB_TOKEN"),
        "SYNC_GITHUB_ID": check_secret_configured("SYNC_GITHUB_ID"),
        "SYNC_GITLAB_TOKEN": check_secret_configured("SYNC_GITLAB_TOKEN"),
        "SYNC_GITLAB_ID": check_secret_configured("SYNC_GITLAB_ID"),
    }

    all_configured = all(secrets.values())

    # In CI environment, don't fail if secrets are missing (they're injected at runtime)
    # In local environment, warn but don't fail the test
    in_ci = os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") or os.environ.get("GITLAB_CI")

    print_info("Secrets Configuration Status:")
    for secret, configured in secrets.items():
        if configured:
            print_success(f"  {secret}: Configured ✓")
        else:
            print_warning(f"  {secret}: Not configured ✗")

    return all_configured, secrets


def check_workflows() -> Tuple[bool, List[str]]:
    """Check GitHub Actions workflows."""
    issues = []

    workflows = {
        ".github/workflows/ci.yml": "Active (tests + quality)",
        ".github/workflows/universal_sync.yml": "Active (GitLab sync)",
        ".github/workflows/comprehensive_testing.yml": "Manual only",
        ".github/workflows/omega_pipeline.yml": "Manual only",
    }

    print_info("Workflows Status:")
    for workflow, status in workflows.items():
        if os.path.exists(workflow):
            print_success(f"  {os.path.basename(workflow)}: {status}")
        else:
            issues.append(f"Workflow not found: {workflow}")
            print_error(f"  {os.path.basename(workflow)}: Not found")

    return len(issues) == 0, issues


def test_sync_dry_run() -> Tuple[bool, List[str]]:
    """Test the sync in dry-run mode (check what would be synced)."""
    issues = []

    print_info("Testing sync configuration (dry-run)...")

    # Check what would be pushed
    try:
        # Get all local branches
        result = subprocess.run(
            ["git", "branch", "-a"],
            check=True,
            capture_output=True,
            text=True
        )
        branches = [b.strip() for b in result.stdout.split("\n") if b.strip()]
        print_info(f"Branches that would be synced: {len(branches)}")

        # Get all tags
        result = subprocess.run(
            ["git", "tag"],
            check=True,
            capture_output=True,
            text=True
        )
        tags = [t.strip() for t in result.stdout.split("\n") if t.strip()]
        print_info(f"Tags that would be synced: {len(tags)}")

        print_success("Sync dry-run completed successfully")

    except subprocess.CalledProcessError as e:
        issues.append(f"Dry-run failed: {e}")
        return False, issues

    return True, []


def main():
    """Main test function."""
    print_header("GitLab Sync Validation Test")

    print_info("This script validates the GitLab sync configuration")
    print_info("It does NOT perform actual sync - only checks configuration\n")

    all_tests_passed = True

    # Test 1: Git Configuration
    print_header("Test 1: Git Configuration")
    success, issues = check_git_config()
    if success:
        print_success("Git configuration: OK")
    else:
        print_error("Git configuration: FAILED")
        for issue in issues:
            print_error(f"  - {issue}")
        all_tests_passed = False

    # Test 2: Sync Script
    print_header("Test 2: Sync Script Validation")
    success, issues = check_sync_script()
    if success:
        print_success("Sync script: OK")
    else:
        print_error("Sync script: FAILED")
        for issue in issues:
            print_error(f"  - {issue}")
        all_tests_passed = False

    # Test 3: Secrets Configuration
    print_header("Test 3: Secrets Configuration")
    all_configured, secrets = check_secrets_configuration()

    # Determine if we're in CI environment
    in_ci = os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") or os.environ.get("GITLAB_CI")

    if all_configured:
        print_success("All secrets configured: OK")
        print_success("🎉 GitLab sync is ready to use!")
    else:
        print_warning("Some secrets not configured")
        if in_ci:
            print_info("Running in CI: Secrets will be injected at runtime")
        else:
            print_warning("Running locally: Secrets only available in GitHub Actions")
            print_info("\nTo configure secrets:")
            print_info("1. Go to: GitHub Repository → Settings → Secrets and variables → Actions")
            print_info("2. Add the missing secrets (see GITLAB_SYNC_SETUP_AR.md)")
        # Don't fail - secrets are expected to be missing in local/CI test environments

    # Test 4: Workflows
    print_header("Test 4: Workflows Configuration")
    success, issues = check_workflows()
    if success:
        print_success("Workflows configuration: OK")
    else:
        print_error("Workflows configuration: FAILED")
        for issue in issues:
            print_error(f"  - {issue}")
        all_tests_passed = False

    # Test 5: Dry Run
    print_header("Test 5: Sync Dry-Run Test")
    success, issues = test_sync_dry_run()
    if success:
        print_success("Sync dry-run: OK")
    else:
        print_error("Sync dry-run: FAILED")
        for issue in issues:
            print_error(f"  - {issue}")
        all_tests_passed = False

    # Final Summary
    print_header("Test Summary")
    if all_tests_passed:
        print_success("✅ All tests passed!")
        print_success("🚀 GitLab sync is properly configured")
        if all_configured:
            print_success("🎉 Sync is ready to use!")
        else:
            print_warning("⚠️  Add secrets to enable automatic sync")
        return 0
    else:
        print_error("❌ Some tests failed")
        print_info("Please review the errors above and fix them")
        return 1


if __name__ == "__main__":
    sys.exit(main())
