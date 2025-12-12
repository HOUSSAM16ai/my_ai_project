"""Breaking change detection implementation."""

import logging
from typing import Any

from ..domain.models import BreakingChange
from ..domain.ports import BreakingChangeDetector

logger = logging.getLogger(__name__)


class SimpleBreakingChangeDetector(BreakingChangeDetector):
    """Detects breaking changes between schema versions."""

    def detect_changes(
        self, old_schema: dict[str, Any], new_schema: dict[str, Any]
    ) -> list[BreakingChange]:
        """Detect breaking changes between schemas."""
        changes = []

        # Check for removed required fields
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))
        removed_required = old_required - new_required

        for field in removed_required:
            changes.append(
                BreakingChange(
                    field_path=field,
                    change_type="required_removed",
                    old_value=True,
                    new_value=False,
                    severity="major",
                )
            )

        # Check for added required fields
        added_required = new_required - old_required
        for field in added_required:
            changes.append(
                BreakingChange(
                    field_path=field,
                    change_type="required_added",
                    old_value=False,
                    new_value=True,
                    severity="critical",
                )
            )

        # Check for removed properties
        old_props = set(old_schema.get("properties", {}).keys())
        new_props = set(new_schema.get("properties", {}).keys())
        removed_props = old_props - new_props

        for prop in removed_props:
            changes.append(
                BreakingChange(
                    field_path=prop,
                    change_type="removed",
                    old_value=old_schema["properties"][prop],
                    new_value=None,
                    severity="critical",
                )
            )

        # Check for type changes
        common_props = old_props & new_props
        for prop in common_props:
            old_type = old_schema["properties"][prop].get("type")
            new_type = new_schema["properties"][prop].get("type")
            if old_type != new_type:
                changes.append(
                    BreakingChange(
                        field_path=prop,
                        change_type="type_changed",
                        old_value=old_type,
                        new_value=new_type,
                        severity="critical",
                    )
                )

        if changes:
            logger.warning(f"Detected {len(changes)} breaking changes")

        return changes
