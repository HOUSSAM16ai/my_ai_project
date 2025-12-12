"""Contract management application service."""

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

from ..domain.models import ContractSchema, ContractValidationResult
from ..domain.ports import (
    BreakingChangeDetector,
    ContractRepository,
    SchemaValidator,
)

logger = logging.getLogger(__name__)


class ContractManager:
    """Manages API contracts and validation."""

    def __init__(
        self,
        repository: ContractRepository,
        validator: SchemaValidator,
        change_detector: BreakingChangeDetector,
    ):
        self.repository = repository
        self.validator = validator
        self.change_detector = change_detector

    def register_contract(
        self, name: str, version: str, schema: dict[str, Any]
    ) -> ContractSchema:
        """Register a new API contract."""
        now = datetime.now(UTC)
        schema_hash = self._compute_hash(schema)

        contract = ContractSchema(
            name=name,
            version=version,
            schema=schema,
            created_at=now,
            updated_at=now,
            hash=schema_hash,
        )

        # Check for breaking changes if previous version exists
        existing = self.repository.get_contract(name, version)
        if existing:
            changes = self.change_detector.detect_changes(existing.schema, schema)
            if changes:
                logger.warning(
                    f"Breaking changes detected in {name} v{version}: {len(changes)} changes"
                )

        self.repository.save_contract(contract)
        logger.info(f"Registered contract: {name} v{version}")
        return contract

    def validate_against_contract(
        self, name: str, version: str, data: Any
    ) -> ContractValidationResult:
        """Validate data against a contract."""
        contract = self.repository.get_contract(name, version)
        if not contract:
            return ContractValidationResult(
                is_valid=False, errors=[f"Contract {name} v{version} not found"]
            )

        return self.validator.validate(data, contract.schema)

    def get_contract(self, name: str, version: str) -> ContractSchema | None:
        """Retrieve a contract."""
        return self.repository.get_contract(name, version)

    def list_all_contracts(self) -> list[ContractSchema]:
        """List all registered contracts."""
        return self.repository.list_contracts()

    def _compute_hash(self, schema: dict[str, Any]) -> str:
        """Compute hash of schema for change detection."""
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()
