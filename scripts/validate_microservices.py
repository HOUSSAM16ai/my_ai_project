#!/usr/bin/env python3
"""
Microservices Compliance Validator.
Checks the project against key rules from the Constitution.
"""

import sys
import os
import re
from pathlib import Path

# Constants
MICROSERVICES_DIR = Path("microservices")
APP_DIR = Path("app")
CONSTITUTION_FILE = Path("docs/architecture/MICROSERVICES_CONSTITUTION.md")

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg: str, color: str = RESET):
    print(f"{color}{msg}{RESET}")

def check_constitution_exists():
    if CONSTITUTION_FILE.exists():
        log(f"✅ Constitution found: {CONSTITUTION_FILE}", GREEN)
        return True
    else:
        log(f"❌ Constitution missing!", RED)
        return False

def check_microservices_structure():
    log("\n--- Checking Microservices Structure ---")
    if not MICROSERVICES_DIR.exists():
        log("❌ 'microservices' directory missing", RED)
        return False

    services = [d for d in MICROSERVICES_DIR.iterdir() if d.is_dir() and (d / "main.py").exists()]

    all_passed = True
    for service in services:
        log(f"Checking {service.name}...")

        # Rule 7: Containerization
        if (service / "Dockerfile").exists():
             log(f"  ✅ Dockerfile exists", GREEN)
        else:
             log(f"  ❌ Dockerfile missing (Rule 7)", RED)
             all_passed = False

        # Rule 56: Polyglot/Own DB (Check for DB file or logic)
        # Rudimentary check for local DB usage or config
        has_db = False
        for f in service.rglob("*.py"):
            content = f.read_text()
            if "SQLModel" in content or "sqlalchemy" in content:
                has_db = True
                break

        if has_db:
            log(f"  ✅ Has local DB logic (Rule 5)", GREEN)
        else:
            log(f"  ⚠️ No explicit DB logic found (might be stateless)", YELLOW)

    return all_passed

def check_direct_imports():
    log("\n--- Checking for Forbidden Imports (Independence) ---")
    # Rule 2: Independence. App should not import from microservices directly.

    violations = []

    for root, _, files in os.walk(APP_DIR):
        for file in files:
            if not file.endswith(".py"): continue
            path = Path(root) / file
            content = path.read_text()

            # Check for imports from microservices
            # Valid: from app.infrastructure.clients...
            # Invalid: from microservices.user_service...

            lines = content.splitlines()
            for i, line in enumerate(lines):
                if "from microservices" in line or "import microservices" in line:
                    # Exclude comments
                    if line.strip().startswith("#"): continue

                    violations.append(f"{path}:{i+1} -> {line.strip()}")

    if violations:
        log("❌ Found Direct Import Violations (Rule 2):", RED)
        for v in violations:
            log(f"  {v}", RED)
        return False
    else:
        log("✅ No direct imports from Core to Microservices found.", GREEN)
        return True

def main():
    log("🔒 Starting CogniForge Microservices Validator...", YELLOW)

    checks = [
        check_constitution_exists(),
        check_microservices_structure(),
        check_direct_imports()
    ]

    if all(checks):
        log("\n✅✅✅ ALL CHECKS PASSED. SYSTEM IS COMPLIANT. ✅✅✅", GREEN)
        sys.exit(0)
    else:
        log("\n❌❌❌ COMPLIANCE FAILURES DETECTED. ❌❌❌", RED)
        sys.exit(1)

if __name__ == "__main__":
    main()
