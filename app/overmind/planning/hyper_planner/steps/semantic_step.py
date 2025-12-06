from __future__ import annotations

from typing import Any

from ...deep_indexer import build_index, summarize_for_prompt
from ...schemas import PlannedTask
from .. import config, deep_index_logic, prompts, utils
from .base import PlanningStep


class SemanticAnalysisStep(PlanningStep):
    """Step 3: Semantic Analysis (Structure & Global Summary)."""

    def execute(self, tasks: list[PlannedTask], idx: int, context: dict[str, Any]) -> int:
        lang = context.get("lang", "en")
        index_deps = context.get("index_deps", [])
        struct_meta = context.get("struct_meta", {})
        analysis_dependency_ids = context.get("analysis_dependency_ids", [])

        # Structure Analysis
        struct_semantic_task = self._step_semantic_analysis(
            tasks, idx, lang, index_deps, struct_meta
        )
        if struct_semantic_task:
            idx += 1
            index_deps.append(struct_semantic_task.task_id)
            struct_meta["struct_semantic_task"] = struct_semantic_task.task_id
            context["struct_semantic_task_id"] = struct_semantic_task.task_id

        # Global Code Summary
        global_code_summary_task = self._step_global_code_summary(
            tasks, idx, lang, analysis_dependency_ids
        )
        if global_code_summary_task:
            idx += 1
            context["global_code_summary_task_id"] = global_code_summary_task.task_id

        # Update context source
        context_source, struct_placeholder_ref = self._determine_context_source(
            context.get("struct_semantic_task_id"),
            struct_meta.get("md_task"),
            context.get("global_code_summary_task_id"),
        )
        struct_meta["struct_context_injected"] = context_source != "none"
        context["context_source"] = context_source
        context["struct_placeholder_ref"] = struct_placeholder_ref

        return idx

    def _step_semantic_analysis(
        self,
        tasks: list[PlannedTask],
        idx: int,
        lang: str,
        index_deps: list[str],
        struct_meta: dict,
    ) -> PlannedTask | None:
        if not (struct_meta.get("attached") and config.STRUCT_SEMANTIC_THINK):
            return None

        deep_summary_text = struct_meta.get("summary_inline")
        try:
            if config.SEMANTIC_REUSE_INDEX and deep_summary_text:
                sem_source = deep_summary_text
            else:
                if deep_index_logic._DEEP_INDEX_ENABLED and deep_index_logic._HAS_INDEXER:
                    index_for_sem = build_index(".")
                    sem_source = summarize_for_prompt(
                        index_for_sem,
                        max_len=min(
                            config.STRUCT_SEMANTIC_MAX_BYTES, config.DEEP_INDEX_SUMMARY_MAX
                        ),
                    )
                else:
                    sem_source = deep_summary_text or ""

            prompt = prompts.semantic_analysis_prompt(
                lang, sem_source, config.STRUCT_SEMANTIC_MAX_BYTES
            )

            struct_semantic_task = utils._tid(idx)
            t = PlannedTask(
                task_id=struct_semantic_task,
                description="Semantic structural JSON (enriched).",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": prompt},
                dependencies=index_deps,
            )
            tasks.append(t)
            return t
        except Exception:
            return None

    def _step_global_code_summary(
        self, tasks: list[PlannedTask], idx: int, lang: str, extra_read_ids: list[str]
    ) -> PlannedTask | None:
        if not (config.GLOBAL_CODE_SUMMARY_EN and extra_read_ids):
            return None

        try:
            use_ids = (
                extra_read_ids[: config.GLOBAL_CODE_SUMMARY_MAX_FILES]
                if len(extra_read_ids) > config.GLOBAL_CODE_SUMMARY_MAX_FILES
                else extra_read_ids
            )
            refs = "\n".join([f"[{t}] => {{{{{t}.answer.content}}}}" for t in use_ids])

            prompt = prompts.global_code_summary_prompt(
                lang, refs, config.GLOBAL_CODE_SUMMARY_MAX_BYTES
            )

            global_code_summary_task = utils._tid(idx)
            t = PlannedTask(
                task_id=global_code_summary_task,
                description="Global code semantic summary JSON.",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": prompt},
                dependencies=extra_read_ids,
            )
            tasks.append(t)
            return t
        except Exception:
            return None

    def _determine_context_source(
        self,
        struct_semantic_task_id: str | None,
        md_task_id: str | None,
        global_summary_task_id: str | None,
    ) -> tuple[str, str | None]:
        if struct_semantic_task_id:
            return "semantic", struct_semantic_task_id
        elif md_task_id:
            return "deep_index_summary", md_task_id
        elif global_summary_task_id:
            return "global", global_summary_task_id
        return "none", None
