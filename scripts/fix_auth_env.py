#!/usr/bin/env python3
"""
Fix Authentication Environment Script.

This script repairs the "Login Disaster" by:
1. Creating a correct .env file with the provided PostgreSQL credentials.
2. Checking for conflicting JWT libraries (jwt vs PyJWT).
"""

import os
import sys
import subprocess

def fix_env_file():
    print("🔧 Fixing .env configuration...")

    # The credentials provided by the user
    env_content = (
        'DATABASE_URL="postgresql://postgres.aocnuqhxrhxgbfcgbxfy:199720242025%40HOUSSAMbenmerah@aws-1-eu-west-3.pooler.supabase.com:6543/postgres?sslmode=require"\n'
        'ENVIRONMENT="development"\n'
        'DEBUG=True\n'
        'LOG_LEVEL="DEBUG"\n'
        'SECRET_KEY="super-secret-key-for-houssam"\n'
    )

    env_path = os.path.join(os.getcwd(), ".env")

    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"✅ .env file created/updated at: {env_path}")
    print("   Database URL set to Supabase Pooler.")

def check_dependencies():
    print("🔍 Checking for dependency conflicts...")

    # Check if 'jwt' package is installed (conflicts with 'PyJWT')
    try:
        # We use pip freeze to check installed packages
        result = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
        installed = result.stdout.lower()

        has_pyjwt = "pyjwt" in installed
        has_jwt = "\njwt==" in installed or installed.startswith("jwt==")

        if has_jwt and has_pyjwt:
            print("❌ CRITICAL CONFLICT DETECTED: Both 'jwt' and 'PyJWT' are installed.")
            print("   The 'jwt' package overrides 'PyJWT' namespace, causing import errors.")
            print("   Action: Uninstalling 'jwt'...")
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "jwt"], check=True)
            print("✅ 'jwt' uninstalled. 'PyJWT' should now work correctly.")
        elif has_jwt:
            print("❌ WRONG LIBRARY DETECTED: 'jwt' is installed but 'PyJWT' is required.")
            print("   Action: Uninstalling 'jwt' and installing 'PyJWT'...")
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "jwt"], check=True)
            subprocess.run([sys.executable, "-m", "pip", "install", "PyJWT"], check=True)
            print("✅ Fixed: Swapped 'jwt' for 'PyJWT'.")
        else:
            print("✅ Dependency Check Passed: 'PyJWT' appears to be the only JWT library.")

    except Exception as e:
        print(f"⚠️ Failed to check dependencies: {e}")

def main():
    print("🚀 Starting Login Disaster Recovery...")
    fix_env_file()
    check_dependencies()
    print("\n✅ RECOVERY COMPLETE.")
    print("   Please restart your application server (uvicorn/docker) to apply changes.")

if __name__ == "__main__":
    main()
