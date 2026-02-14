#!/usr/bin/env python3
"""
CI Script to enforce Microservices Constitution (Boundary Checks).
Ensures no forbidden cross-service imports.
"""

import ast
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Constants
MICROSERVICES_DIR = "microservices"
APP_DIR = "app"


def get_microservice_name(filepath: Path) -> str | None:
    """
    Extracts the microservice name from the file path.
    Returns None if the file is not inside a microservice.
    """
    parts = filepath.parts
    if len(parts) > 1 and parts[0] == MICROSERVICES_DIR:
        return parts[1]
    return None


def is_app_file(filepath: Path) -> bool:
    """Checks if the file is part of the main application (monolith/gateway)."""
    return filepath.parts[0] == APP_DIR


def check_import_violation(
    filepath: Path,
    module: str,
    lineno: int,
    is_app: bool,
    current_service: str | None,
) -> str | None:
    """
    Checks if an imported module violates boundary rules.
    """
    if not module:
        return None

    # Rule 1: App must not import Microservices
    if is_app and (
        module == MICROSERVICES_DIR or module.startswith(f"{MICROSERVICES_DIR}.")
    ):
        return (
            f"{filepath}:{lineno}: 🚨 App Code Violation: "
            f"Cannot import '{module}'. App must treat microservices as external systems."
        )

    # Rule 2: Microservices Isolation
    if current_service:
        # 2a: Must not import App
        if module == APP_DIR or module.startswith(f"{APP_DIR}."):
            return (
                f"{filepath}:{lineno}: 🚨 Microservice Violation: "
                f"'{current_service}' cannot import '{module}'. Microservices must be decoupled from App core."
            )

        # 2b: Must not import Sibling Microservices
        if module.startswith(f"{MICROSERVICES_DIR}."):
            parts = module.split(".")
            if len(parts) >= 2:
                target_service = parts[1]
                # Allow self-reference
                if target_service == current_service:
                    return None

                # Verify target is actually a microservice (and not a shared lib if one existed)
                # Since we don't have a shared lib currently, any cross-service import is banned.
                return (
                    f"{filepath}:{lineno}: 🚨 Microservice Isolation Violation: "
                    f"'{current_service}' cannot import '{target_service}' via '{module}'. "
                    f"Communication must be via HTTP contracts only."
                )

        # 2c: Must not import 'microservices' root package directly to avoid 'microservices.other_service' usage
        if module == MICROSERVICES_DIR:
            return (
                f"{filepath}:{lineno}: 🚨 Ambiguous Import Violation: "
                f"'{current_service}' cannot import '{module}' root. Import specific modules from your own service instead."
            )

    return None


class ImportVisitor(ast.NodeVisitor):
    def __init__(self, filepath: Path, is_app: bool, current_service: str | None):
        self.filepath = filepath
        self.is_app = is_app
        self.current_service = current_service
        self.errors: list[str] = []

    def visit_Import(self, node):
        for alias in node.names:
            error = check_import_violation(
                self.filepath,
                alias.name,
                node.lineno,
                self.is_app,
                self.current_service,
            )
            if error:
                self.errors.append(error)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # Handle 'from module import ...'
        if node.module:
            error = check_import_violation(
                self.filepath,
                node.module,
                node.lineno,
                self.is_app,
                self.current_service,
            )
            if error:
                self.errors.append(error)

        # We don't need to check relative imports (level > 0) usually,
        # unless they escape the service boundary, but that's hard to catch with AST alone
        # without resolving paths. Assuming standard structure, relative imports stay local.

        self.generic_visit(node)


def check_file(filepath: Path) -> list[str]:
    """Parses a file and checks imports using AST."""
    errors = []
    is_app = is_app_file(filepath)
    current_service = get_microservice_name(filepath)

    if not is_app and not current_service:
        return []  # File is neither app nor microservice (e.g. tools, root scripts)

    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        visitor = ImportVisitor(filepath, is_app, current_service)
        visitor.visit(tree)
        errors.extend(visitor.errors)

    except SyntaxError as e:
        errors.append(f"{filepath}: ⚠️ Syntax Error: {e}")
    except Exception as e:
        errors.append(f"{filepath}: ⚠️ Error parsing file: {e}")

    return errors


def main():
    root_dir = Path(".")
    all_errors = []

    logger.info("🔍 Scanning for boundary violations (Strict AST Mode)...")

    # Directories to scan
    scan_dirs = [APP_DIR, MICROSERVICES_DIR]

    for scan_dir in scan_dirs:
        start_path = root_dir / scan_dir
        if not start_path.exists():
            continue

        for path in start_path.rglob("*.py"):
            # Exclude tests/ directories if needed, but usually strict is better.
            # However, tests might mock things. For now, we enforce strictness everywhere.
            errors = check_file(path)
            all_errors.extend(errors)

    if all_errors:
        logger.error("❌ Boundary Violations Found:")
        for err in all_errors:
            logger.error(err)
        logger.error(
            f"\nFound {len(all_errors)} violations. \n"
            "See docs/ARCH_MICROSERVICES_CONSTITUTION.md for rules."
        )
        sys.exit(1)
    else:
        logger.info("✅ No boundary violations found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
