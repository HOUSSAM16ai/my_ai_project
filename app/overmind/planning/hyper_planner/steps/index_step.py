from __future__ import annotations

from typing import Any

from ...schemas import PlannedTask
from .. import deep_index_logic
from .base import PlanningStep


class DeepIndexStep(PlanningStep):
    """Step 2: Deep Index (Inline wrapper around deep_index_logic)."""

    def execute(self, tasks: list[PlannedTask], idx: int, context: dict[str, Any]) -> int:
        analysis_dependency_ids = context.get("analysis_dependency_ids", [])
        lang = context.get("lang", "en")

        struct_meta, idx_meta = deep_index_logic.attempt_deep_index(
            tasks, idx, analysis_dependency_ids, lang
        )
        context["struct_meta"] = struct_meta
        context["index_deps"] = idx_meta["deps"]
        return idx_meta["next_idx"]
