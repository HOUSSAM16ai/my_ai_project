#!/usr/bin/env python3
"""
Add Missing Module Docstrings
Adds docstrings to files that are missing them.
"""
import json
from pathlib import Path


DOCSTRINGS = {
    "app/ai/application/__init__.py": '"""AI Application Layer - Service Interfaces and Implementations."""',
    "app/ai/application/payload_builder.py": '"""Payload Builder - Constructs AI model request payloads."""',
    "app/ai/application/response_normalizer.py": '"""Response Normalizer - Standardizes AI model responses."""',
    "app/api/exceptions.py": '"""API Exceptions - Custom exception classes for API errors."""',
    "app/api/main.py": '"""API Main Module - API router configuration and setup."""',
    "app/api_docs.py": '"""API Documentation - OpenAPI documentation configuration."""',
    "app/blueprints/__init__.py": '"""Blueprints - Modular API route organization."""',
    "app/blueprints/security_blueprint.py": '"""Security Blueprint - Security-related API endpoints."""',
    "app/boundaries/data/core.py": '"""Data Boundary Core - Core data access abstractions."""',
    "app/boundaries/data/database.py": '"""Data Boundary Database - Database access layer."""',
    "app/boundaries/data/events.py": '"""Data Boundary Events - Event sourcing and streaming."""',
    "app/boundaries/data/saga.py": '"""Data Boundary Saga - Distributed transaction coordination."""',
    "app/boundaries/policy/__init__.py": '"""Policy Boundary - Policy enforcement and governance."""',
    "app/boundaries/policy/auth.py": '"""Policy Auth - Authentication and authorization policies."""',
    "app/boundaries/policy/compliance.py": '"""Policy Compliance - Compliance and regulatory policies."""',
    "app/boundaries/policy/engine.py": '"""Policy Engine - Policy evaluation and enforcement engine."""',
    "app/boundaries/policy/governance.py": '"""Policy Governance - Data governance and access control."""',
}


def add_docstring(filepath: str, docstring: str) -> bool:
    """Add docstring to file if missing."""
    try:
        path = Path(filepath)
        if not path.exists():
            print(f"⚠️  File not found: {filepath}")
            return False

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if already has docstring
        if content.strip().startswith('"""') or content.strip().startswith("'''"):
            print(f"✓ Already has docstring: {filepath}")
            return True

        # Add docstring at the beginning
        lines = content.splitlines(keepends=True)
        
        # Find first non-comment, non-blank line
        insert_pos = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                insert_pos = i
                break

        # Insert docstring
        new_content = (
            "".join(lines[:insert_pos]) +
            docstring + "\n" +
            "".join(lines[insert_pos:])
        )

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"✅ Added docstring: {filepath}")
        return True

    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False


def main():
    """Main execution."""
    print("📚 Adding Missing Module Docstrings")
    print("=" * 80)

    success_count = 0
    for filepath, docstring in DOCSTRINGS.items():
        if add_docstring(filepath, docstring):
            success_count += 1

    print(f"\n✅ Processed {success_count}/{len(DOCSTRINGS)} files")
    print("=" * 80)


if __name__ == "__main__":
    main()
