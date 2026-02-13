#!/usr/bin/env python3
"""
CI Script to enforce Microservices Constitution (Boundary Checks).
Ensures no forbidden cross-service imports.
"""

import os
import re
import sys
from pathlib import Path

# Define forbidden patterns
# Format: (Scanning Directory, Forbidden Pattern in Import)
CHECKS = [
    # Rule 1: App (Gateway) must not import Microservices code directly
    ("app", r"^microservices\."),
    ("app", r"^microservices$"),
    # Rule 2: Microservices must not import App code (should use shared libs or nothing)
    ("microservices", r"^app\."),
    ("microservices", r"^app$"),
]


def check_file(filepath: Path) -> list[str]:
    errors = []
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        for i, raw_line in enumerate(lines):
            line = raw_line.strip()
            # Simple heuristic for imports
            if line.startswith("import ") or line.startswith("from "):
                # Extract the module being imported
                parts = line.split()
                if len(parts) > 1:
                    module = parts[1]

                    # Check against rules
                    for scan_dir, forbidden_pattern in CHECKS:
                        if str(filepath).startswith(scan_dir) and re.search(
                            forbidden_pattern, module
                        ):
                            errors.append(
                                f"{filepath}:{i + 1}: Forbidden import '{module}' matching '{forbidden_pattern}'"
                            )
    except Exception:
        pass  # Ignore binary files or read errors

    return errors


def main():
    root_dir = Path(".")
    all_errors = []

    print("🔍 Scanning for boundary violations...")

    for scan_dir, _ in CHECKS:
        start_path = root_dir / scan_dir
        if not start_path.exists():
            continue

        for root, _, files in os.walk(start_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = Path(root) / file
                    # Skip tests in the scan if needed, but strictness is better
                    errors = check_file(filepath)
                    all_errors.extend(errors)

    if all_errors:
        print("❌ Boundary Violations Found:")
        for err in all_errors:
            print(err)
        print(f"\nFound {len(all_errors)} violations. See docs/ARCH_MICROSERVICES_CONSTITUTION.md")
        sys.exit(1)
    else:
        print("✅ No boundary violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
