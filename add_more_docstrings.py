#!/usr/bin/env python3
"""
Add More Module Docstrings - Phase 2
Adds docstrings to additional files.
"""
from pathlib import Path


DOCSTRINGS = {
    "app/boundaries/policy/layers.py": '"""Policy Layers - Layered policy enforcement architecture."""',
    "app/boundaries/policy/main.py": '"""Policy Main - Policy subsystem entry point."""',
    "app/cli.py": '"""CLI - Command-line interface for application management."""',
    "app/cli_handlers/db_cli.py": '"""Database CLI - Database management commands."""',
    "app/cli_handlers/maintenance_cli.py": '"""Maintenance CLI - System maintenance commands."""',
    "app/cli_handlers/migrate_cli.py": '"""Migration CLI - Database migration commands."""',
    "app/config/__init__.py": '"""Configuration - Application configuration management."""',
    "app/config/dependencies.py": '"""Dependencies - Dependency injection configuration."""',
    "app/core/__init__.py": '"""Core - Core application utilities and abstractions."""',
    "app/core/cli_logging.py": '"""CLI Logging - Logging configuration for CLI commands."""',
    "app/core/common_imports.py": '"""Common Imports - Frequently used imports and utilities."""',
    "app/core/database.py": '"""Database - Database connection and session management."""',
    "app/core/error_messages.py": '"""Error Messages - Standardized error message formatting."""',
    "app/core/gateway/__init__.py": '"""Gateway - API gateway and routing abstractions."""',
    "app/core/interfaces/__init__.py": '"""Interfaces - Core interface definitions and protocols."""',
    "app/core/kernel_v2/__init__.py": '"""Kernel V2 - Application kernel implementation."""',
    "app/core/patterns/__init__.py": '"""Patterns - Design pattern implementations."""',
    "app/core/protocols.py": '"""Protocols - Protocol definitions for type checking."""',
    "app/domain/__init__.py": '"""Domain - Domain layer with business entities and rules."""',
    "app/infrastructure/__init__.py": '"""Infrastructure - Infrastructure layer implementations."""',
}


def add_docstring(filepath: str, docstring: str) -> bool:
    """Add docstring to file if missing."""
    try:
        path = Path(filepath)
        if not path.exists():
            return False

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if content.strip().startswith('"""') or content.strip().startswith("'''"):
            return True

        lines = content.splitlines(keepends=True)
        insert_pos = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                insert_pos = i
                break

        new_content = (
            "".join(lines[:insert_pos]) +
            docstring + "\n" +
            "".join(lines[insert_pos:])
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ {filepath}")
        return True

    except Exception:
        return False


def main():
    """Main execution."""
    print("📚 Adding More Module Docstrings - Phase 2")
    print("=" * 80)

    success_count = 0
    for filepath, docstring in DOCSTRINGS.items():
        if add_docstring(filepath, docstring):
            success_count += 1

    print(f"\n✅ Processed {success_count}/{len(DOCSTRINGS)} files")
    print("=" * 80)


if __name__ == "__main__":
    main()
