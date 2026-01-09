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
    {
        "pattern": "print",
        "allowed_in": ["scripts/*", "cli.py", "tests/*", "examples/*", "dev_setup.py"],
        "message": "Use of 'print()' is forbidden in application code. Use 'app.core.logging' instead.",
    },
]

# Legacy exemptions to allow gradual refactoring.
# These files are KNOWN to violate rules. New files must not be added here.
LEGACY_EXEMPTIONS = {
    "app/core/gateway/policy.py": ["Any"],
    "app/core/gateway/service.py": ["Any"],
    "app/core/gateway/cache.py": ["Any"],
    "app/core/gateway/providers/anthropic.py": ["Any"],
    "app/core/gateway/providers/base.py": ["Any"],
    "app/core/gateway/providers/openai.py": ["Any"],
    "app/core/gateway/protocols/grpc.py": ["Any"],
    "app/core/gateway/protocols/rest.py": ["Any"],
    "app/core/gateway/protocols/graphql.py": ["Any"],
    "app/core/gateway/protocols/base.py": ["Any"],
    "app/core/gateway/protocols/cache.py": ["Any"],
    "app/core/gateway/strategies/implementations.py": ["Any"],
    "app/core/domain/models.py": ["Any"],
    "app/core/resilience/circuit_breaker.py": ["Any"],
    "app/core/resilience/composite.py": ["Any"],
    "app/core/resilience/bulkhead.py": ["Any"],
    "app/tooling/repository_map.py": ["print"],
    "app/api/routers/security.py": ["db_import"],
    "app/api/routers/crud.py": ["db_import", "Any"],
    "app/api/routers/overmind.py": ["db_import"],
    "app/api/routers/customer_chat.py": ["db_import"],
    "app/api/routers/admin.py": ["db_import"],
    "app/api/routers/ums.py": ["db_import"],
    "app/api/routers/system/__init__.py": ["Any"],
    "app/monitoring/metrics.py": ["Any"],
    "app/monitoring/dashboard.py": ["Any"],
    "app/monitoring/performance.py": ["Any"],
    "app/monitoring/alerts.py": ["Any"],
    "app/monitoring/exporters.py": ["Any"],
    "infra/pipelines/data_quality_checkpoint.py": ["Any"],
    "microservices/orchestrator_service/database.py": ["create_async_engine"],
    "microservices/planning_agent/database.py": ["create_async_engine"],
    "microservices/memory_agent/database.py": ["create_async_engine"],
}

def check_file(filepath: Path) -> list[str]:
    errors = []
    str_path = str(filepath).replace(os.sep, "/")
    exemptions = LEGACY_EXEMPTIONS.get(str_path, [])

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))
        parts = filepath.parts

        # 1. Check Function Calls (Forbidden Patterns)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    for check in FORBIDDEN_PATTERNS:
                        if func_name == check["pattern"]:
                            # Check exemptions
                            if check["pattern"] in exemptions:
                                continue

                            # Check allow list (glob-like)
                            allowed = False
                            for allowed_pattern in check["allowed_in"]:
                                if _match_path(filepath, allowed_pattern):
                                    allowed = True
                                    break

                            if not allowed:
                                errors.append(f"{filepath}:{node.lineno} - {check['message']}")

        # 2. Architecture & Boundary Checks

        # A. Microservices Isolation
        if "microservices" in parts and "tests" not in parts:
            try:
                ms_index = parts.index("microservices")
                # Ensure we are inside a service folder
                if ms_index + 1 < len(parts):
                    current_service = parts[ms_index + 1]

                    for node in ast.walk(tree):
                        if isinstance(node, (ast.Import, ast.ImportFrom)):
                            _check_microservice_imports(node, current_service, filepath, errors, exemptions)
            except ValueError:
                pass

        # B. App (Monolith) Isolation
        # 'app' code (excluding core) should not import microservices
        if "app" in parts and "core" not in parts and "tests" not in parts:
             for node in ast.walk(tree):
                 if isinstance(node, (ast.Import, ast.ImportFrom)):
                     _check_monolith_imports(node, filepath, errors)

        # C. Admin UI / API Layer DB Ban
        if _match_path(filepath, "app/api/routers/*") or _match_path(filepath, "app/services/admin/*"):
             for node in ast.walk(tree):
                 if isinstance(node, (ast.Import, ast.ImportFrom)):
                     _check_admin_db_imports(node, filepath, errors, exemptions)

        # 3. Type Safety (No Any)
        if "tests" not in parts and "scripts" not in parts and "Any" not in exemptions:
             for node in ast.walk(tree):
                 if isinstance(node, ast.Name) and node.id == "Any":
                     errors.append(f"{filepath}:{node.lineno} - Use of 'Any' is forbidden. Use specific types or 'object'.")
                 elif isinstance(node, ast.Attribute) and node.attr == "Any":
                     errors.append(f"{filepath}:{node.lineno} - Use of 'Any' is forbidden.")


    except Exception as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)

    return errors

