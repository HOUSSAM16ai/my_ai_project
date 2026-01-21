"""اختبارات عقد OpenAPI لضمان الالتزام بمنهجية API-First."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.openapi_contracts import (
    detect_runtime_drift,
    load_contract_operations,
    load_contract_paths,
)
from app.main import create_app
from app.services.chat.agents.api_contract import APIContractAgent

CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "contracts" / "openapi" / "core-api-v1.yaml"
)


class TestAPIContracts:
    """اختبارات عملية لعقود OpenAPI الأساسية."""

    def test_contract_paths_are_available(self) -> None:
        """يتحقق من أن عقد OpenAPI يعرّف مسارات أساسية."""

        paths = load_contract_paths(CONTRACT_PATH)
        assert paths, "يجب أن يحتوي العقد على مسارات معرفة"
        assert "/api/security/health" in paths

    def test_contract_paths_exist_in_runtime_openapi(self) -> None:
        """يتحقق من توفر مسارات العقد ضمن مخطط التشغيل الفعلي."""

        contract_paths = load_contract_paths(CONTRACT_PATH)
        app = create_app(enable_static_files=False)
        runtime_paths = set(app.openapi().get("paths", {}).keys())

        missing = contract_paths - runtime_paths
        assert not missing, f"مسارات العقد غير موجودة في التطبيق: {sorted(missing)}"

    def test_contract_operations_exist_in_runtime_openapi(self) -> None:
        """يتحقق من توفر عمليات العقد ضمن مخطط التشغيل الفعلي."""

        contract_operations = load_contract_operations(CONTRACT_PATH)
        app = create_app(enable_static_files=False)
        runtime_paths = app.openapi().get("paths", {})

        missing_operations: dict[str, list[str]] = {}
        for path, methods in contract_operations.items():
            runtime_methods = runtime_paths.get(path, {})
            if not isinstance(runtime_methods, dict):
                missing_operations[path] = sorted(methods)
                continue
            missing = {method for method in methods if method not in runtime_methods}
            if missing:
                missing_operations[path] = sorted(missing)

        assert not missing_operations, f"عمليات العقد غير موجودة: {missing_operations}"

    def test_runtime_does_not_expose_undocumented_contracts(self) -> None:
        """يتحقق من عدم وجود مسارات أو عمليات غير موثقة ضمن العقد."""

        contract_operations = load_contract_operations(CONTRACT_PATH)
        app = create_app(enable_static_files=False)
        report = detect_runtime_drift(
            contract_operations=contract_operations,
            runtime_schema=app.openapi(),
        )

        assert report.is_clean(), (
            "تم العثور على انحرافات بين التشغيل والعقد: "
            f"paths={sorted(report.unexpected_paths)}, "
            f"operations={ {path: sorted(methods) for path, methods in report.unexpected_operations.items()} }"
        )

    @pytest.mark.asyncio
    async def test_contract_agent_validation(self) -> None:
        """يتحقق من أن وكيل العقد يرفض المسارات غير المعرفة."""

        agent = APIContractAgent(spec_path=CONTRACT_PATH)
        success = await agent.process(
            {"action": "validate_route_existence", "path": "/api/security/health"}
        )
        failure = await agent.process(
            {"action": "validate_route_existence", "path": "/api/unknown/path"}
        )

        assert success.success is True
        assert failure.success is False
