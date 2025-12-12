"""JSON Schema validator implementation."""

import logging
from typing import Any

from jsonschema import Draft7Validator, ValidationError

from ..domain.models import ContractValidationResult
from ..domain.ports import SchemaValidator

logger = logging.getLogger(__name__)


class JSONSchemaValidator(SchemaValidator):
    """Validates data using JSON Schema Draft 7."""

    def validate(self, data: Any, schema: dict[str, Any]) -> ContractValidationResult:
        """Validate data against JSON schema."""
        validator = Draft7Validator(schema)
        errors = []
        warnings = []

        try:
            # Collect all validation errors
            for error in validator.iter_errors(data):
                error_msg = f"{'.'.join(str(p) for p in error.path)}: {error.message}"
                errors.append(error_msg)

            is_valid = len(errors) == 0

            if not is_valid:
                logger.debug(f"Validation failed with {len(errors)} errors")

            return ContractValidationResult(
                is_valid=is_valid, errors=errors, warnings=warnings
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ContractValidationResult(
                is_valid=False, errors=[f"Validation exception: {str(e)}"]
            )
