#!/usr/bin/env python3
import os
import sys

from dotenv import load_dotenv


def verify_secrets():
    print("Verifying critical secrets...")
    load_dotenv()

    # Check if running in CI environment
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    is_testing = os.environ.get("ENVIRONMENT") == "testing"

    required_secrets = ["DATABASE_URL", "SECRET_KEY"]

    # Only require Supabase secrets in production
    if not is_ci and not is_testing:
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
