from __future__ import annotations

from typing import Any

from ...schemas import PlannedTask
from .. import config, prompts, utils
from .base import PlanningStep


class ReportingStep(PlanningStep):
    """Step 6: Comprehensive Analysis & Reporting."""

    def execute(self, tasks: list[PlannedTask], idx: int, context: dict[str, Any]) -> int:
        lang = context.get("lang", "en")
        final_writes = context.setdefault("final_writes", [])
        files = context.get("files", [])
        struct_meta = context.get("struct_meta", {})
        index_deps = context.get("index_deps", [])
        analysis_dependency_ids = context.get("analysis_dependency_ids", [])
        deps = index_deps or analysis_dependency_ids

        if config.COMPREHENSIVE_MODE:
            idx = self._add_comprehensive_analysis(
                tasks, idx, lang, final_writes, files, struct_meta, deps
            )
        else:
            # Artifact index
            idx = self._maybe_add_artifact_index(tasks, idx, lang, final_writes, files, deps)

            # Architecture deep report
            deep_report_task = None
            if struct_meta.get("attached"):
                deep_report_task = self._maybe_add_deep_arch_report(
                    tasks, idx, lang, deps, struct_meta
                )
                if deep_report_task:
                    idx = deep_report_task["next_idx"]
                    final_writes.append(deep_report_task["write_id"])
        return idx

    def _add_comprehensive_analysis(
        self,
        tasks: list[PlannedTask],
        idx: int,
        lang: str,
        final_writes: list[str],
        files: list[str],
        struct_meta: dict[str, Any],
        deps: list[str],
    ) -> int:
        prompt = prompts.comprehensive_analysis_prompt(lang)
        think_id = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=think_id,
                description="Generate comprehensive project analysis.",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": prompt},
                dependencies=deps,
            )
        )

        write_id = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=write_id,
                description=f"Write comprehensive analysis {config.COMPREHENSIVE_FILE_NAME}.",
                tool_name=config.TOOL_WRITE,
                tool_args={
                    "path": config.COMPREHENSIVE_FILE_NAME,
                    "content": f"{{{{{think_id}.answer}}}}",
                },
                dependencies=[think_id],
            )
        )

        return idx

    def _maybe_add_artifact_index(
        self,
        tasks: list[PlannedTask],
        idx: int,
        lang: str,
        final_writes: list[str],
        files: list[str],
        deps: list[str],
    ) -> int:
        if not (config.INDEX_FILE_EN and len(files) > 1):
            return idx
        idx_think = utils._tid(idx)
        idx += 1
        prompt = prompts.artifact_index_prompt(lang)
        tasks.append(
            PlannedTask(
                task_id=idx_think,
                description="Generate artifact index.",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": prompt},
                dependencies=deps,
            )
        )
        idx_write = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=idx_write,
                description=f"Write artifact index {config.INDEX_FILE_NAME}.",
                tool_name=config.TOOL_WRITE,
                tool_args={
                    "path": config.INDEX_FILE_NAME,
                    "content": f"{{{{{idx_think}.answer}}}}",
                },
                dependencies=[idx_think],
            )
        )
        return idx

    def _maybe_add_deep_arch_report(
        self,
        tasks: list[PlannedTask],
        idx: int,
        lang: str,
        deps: list[str],
        struct_meta: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not struct_meta.get("attached"):
            return None
        prompt = prompts.deep_arch_report_prompt(lang)
        think_id = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=think_id,
                description="Synthesize deep architecture report.",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": prompt},
                dependencies=deps,
            )
        )
        write_id = utils._tid(idx)
        idx += 1
        out_name = "DEEP_ARCHITECTURE_REPORT.md"
        tasks.append(
            PlannedTask(
                task_id=write_id,
                description=f"Write deep architecture report {out_name}.",
                tool_name=config.TOOL_WRITE,
                tool_args={"path": out_name, "content": f"{{{{{think_id}.answer}}}}"},
                dependencies=[think_id],
            )
        )
        return {"next_idx": idx, "write_id": write_id, "think_id": think_id}
