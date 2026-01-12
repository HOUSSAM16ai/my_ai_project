"""أدوات مساندة لتحميل وفحص عقود OpenAPI بشكل خفيف."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


def load_contract_paths(spec_path: Path) -> set[str]:
    """تحميل مسارات عقد OpenAPI من ملف JSON أو YAML بأسلوب خفيف وآمن."""

    if not spec_path.exists():
        return set()

    if spec_path.suffix.lower() == ".json":
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return _extract_paths_from_json(payload)
        return set()

    return _extract_paths_from_yaml(spec_path.read_text(encoding="utf-8"))


def load_contract_operations(spec_path: Path) -> dict[str, set[str]]:
    """تحميل العمليات لكل مسار ضمن عقد OpenAPI بصيغة خفيفة."""

    if not spec_path.exists():
        return {}

    if spec_path.suffix.lower() == ".json":
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return _extract_operations_from_json(payload)
        return {}

    return _extract_operations_from_yaml(spec_path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class ContractComparisonReport:
    """تقرير يوضح الفجوات بين العقد ومخطط التشغيل الفعلي."""

    missing_paths: set[str]
    missing_operations: dict[str, set[str]]

    def is_clean(self) -> bool:
        """يتحقق مما إذا كان التقرير خالياً من الفجوات."""

        return not self.missing_paths and not self.missing_operations


def _extract_paths_from_json(payload: dict[str, object]) -> set[str]:
    """استخراج المسارات من حمولة OpenAPI بصيغة JSON."""

    paths_node = payload.get("paths")
    if isinstance(paths_node, dict):
        return {str(path) for path in paths_node}
    return set()


def _extract_operations_from_json(payload: dict[str, object]) -> dict[str, set[str]]:
    """استخراج العمليات لكل مسار من حمولة OpenAPI بصيغة JSON."""

    paths_node = payload.get("paths")
    if not isinstance(paths_node, dict):
        return {}

    operations: dict[str, set[str]] = {}
    for path, details in paths_node.items():
        if not isinstance(path, str) or not isinstance(details, dict):
            continue
        operations[path] = {method.lower() for method in details if isinstance(method, str)}
    return operations


def _extract_paths_from_yaml(text: str) -> set[str]:
    """استخراج مسارات OpenAPI من YAML عبر مسح نصي يعتمد على التهيئة."""

    operations = _extract_operations_from_yaml(text)
    return set(operations.keys())


def _runtime_operations_from_openapi(schema: dict[str, object]) -> dict[str, set[str]]:
    """يبني خريطة العمليات من مخطط OpenAPI الناتج عن التطبيق."""

    paths_node = schema.get("paths")
    if not isinstance(paths_node, dict):
        return {}

    operations: dict[str, set[str]] = {}
    for path, details in paths_node.items():
        if not isinstance(path, str) or not isinstance(details, dict):
            continue
        methods = {
            method.lower()
            for method in details
            if isinstance(method, str)
        }
        operations[path] = methods

    return operations


def compare_contract_to_runtime(
    *,
    contract_operations: dict[str, set[str]],
    runtime_schema: dict[str, object],
) -> ContractComparisonReport:
    """يقارن العقد بمخطط التشغيل ويعيد الفجوات المكتشفة."""

    runtime_operations = _runtime_operations_from_openapi(runtime_schema)
    contract_paths = set(contract_operations.keys())
    runtime_paths = set(runtime_operations.keys())

    missing_paths = contract_paths - runtime_paths
    missing_operations: dict[str, set[str]] = {}

    for path, methods in contract_operations.items():
        runtime_methods = runtime_operations.get(path, set())
        missing = {method for method in methods if method not in runtime_methods}
        if missing:
            missing_operations[path] = missing

    return ContractComparisonReport(
        missing_paths=missing_paths,
        missing_operations=missing_operations,
    )


def default_contract_path() -> Path:
    """يبني المسار الافتراضي لعقد OpenAPI الأساسي."""

    return (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "contracts"
        / "openapi"
        / "core-api-v1.yaml"
    )


def _extract_operations_from_yaml(text: str) -> dict[str, set[str]]:
    """استخراج العمليات لكل مسار من YAML عبر مسح نصي مبسط."""

    lines = text.splitlines()
    operations: dict[str, set[str]] = {}
    in_paths = False
    base_indent: int | None = None
    current_path: str | None = None
    method_indent: int | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if not in_paths:
            if stripped == "paths:":
                in_paths = True
                base_indent = len(line) - len(line.lstrip(" "))
            continue

        if base_indent is None:
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent <= base_indent:
            break

        if stripped.startswith("/") and stripped.endswith(":"):
            current_path = stripped[:-1]
            operations.setdefault(current_path, set())
            method_indent = indent + 2
            continue

        if current_path is None or method_indent is None:
            continue

        if indent == method_indent and stripped.endswith(":"):
            method = stripped[:-1].lower()
            if method in {"get", "post", "put", "patch", "delete", "options", "head"}:
                operations[current_path].add(method)

    return operations
