#!/usr/bin/env python3
"""
Check if GitHub Actions secrets are configured for GitLab sync.
This runs in GitHub Actions environment.
"""

import os
import sys


def check_secret(name):
    """Check if a secret is configured (non-empty)."""
    value = os.environ.get(name, "")
    if value and len(value) > 0:
        # Show first 4 chars only for security
        masked = value[:4] + "..." if len(value) > 4 else "***"
        return True, masked
    return False, "Not set"


print("=" * 70)
print("Checking GitHub Actions Secrets for GitLab Sync")
print("=" * 70)
print()

secrets = {
    "SYNC_GITHUB_TOKEN": "GitHub Personal Access Token",
    "SYNC_GITHUB_ID": "GitHub Repository ID",
    "SYNC_GITLAB_TOKEN": "GitLab Personal Access Token",
    "SYNC_GITLAB_ID": "GitLab Project ID",
}

all_configured = True
for secret_name, description in secrets.items():
    configured, value = check_secret(secret_name)
    status = "✅ Configured" if configured else "❌ Not configured"
    print(f"{status} - {secret_name}")
    print(f"   Description: {description}")
    if configured:
        print(f"   Value: {value}")
    print()
    if not configured:
        all_configured = False

print("=" * 70)
if all_configured:
    print("✅ All secrets are configured!")
    print("🚀 GitLab sync should be working")
    sys.exit(0)
else:
    print("⚠️  Some secrets are missing")
    print("ℹ️  Note: Secrets are only available in GitHub Actions environment")
    sys.exit(0)  # Don't fail in local environment
