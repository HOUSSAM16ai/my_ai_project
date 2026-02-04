#!/usr/bin/env python3
import os
import sys

from dotenv import load_dotenv


def verify_secrets():
    print("Verifying critical secrets...")
    load_dotenv()

    # Check if running in CI/Dev environment
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    is_testing = os.environ.get("ENVIRONMENT") == "testing"
    is_gitpod = (
        os.environ.get("GITPOD_ENVIRONMENT_ID") is not None
        or os.environ.get("GITPOD_WORKSPACE_ID") is not None
    )
    is_codespaces = (
        os.environ.get("CODESPACES") == "true"
        or os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN") is not None
    )
    is_dev = os.environ.get("TESTING") == "1"

    required_secrets = ["DATABASE_URL", "SECRET_KEY"]

    # Only require Supabase secrets in production (not in CI, testing, Gitpod, or Codespaces)
    if not any([is_ci, is_testing, is_gitpod, is_codespaces, is_dev]):
        required_secrets.extend(["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"])

    missing = []
    for secret in required_secrets:
        val = os.environ.get(secret)
        if not val:
            missing.append(secret)
            print(f"[FAIL] {secret} is missing or empty.")
        else:
            # Print checksum (first 4 chars)
            checksum = val[:4] + "..." + val[-4:] if len(val) > 8 else "****"
            print(f"[OK] {secret} is set. ({checksum})")

    if missing:
        print("\nCRITICAL: Missing secrets!")
        sys.exit(1)
    else:
        print("\nAll critical secrets verified.")
        sys.exit(0)


if __name__ == "__main__":
    verify_secrets()
