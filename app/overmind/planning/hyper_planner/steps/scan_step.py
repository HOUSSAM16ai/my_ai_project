from __future__ import annotations

from typing import Any

from ...schemas import PlannedTask
from .. import config, scan_logic, utils
from .base import PlanningStep


class ScanRepoStep(PlanningStep):
    """Step 1: Scans the repository and reads extra files."""

    def execute(self, tasks: list[PlannedTask], idx: int, context: dict[str, Any]) -> int:
        objective = context.get("objective", "")
        deps_accum = context.setdefault("analysis_dependency_ids", [])

        if config.ALLOW_LIST_READ_ANALYSIS and self._wants_repo_scan(objective):
            idx = self._add_repo_scan_tasks(tasks, idx, deps_accum)

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

    def _wants_repo_scan(self, objective: str) -> bool:
        low = objective.lower()
        return any(
            k in low
            for k in (
                "repository",
                "repo",
                "structure",
                "architecture",
                "معمار",
                "هيكل",
                "بنية",
                "analyze project",
            )
        )

    def _add_repo_scan_tasks(
        self, tasks: list[PlannedTask], idx: int, deps_accum: list[str]
    ) -> int:
        for root in (".", "app"):
            tid = utils._tid(idx)
            idx += 1
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description=f"List directory '{root}' (struct awareness).",
                    tool_name=config.TOOL_LIST,
                    tool_args={"path": root, "max_entries": 600},
                    dependencies=[],
                )
            )
            deps_accum.append(tid)
        for cf in config.CORE_READ_FILES[:18]:
            tid = utils._tid(idx)
            idx += 1
            tasks.append(
                PlannedTask(
                    task_id=tid,
                    description=f"Read core file {cf} (ignore missing).",
                    tool_name=config.TOOL_READ,
                    tool_args={"path": cf, "ignore_missing": True, "max_bytes": 65000},
                    dependencies=[],
                )
            )
            deps_accum.append(tid)
        return idx
