"""In-memory implementation of contract repository."""


from ..domain.models import ContractSchema
from ..domain.ports import ContractRepository


class InMemoryContractRepository(ContractRepository):
    """In-memory storage for contracts."""

    def __init__(self):
        self._contracts: dict[str, ContractSchema] = {}

    def save_contract(self, contract: ContractSchema) -> None:
        """Save a contract schema."""
        key = f"{contract.name}:{contract.version}"
        self._contracts[key] = contract

    def get_contract(self, name: str, version: str) -> ContractSchema | None:
        """Retrieve a contract schema."""
        key = f"{name}:{version}"
        return self._contracts.get(key)

    def list_contracts(self) -> list[ContractSchema]:
        """List all contracts."""
        return list(self._contracts.values())
