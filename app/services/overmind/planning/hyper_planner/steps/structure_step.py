from __future__ import annotations

from typing import Any

from ...schemas import PlannedTask
from .. import config, prompts, utils
from .base import PlanningStep


class StructureStep(PlanningStep):
    """Step 4: Roles & Sections definition."""

    def execute(self, tasks: list[PlannedTask], idx: int, context: dict[str, Any]) -> int:
        files = context.get("files", [])
        objective = context.get("objective", "")
        lang = context.get("lang", "en")
        struct_placeholder_ref = context.get("struct_placeholder_ref")
        index_deps = context.get("index_deps", [])
        analysis_dependency_ids = context.get("analysis_dependency_ids", [])

        deps = index_deps or analysis_dependency_ids

        # Roles
        role_task_id, idx = self._step_roles(
            tasks, idx, files, objective, lang, struct_placeholder_ref, deps
        )
        context["role_task_id"] = role_task_id

        # Sections
        section_task_id, idx = self._step_sections(
            tasks, idx, objective, lang, struct_placeholder_ref, role_task_id, deps
        )
        context["section_task_id"] = section_task_id

        return idx

    def _step_roles(
        self,
        tasks: list[PlannedTask],
        idx: int,
        files: list[str],
        objective: str,
        lang: str,
        struct_placeholder_ref: str | None,
        deps: list[str],
    ) -> tuple[str | None, int]:
        role_task_id = None
        if config.ROLE_DERIVATION and len(files) > 1:
            role_task_id = utils._tid(idx)
            idx += 1
            ref = f"{{{{{struct_placeholder_ref}.answer}}}}" if struct_placeholder_ref else ""
            tasks.append(
                PlannedTask(
                    task_id=role_task_id,
                    description="Derive unique roles JSON (no overlap).",
                    tool_name=config.TOOL_THINK,
                    tool_args={
                        "prompt": prompts.build_role_prompt(
                            files, objective, lang, struct_ref=utils._truncate(ref or "", 1100)
                        )
                    },
                    dependencies=deps,
                )
            )
        return role_task_id, idx

    def _step_sections(
        self,
        tasks: list[PlannedTask],
        idx: int,
        objective: str,
        lang: str,
        struct_placeholder_ref: str | None,
        role_task_id: str | None,
        deps: list[str],
    ) -> tuple[str | None, int]:
        section_task_id = None
        inferred_sections = utils.infer_sections(objective, lang)
        if inferred_sections:
            section_task_id = utils._tid(idx)
            idx += 1
            ref = f"{{{{{struct_placeholder_ref}.answer}}}}" if struct_placeholder_ref else ""
            tasks.append(
                PlannedTask(
                    task_id=section_task_id,
                    description="Refine sections JSON.",
                    tool_name=config.TOOL_THINK,
                    tool_args={
                        "prompt": prompts.build_section_prompt(
                            objective,
                            inferred_sections,
                            lang,
                            struct_ref=utils._truncate(ref or "", 900),
                        )
                    },
                    dependencies=([role_task_id] if role_task_id else deps),
                )
            )
        return section_task_id, idx
