from pathlib import Path

from app.core.logging import get_logger
from app.core.openapi_contracts import default_contract_path, load_contract_paths
from app.services.chat.agents.base import AgentResponse

logger = get_logger("api-contract-agent")

class APIContractAgent:
    """
    وكيل يتحقق من صحة الالتزام بعقود OpenAPI وفق منهجية API-First.
    """

    def __init__(self, spec_path: Path | None = None) -> None:
        self.spec_path = spec_path or default_contract_path()
        self._cached_paths: set[str] | None = None

    async def process(self, input_data: dict[str, object]) -> AgentResponse:
        """
        يتحقق من التزام العملية بعقد الواجهات.

        المدخل:
        - {"action": "validate_route_existence", "path": "..."}
        """
        action = _read_action(input_data)

        if action == "validate_route_existence":
            route_path = _read_path(input_data)
            if route_path is None:
                return AgentResponse(success=False, message="مسار غير صالح للتحقق من العقد.")

            contract_paths = self._load_contract_paths()
            logger.info("Validating route existence against contract: %s", route_path)
            if route_path in contract_paths:
                return AgentResponse(
                    success=True,
                    message=f"تم التحقق من المسار ضمن العقد: {route_path}",
                )
            return AgentResponse(
                success=False,
                message=f"المسار غير معرّف في عقد OpenAPI: {route_path}",
            )

        return AgentResponse(success=False, message="عملية غير مدعومة في وكيل العقد.")

    def _load_contract_paths(self) -> set[str]:
        if self._cached_paths is None:
            self._cached_paths = load_contract_paths(self.spec_path)
        return self._cached_paths


def _read_action(input_data: dict[str, object]) -> str | None:
    action = input_data.get("action")
    if isinstance(action, str):
        return action
    return None


def _read_path(input_data: dict[str, object]) -> str | None:
    path_value = input_data.get("path")
    if isinstance(path_value, str) and path_value.strip():
        return path_value.strip()
    return None
