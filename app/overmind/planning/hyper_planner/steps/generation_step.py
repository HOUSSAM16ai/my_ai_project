from __future__ import annotations

import os
from typing import Any

from ...schemas import PlannedTask
from .. import config, prompts, utils
from .base import PlanningStep


class GenerationStep(PlanningStep):
    """Step 5: File Generation logic."""

    def execute(self, tasks: list[PlannedTask], idx: int, context: dict[str, Any]) -> int:
        files = context.get("files", [])
        objective = context.get("objective", "")
        lang = context.get("lang", "en")
        role_task_id = context.get("role_task_id")
        section_task_id = context.get("section_task_id")
        index_deps = context.get("index_deps", [])
        analysis_dependency_ids = context.get("analysis_dependency_ids", [])
        total_chunks = context.get("total_chunks", 1)
        per_chunk = context.get("per_chunk", 100)
        use_stream = context.get("use_stream", False)
        struct_placeholder = context.get("struct_placeholder_ref")

        analysis_deps = index_deps or analysis_dependency_ids
        final_writes = context.setdefault("final_writes", [])

        return self._add_file_generation_blocks(
            tasks=tasks,
            idx=idx,
            files=files,
            objective=objective,
            lang=lang,
            role_task_id=role_task_id,
            section_task_id=section_task_id,
            analysis_deps=analysis_deps,
            total_chunks=total_chunks,
            per_chunk=per_chunk,
            use_stream=use_stream,
            final_writes=final_writes,
            struct_placeholder=struct_placeholder,
            inline_struct="",
        )

    def _add_file_generation_blocks(
        self,
        tasks: list[PlannedTask],
        idx: int,
        files: list[str],
        objective: str,
        lang: str,
        role_task_id: str | None,
        section_task_id: str | None,
        analysis_deps: list[str],
        total_chunks: int,
        per_chunk: int,
        use_stream: bool,
        final_writes: list[str],
        struct_placeholder: str | None,
        inline_struct: str,
    ) -> int:
        for fname in files:
            base_deps = []
            if role_task_id:
                base_deps.append(role_task_id)
            if section_task_id:
                base_deps.append(section_task_id)
            if analysis_deps and not base_deps:
                base_deps = analysis_deps

            if config.ENSURE_FILE:
                ensure_id = utils._tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=ensure_id,
                        description=f"Ensure file {fname} exists.",
                        tool_name=config.TOOL_ENSURE,
                        tool_args={
                            "path": fname,
                            "initial_content": self._initial_banner(fname, objective, lang),
                        },
                        dependencies=[],
                    )
                )
                base_deps.append(ensure_id)

            ftype = utils.file_type(fname)

            if use_stream and self._append_allowed() and total_chunks > 1:
                idx = self._add_streaming_tasks(
                    tasks,
                    idx,
                    fname,
                    objective,
                    lang,
                    role_task_id,
                    section_task_id,
                    base_deps,
                    total_chunks,
                    per_chunk,
                    ftype,
                    struct_placeholder,
                    inline_struct,
                    final_writes,
                )
            else:
                idx = self._add_batch_tasks(
                    tasks,
                    idx,
                    fname,
                    objective,
                    lang,
                    role_task_id,
                    section_task_id,
                    base_deps,
                    total_chunks,
                    per_chunk,
                    ftype,
                    struct_placeholder,
                    inline_struct,
                    final_writes,
                )
        return idx

    def _add_streaming_tasks(
        self,
        tasks,
        idx,
        fname,
        objective,
        lang,
        role_task_id,
        section_task_id,
        base_deps,
        total_chunks,
        per_chunk,
        ftype,
        struct_placeholder,
        inline_struct,
        final_writes,
    ) -> int:
        prev = None
        for c in range(1, total_chunks + 1):
            think_id = utils._tid(idx)
            idx += 1
            prompt = prompts.build_chunk_prompt(
                objective,
                fname,
                role_task_id,
                section_task_id,
                c,
                total_chunks,
                per_chunk,
                lang,
                ftype,
                struct_placeholder=struct_placeholder,
                inline_struct=inline_struct,
            )
            deps = base_deps.copy()
            if prev:
                deps.append(prev)
            tasks.append(
                PlannedTask(
                    task_id=think_id,
                    description=f"Stream chunk {c}/{total_chunks} for {fname}.",
                    tool_name=config.TOOL_THINK,
                    tool_args={"prompt": prompt},
                    dependencies=deps,
                )
            )
            append_id = utils._tid(idx)
            idx += 1
            tasks.append(
                PlannedTask(
                    task_id=append_id,
                    description=f"Append chunk {c} to {fname}.",
                    tool_name=config.TOOL_APPEND,
                    tool_args={"path": fname, "content": f"{{{{{think_id}.answer}}}}"},
                    dependencies=[think_id],
                )
            )
            prev = append_id
        wrap_think = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=wrap_think,
                description=f"Generate final wrap (stream) for {fname}.",
                tool_name=config.TOOL_THINK,
                tool_args={
                    "prompt": prompts.build_final_wrap_prompt(
                        objective,
                        fname,
                        role_task_id,
                        lang,
                        struct_placeholder,
                        inline_struct,
                    )
                },
                dependencies=[prev] if prev else base_deps,
            )
        )
        wrap_append = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=wrap_append,
                description=f"Append final wrap to {fname}.",
                tool_name=config.TOOL_APPEND,
                tool_args={"path": fname, "content": f"\n\n{{{{{wrap_think}.answer}}}}"},
                dependencies=[wrap_think],
            )
        )
        final_writes.append(wrap_append)
        return idx

    def _add_batch_tasks(
        self,
        tasks,
        idx,
        fname,
        objective,
        lang,
        role_task_id,
        section_task_id,
        base_deps,
        total_chunks,
        per_chunk,
        ftype,
        struct_placeholder,
        inline_struct,
        final_writes,
    ) -> int:
        chunk_thinks = []
        for c in range(1, total_chunks + 1):
            think_id = utils._tid(idx)
            idx += 1
            prompt = prompts.build_chunk_prompt(
                objective,
                fname,
                role_task_id,
                section_task_id,
                c,
                total_chunks,
                per_chunk,
                lang,
                ftype,
                struct_placeholder,
                inline_struct,
            )
            deps = base_deps.copy()
            if chunk_thinks:
                deps.append(chunk_thinks[-1])
            tasks.append(
                PlannedTask(
                    task_id=think_id,
                    description=f"Batch chunk {c}/{total_chunks} for {fname}.",
                    tool_name=config.TOOL_THINK,
                    tool_args={"prompt": prompt},
                    dependencies=deps,
                )
            )
            chunk_thinks.append(think_id)
        wrap_think = None
        if total_chunks > 1:
            wrap_think = utils._tid(idx)
            idx += 1
            tasks.append(
                PlannedTask(
                    task_id=wrap_think,
                    description=f"Generate final wrap (batch) for {fname}.",
                    tool_name=config.TOOL_THINK,
                    tool_args={
                        "prompt": prompts.build_final_wrap_prompt(
                            objective,
                            fname,
                            role_task_id,
                            lang,
                            struct_placeholder,
                            inline_struct,
                        )
                    },
                    dependencies=[chunk_thinks[-1]],
                )
            )
        parts = [f"{{{{{cid}.answer}}}}" for cid in chunk_thinks]
        if wrap_think:
            parts.append(f"\n\n{{{{{wrap_think}.answer}}}}")
        combined = "\n\n".join(parts)
        write_id = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=write_id,
                description=f"Write composed file {fname} (batch).",
                tool_name=config.TOOL_WRITE,
                tool_args={"path": fname, "content": combined},
                dependencies=[chunk_thinks[-1]] if chunk_thinks else base_deps,
            )
        )
        final_writes.append(write_id)
        return idx

    def _can_stream(self) -> bool:
        mode = config.ALLOW_APPEND_MODE
        if mode == "0":
            return False
        if mode == "1":
            return True
        allowed_env = os.getenv("PLANNER_ALLOWED_TOOLS", "")
        if allowed_env:
            allowed = {t.strip() for t in allowed_env.split(",") if t.strip()}
            return "append_file" in allowed
        return True

    def _append_allowed(self) -> bool:
        return self._can_stream()

    def _initial_banner(self, fname: str, objective: str, lang: str) -> str:
        ext = fname.lower()
        trunc = objective[:220]
        if ext.endswith((".md", ".txt", ".log", ".rst", ".adoc", ".html")):
            return (
                (f"# تهيئة: {fname}\n\n> الهدف: {trunc}...\n\n")
                if lang == "ar"
                else (f"# Init: {fname}\n\n> Objective: {trunc}...\n\n")
            )
        if any(ext.endswith(e) for e in utils.CODE_EXTS):
            return f"# Scaffold for objective: {objective[:150]}\n\n"
        if any(ext.endswith(e) for e in utils.DATA_EXTS):
            return f"# Data artifact scaffold: {objective[:150]}\n"
        return ""
