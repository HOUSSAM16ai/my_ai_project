import ast
import os

import pytest

APP_ROOT = "app"


def get_python_files(root_dir):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                yield os.path.join(root, file)


def test_no_microservice_imports_in_app():
    """
    Rule 1: Hard Boundary.
    The 'app' layer MUST NOT import from 'microservices'.
    Communication must be via Network Contracts (HTTP Clients).
    """
    violations = []

    for file_path in get_python_files(APP_ROOT):
        # Skip this test file itself if it were in app, but it's in tests.

        with open(file_path, encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=file_path)
            except SyntaxError:
                continue  # Skip files with syntax errors

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("microservices"):
                            violations.append(f"{file_path}: import {alias.name}")
                elif (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module.startswith("microservices")
                ):
                    violations.append(f"{file_path}: from {node.module} import ...")

    if violations:
        pytest.fail(
            f"Architecture Violation: 'app' layer imports 'microservices' code directly.\nFound {len(violations)} violations:\n"
            + "\n".join(violations)
        )