def _match_path(filepath: Path, pattern: str) -> bool:
    """Simple glob matcher for paths."""
    from fnmatch import fnmatch
    # Convert filepath to string and generic POSIX style for matching
    s_path = str(filepath).replace(os.sep, "/")
    if pattern.endswith("*"):
        return s_path.startswith(pattern[:-1]) or fnmatch(s_path, pattern)
    return fnmatch(s_path, pattern)

def _check_microservice_imports(node, current_service, filepath, errors, exemptions):
    module_name = _get_import_module(node)
    if not module_name:
        return

    # Rule: No cross-service imports
    if module_name.startswith("microservices."):
        parts = module_name.split(".")
        if len(parts) > 1:
            imported_service = parts[1]
            if imported_service != current_service:
                errors.append(f"{filepath}:{node.lineno} - Cross-service import forbidden: '{current_service}' importing from '{imported_service}'")

    # Rule: No importing app.services (Monolith Leak)
    if module_name.startswith("app.services"):
        errors.append(f"{filepath}:{node.lineno} - Microservice cannot import 'app.services' (Monolith Leak).")

    # Rule: No importing app.api (Layer Violation)
    if module_name.startswith("app.api"):
        errors.append(f"{filepath}:{node.lineno} - Microservice cannot import 'app.api' (Layer Violation).")

    # Rule: Only app.core is allowed from app
    if module_name.startswith("app.") and not module_name.startswith("app.core"):
        errors.append(f"{filepath}:{node.lineno} - Microservice can only import from 'app.core'. Found: '{module_name}'")


def _check_monolith_imports(node, filepath, errors):
    module_name = _get_import_module(node)
    if not module_name:
        return

    # Rule: Monolith cannot import microservices (Use HTTP/Event Bus)
    if module_name.startswith("microservices"):
        errors.append(f"{filepath}:{node.lineno} - Monolith cannot import 'microservices' directly. Use APIs.")

def _check_admin_db_imports(node, filepath, errors, exemptions):
    if "db_import" in exemptions:
        return

    module_name = _get_import_module(node)
    if not module_name:
        return

    forbidden_db = ["sqlalchemy", "sqlmodel", "alembic", "app.core.database"]

    for db_mod in forbidden_db:
        if module_name.startswith(db_mod) or module_name == db_mod:
             errors.append(f"{filepath}:{node.lineno} - UI/API Layer cannot import DB module '{module_name}'. Use Services/Boundaries.")

def _get_import_module(node) -> str | None:
    if isinstance(node, ast.Import):
        # Return first one for simplicity, though could be multiple
        return node.names[0].name
    elif isinstance(node, ast.ImportFrom):
        return node.module
    return None

def main():
    root_dir = Path(".")
    all_errors = []

    print("🛡️  Running Architecture Guardrails...")

    # Walk through python files
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = Path(root) / file
                # Skip venv, .git, etc
                if any(p in filepath.parts for p in [".venv", "venv", ".git", "__pycache__"]):
                    continue

                # Skip migrations
                if "migrations" in filepath.parts:
                    continue

                file_errors = check_file(filepath)
                all_errors.extend(file_errors)

    if all_errors:
        print("\n❌ Guardrails violations found:")
        for err in all_errors:
            print(err)
        sys.exit(1)
    else:
        print("\n✅ Guardrails passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
