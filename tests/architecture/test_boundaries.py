import ast
import os
from pathlib import Path

# List of known violations to be grandfathered in temporarily.
# Ideally, this list should be empty.
ALLOWED_VIOLATIONS = {
    "app/core/interfaces/common.py",
    "app/services/chat/graph/workflow.py",
    "app/services/chat/graph/search.py",
    "app/services/chat/graph/nodes/researcher.py",
    "app/services/chat/tools/content.py",
    "app/services/mcp/integrations.py",
    "app/integration/gateways/research.py",
    "app/integration/gateways/planning.py",
}


def test_app_does_not_import_microservices_logic():
    """
    Enforce architectural boundary: 'app' (Monolith/Orchestrator) must NOT import
    internal logic from 'microservices'. It should only communicate via HTTP/gRPC.

    Allowed exceptions (if any) would be strict type definitions or client wrappers
    if they are packaged separately (but here we assume strict separation).
    """
    app_dir = Path("app")
    violations = []

    for root, _, files in os.walk(app_dir):
        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = Path(root) / file

            # Skip allowed violations for now (Technical Debt)
            if str(filepath) in ALLOWED_VIOLATIONS:
                continue

            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                    # Basic check first to avoid parsing everything
                    if "microservices" not in content:
                        continue
                    tree = ast.parse(content, filename=str(filepath))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        # Check direct imports
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name.startswith("microservices"):
                                    violations.append(f"{filepath}: import {alias.name}")

                        # Check from ... import ...
                        elif (
                            isinstance(node, ast.ImportFrom)
                            and node.module
                            and node.module.startswith("microservices")
                        ):
                            violations.append(f"{filepath}: from {node.module} import ...")

            except Exception as e:
                # Skip files that can't be parsed (shouldn't happen in valid python code)
                print(f"Skipping {filepath}: {e}")

    if violations:
        error_msg = "\n".join(violations)
        raise AssertionError(
            f"Architecture Violation: 'app' imports from 'microservices':\n{error_msg}"
        )
