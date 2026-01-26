"""أدوات مساندة لتحميل وفحص عقود OpenAPI بشكل خفيف."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml


def _load_spec_text(spec_path: Path) -> tuple[str, str] | None:
    """يحمل نص عقد OpenAPI ويعيد الامتداد والنص إن كان الملف موجوداً."""

    if not spec_path.exists():
        return None
    return spec_path.suffix.lower(), spec_path.read_text(encoding="utf-8")


def _parse_json_payload(text: str) -> dict[str, object] | None:
    """يفكك نص JSON ويعيد القاموس أو None عند عدم توافق الصيغة."""

    payload = json.loads(text)
    if isinstance(payload, dict):
        return payload
    return None


def load_contract_paths(spec_path: Path) -> set[str]:
    """تحميل مسارات عقد OpenAPI من ملف JSON أو YAML بأسلوب خفيف وآمن."""

    payload = load_contract_schema(spec_path)
    if payload is None:
        return set()

    return _extract_paths_from_schema(payload)


def load_contract_operations(spec_path: Path) -> dict[str, set[str]]:
    """تحميل العمليات لكل مسار ضمن عقد OpenAPI بصيغة خفيفة."""

    payload = load_contract_schema(spec_path)
    if payload is None:
        return {}

    return _extract_operations_from_schema(payload)


def load_contract_schema(spec_path: Path) -> dict[str, object] | None:
    """يحمل عقد OpenAPI كقاموس موحد بغض النظر عن صيغة الملف."""

    loaded = _load_spec_text(spec_path)
    if loaded is None:
        return None

    suffix, text = loaded
    if suffix == ".json":
        return _parse_json_payload(text)

    payload = yaml.safe_load(text)
    if isinstance(payload, dict):
        return payload
    return None


@dataclass(frozen=True)
class ContractComparisonReport:
    """تقرير يوضح الفجوات بين العقد ومخطط التشغيل الفعلي."""

    missing_paths: set[str]
    missing_operations: dict[str, set[str]]

    def is_clean(self) -> bool:
        """يتحقق مما إذا كان التقرير خالياً من الفجوات."""

        return not self.missing_paths and not self.missing_operations


@dataclass(frozen=True)
class RuntimeContractDriftReport:
    """تقرير يكشف المسارات والعمليات غير الموثقة ضمن عقد OpenAPI."""

    unexpected_paths: set[str]
    unexpected_operations: dict[str, set[str]]

    def is_clean(self) -> bool:
        """يتحقق مما إذا كان التقرير خالياً من الانحرافات."""

        return not self.unexpected_paths and not self.unexpected_operations


def _extract_paths_from_schema(payload: dict[str, object]) -> set[str]:
    """استخراج المسارات من حمولة OpenAPI بصيغة موحدة."""

    paths_node = payload.get("paths")
    if isinstance(paths_node, dict):
        return {str(path) for path in paths_node}
    return set()


def _extract_operations_from_schema(payload: dict[str, object]) -> dict[str, set[str]]:
    """استخراج العمليات لكل مسار من حمولة OpenAPI بصيغة موحدة."""

    paths_node = payload.get("paths")
    if not isinstance(paths_node, dict):
        return {}

    operations: dict[str, set[str]] = {}
    for path, details in paths_node.items():
        if not isinstance(path, str) or not isinstance(details, dict):
            continue
        operations[path] = {method.lower() for method in details if isinstance(method, str)}
    return operations


def _runtime_operations_from_openapi(schema: dict[str, object]) -> dict[str, set[str]]:
    """يبني خريطة العمليات من مخطط OpenAPI الناتج عن التطبيق."""

    paths_node = schema.get("paths")
    if not isinstance(paths_node, dict):
        return {}

    operations: dict[str, set[str]] = {}
    for path, details in paths_node.items():
        if not isinstance(path, str) or not isinstance(details, dict):
            continue
        methods = {method.lower() for method in details if isinstance(method, str)}
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
        Path(__file__).resolve().parents[2] / "docs" / "contracts" / "openapi" / "core-api-v1.yaml"
    )


def detect_runtime_drift(
    *,
    contract_operations: dict[str, set[str]],
    runtime_schema: dict[str, object],
) -> RuntimeContractDriftReport:
    """يكشف المسارات أو العمليات غير الموثقة التي ظهرت في التشغيل."""

    runtime_operations = _runtime_operations_from_openapi(runtime_schema)
    contract_paths = set(contract_operations.keys())
    runtime_paths = set(runtime_operations.keys())

    unexpected_paths = runtime_paths - contract_paths
    unexpected_operations: dict[str, set[str]] = {}

    for path, runtime_methods in runtime_operations.items():
        if path not in contract_operations:
            continue
        contract_methods = contract_operations[path]
        extra = runtime_methods - contract_methods
        if extra:
            unexpected_operations[path] = extra

    return RuntimeContractDriftReport(
        unexpected_paths=unexpected_paths,
        unexpected_operations=unexpected_operations,
    )
