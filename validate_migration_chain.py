#!/usr/bin/env python3
"""
Migration Chain Validator
========================

This script validates the integrity of Alembic migration files by checking:
1. All down_revision references point to existing revisions
2. There is exactly one head (latest migration)
3. No circular dependencies exist
4. The chain is properly connected

Usage:
    python validate_migration_chain.py

Exit codes:
    0 - All validations passed
    1 - Validation errors found
"""

import os
import re
import sys
from pathlib import Path


def extract_revision_info(filepath):
    """Extract revision and down_revision from a migration file."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # Extract revision ID
    revision_match = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)

    # Extract down_revision
    down_match = re.search(
        r"^down_revision\s*=\s*(['\"]([^'\"]+)['\"]|None)", content, re.MULTILINE
    )

    if not revision_match:
        return None

    revision = revision_match.group(1)
    down_revision = None

    if down_match:
        if "None" not in down_match.group(0):
            down_revision = down_match.group(2) if down_match.group(2) else None

    return {
        "revision": revision,
        "down_revision": down_revision,
        "file": os.path.basename(filepath),
    }


def validate_migration_chain():
    """Validate the entire migration chain."""
    # Find migrations directory
    script_dir = Path(__file__).parent
    migrations_dir = script_dir / "migrations" / "versions"

    if not migrations_dir.exists():
        print(f"❌ ERROR: Migrations directory not found: {migrations_dir}")
        return False

    print("=" * 80)
    print("🔍 MIGRATION CHAIN VALIDATION")
    print("=" * 80)
    print()

    # Scan all migration files
    migrations = {}
    for filepath in migrations_dir.glob("*.py"):
        if filepath.name == "__init__.py":
            continue

        info = extract_revision_info(filepath)
        if info:
            migrations[info["revision"]] = {
                "down_revision": info["down_revision"],
                "file": info["file"],
            }

    if not migrations:
        print("⚠️  WARNING: No migration files found")
        return True

    print(f"📁 Found {len(migrations)} migration file(s)\n")

    # Check 1: All down_revision references exist
    print("🔗 Checking references...")
    all_ok = True
    for rev, info in migrations.items():
        down = info["down_revision"]
        if down and down not in migrations:
            print(f"  ❌ ERROR: {rev} references non-existent '{down}'")
            print(f"     File: {info['file']}")
            all_ok = False

    if all_ok:
        print("  ✅ All references are valid\n")
    else:
        print()
        return False

    # Check 2: Find heads (migrations with no children)
    print("🎯 Finding head(s)...")
    children = set()
    for _rev, info in migrations.items():
        if info["down_revision"]:
            children.add(info["down_revision"])

    heads = [rev for rev in migrations if rev not in children]

    if len(heads) == 0:
        print("  ❌ ERROR: No head found (circular dependency?)")
        return False
    elif len(heads) > 1:
        print(f"  ⚠️  WARNING: Found {len(heads)} heads (expected 1):")
        for head in heads:
            print(f"     - {head}")
        print()
        print("  This usually means you have divergent migration branches.")
        print("  Consider creating a merge migration.")
        print()
        return False
    else:
        head = heads[0]
        print(f"  ✅ Found exactly 1 head: {head}")
        print(f"     File: {migrations[head]['file']}\n")

    # Check 3: Trace the chain from head
    print("🔄 Tracing migration chain...")
    current = head
    chain = [current]
    max_depth = 100
    depth = 0

    while current in migrations and migrations[current]["down_revision"] and depth < max_depth:
        current = migrations[current]["down_revision"]

        if current in chain:
            print("  ❌ ERROR: Circular reference detected!")
            print(f"     Chain: {' → '.join(chain)} → {current}")
            return False

        chain.append(current)
        depth += 1

    if depth >= max_depth:
        print(f"  ⚠️  WARNING: Chain depth exceeded {max_depth}")
        return False

    print(f"  ✅ Chain is valid ({len(chain)} migrations)\n")

    # Display the chain
    print("📋 Migration chain (newest to oldest):")
    for i, rev in enumerate(chain):
        indent = "  " * i
        symbol = "→" if i > 0 else "⭐"
        tag = " (HEAD)" if i == 0 else " (BASE)" if i == len(chain) - 1 else ""
        print(f"  {indent}{symbol} {rev}{tag}")
    print()

    # Final summary
    print("=" * 80)
    print("✅ MIGRATION CHAIN VALIDATION PASSED!")
    print("=" * 80)
    print(f"""
Summary:
  • Total migrations: {len(migrations)}
  • Chain length: {len(chain)}
  • Head: {head}
  • All references: Valid ✓
  • Circular dependencies: None ✓
  • Ready to migrate: Yes ✓
""")

    return True


def main():
    """Main entry point."""
    try:
        success = validate_migration_chain()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
