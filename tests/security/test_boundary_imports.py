import ast
from pathlib import Path


def _imports_module(tree: ast.AST, module_fragment: str) -> bool:
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and module_fragment in node.module
        ):
            return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if module_fragment in alias.name:
                    return True
    return False


def test_customer_boundary_does_not_import_admin_boundary() -> None:
    path = Path("app/services/boundaries/customer_chat_boundary_service.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))

    assert _imports_module(tree, "admin_chat_boundary_service") is False
