import ast
import os
import sys
from pathlib import Path

# Configuration
FORBIDDEN_PATTERNS = [
    {
        "pattern": "create_async_engine",
        "allowed_in": ["app/core/database.py", "migrations/env.py"],
        "message": "Direct use of 'create_async_engine' is forbidden. Use the shared factory in app.core.database.",
    },
    {
        "pattern": "async_sessionmaker",
        "allowed_in": ["app/core/database.py"],
        "message": "Direct use of 'async_sessionmaker' is forbidden. Use the shared factory in app.core.database.",
    },
]

def check_file(filepath: Path) -> list[str]:
    errors = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))

        for node in ast.walk(tree):
            # Check forbidden calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    for check in FORBIDDEN_PATTERNS:
                        if func_name == check["pattern"]:
                            # Check if allowed
                            allowed = False
                            for allowed_path in check["allowed_in"]:
                                if str(filepath).endswith(allowed_path):
                                    allowed = True
                                    break

                            if not allowed:
                                errors.append(f"{filepath}:{node.lineno} - {check['message']}")

                # Check imports (simplified) - logic for cross-service imports would go here
                # Implementation for cross-service import checks:
                # If file is in microservices/A, it cannot import microservices/B

        # Check Imports for Cross-Service violations
        parts = filepath.parts
        # Exclude tests from microservices check
        if "microservices" in parts and "tests" not in parts:
            try:
                ms_index = parts.index("microservices")
                current_service = parts[ms_index + 1]

                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        module_name = None
                        if isinstance(node, ast.Import):
                            for name in node.names:
                                module_name = name.name
                                _check_import(module_name, current_service, filepath, node.lineno, errors)
                        elif isinstance(node, ast.ImportFrom):
                            module_name = node.module
                            _check_import(module_name, current_service, filepath, node.lineno, errors)

            except IndexError:
                pass # Not deep enough in microservices folder

    except Exception as e:
        # Instead of swallowing, print error to stderr
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)

    return errors

def _check_import(module_name: str | None, current_service: str, filepath: Path, lineno: int, errors: list[str]):
    if not module_name:
        return

    if module_name.startswith("microservices."):
        parts = module_name.split(".")
        if len(parts) > 1:
            imported_service = parts[1]
            if imported_service != current_service:
                errors.append(f"{filepath}:{lineno} - Cross-service import forbidden: '{current_service}' importing from '{imported_service}'")

    # Check for direct import 'from microservices import X'
    if module_name == "microservices":
         errors.append(f"{filepath}:{lineno} - Direct import from 'microservices' is forbidden. Import specific service modules if (and only if) allowed.")

def main():
    root_dir = Path(".")
    all_errors = []

    # Walk through python files
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = Path(root) / file
                # Skip venv, .git, etc
                if any(p in filepath.parts for p in [".venv", "venv", ".git", "__pycache__"]):
                    continue

                file_errors = check_file(filepath)
                all_errors.extend(file_errors)

    if all_errors:
        print("Guardrails violations found:")
        for err in all_errors:
            print(err)
        sys.exit(1)
    else:
        print("Guardrails passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
