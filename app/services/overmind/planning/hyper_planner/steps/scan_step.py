from __future__ import annotations

from typing import Any

from ...schemas import PlannedTask
from .. import config, scan_logic, utils
from .base import PlanningStep


class ScanRepoStep(PlanningStep):
    """Step 1: Scans the repository and reads extra files.

    Refactored to be a pure controller delegating logic to 'scan_logic.py'.
    """

    def execute(self, tasks: list[PlannedTask], idx: int, context: dict[str, Any]) -> int:
        objective = context.get("objective", "")
        deps_accum = context.setdefault("analysis_dependency_ids", [])

        # 1. Repo Scan Logic (Delegated)
        if config.ALLOW_LIST_READ_ANALYSIS and scan_logic.wants_repo_scan(objective):
            idx, new_tasks = scan_logic.generate_repo_scan_tasks(idx, deps_accum)
            tasks.extend(new_tasks)

        # 2. Extra Files Logic (Delegated)
        extra_files = scan_logic._collect_extra_files()
        if extra_files:
            for ef in extra_files:
                tid = utils._tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=tid,
                        description=f"Read extra source {ef}.",
                        tool_name=config.TOOL_READ,
                        tool_args={"path": ef, "ignore_missing": True, "max_bytes": 50000},
                        dependencies=[],
                    )
                )
                deps_accum.append(tid)
        return idx
