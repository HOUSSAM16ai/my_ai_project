#!/usr/bin/env python3
import os
import sys

from dotenv import load_dotenv


def verify_secrets():
    print("Verifying critical secrets...")
    load_dotenv()

    required_secrets = ["DATABASE_URL", "SECRET_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]

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
