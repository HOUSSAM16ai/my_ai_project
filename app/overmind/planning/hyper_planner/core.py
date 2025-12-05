from __future__ import annotations

import json
import logging
import math
import os
import time
from typing import Any, ClassVar

from ..base_planner import BasePlanner, PlannerError, PlanValidationError
from ..deep_indexer import build_index, summarize_for_prompt
from ..schemas import MissionPlanSchema, PlannedTask, PlanningContext
from . import config, deep_index_logic, prompts, scan_logic, utils

# --------------------------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------------------------
_LOG = logging.getLogger("ultra_hyper_planner")
_lvl = os.getenv("LLM_PLANNER_LOG_LEVEL", "").upper()
_LOG.setLevel(getattr(logging, _lvl, logging.INFO) if _lvl else logging.INFO)
if not _LOG.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s"))
    _LOG.addHandler(_h)


# --------------------------------------------------------------------------------------
# Planner
# --------------------------------------------------------------------------------------
class PeerNode:
    """Represents a peer planner in the cluster."""

    def __init__(self, name: str, weight: float):
        self.name = name
        self.weight = weight


class UltraHyperPlanner(BasePlanner):
    name = "ultra_hyper_semantic_planner"
    version = "8.0.0-atomic-modular"
    production_ready = True
    capabilities: ClassVar[set[str]] = {
        "semantic",
        "chunked",
        "multi-file",
        "arabic",
        "adaptive",
        "struct_index",
        "architecture",
        "telemetry",
        "global_scan",
        "clustering",
        "failover",
    }
    tags: ClassVar[set[str]] = {"ultra", "hyper", "planner", "index", "semantic", "cluster"}

    def __init__(self):
        super().__init__()
        self.peers = [PeerNode("backup_planner_alpha", 0.8), PeerNode("backup_planner_beta", 0.7)]

    # ------------------------------------------------------------------
    def generate_plan(
        self,
        objective: str,
        context: PlanningContext | None = None,
        max_tasks: int | None = None,
    ) -> MissionPlanSchema:
        try:
            return self._core_planning_logic(objective, context, max_tasks)
        except Exception as e:
            _LOG.error(f"Primary planner failed: {e}. Attempting fallback...")
            return self._fallback_logic(objective)

    def _fallback_logic(self, objective: str) -> MissionPlanSchema:
        """Failover to a peer node logic simulation."""
        best_peer = max(self.peers, key=lambda p: p.weight)
        _LOG.info(f"Failing over to {best_peer.name}")

        tasks = [
            PlannedTask(
                task_id="f01",
                description=f"Fallback execution by {best_peer.name}: Understand Objective",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": f"Emergency Mode: {objective}"},
                dependencies=[],
            )
        ]

        return MissionPlanSchema(
            objective=objective,
            tasks=tasks,
            meta={"cluster_mode": True, "active_node": best_peer.name, "failover": True},
        )

    def _core_planning_logic(
        self,
        objective: str,
        context: PlanningContext | None = None,
        max_tasks: int | None = None,
    ) -> MissionPlanSchema:
        start = time.perf_counter()
        if not self._valid_objective(objective):
            raise PlannerError("objective_invalid_or_short", self.name, objective)

        lang = utils._detect_lang(objective)
        files = self._resolve_target_files(objective)
        req_lines = utils.extract_requested_lines(objective)
        total_chunks, per_chunk = utils.compute_chunk_plan(req_lines)

        # Adaptive chunk reduction
        adaptive_chunking = False
        est_per_file_stream = total_chunks * 2 + (2 if total_chunks > 1 else 1)
        est_tasks_core = 25
        projected = est_tasks_core + len(files) * est_per_file_stream
        if projected > config.GLOBAL_TASK_CAP and total_chunks > 1:
            reduction_factor = projected / float(config.GLOBAL_TASK_CAP)
            new_total = max(1, int(total_chunks / math.ceil(reduction_factor)))
            if new_total < total_chunks:
                total_chunks = new_total
                per_chunk = max(
                    80, math.ceil((req_lines or config.CHUNK_SIZE_HINT * 2) / max(1, total_chunks))
                )
                adaptive_chunking = True

        streaming_possible = self._can_stream()
        use_stream = (
            streaming_possible and config.STREAM_ENABLE and total_chunks >= config.STREAM_MIN_CHUNKS
        )

        tasks: list[PlannedTask] = []
        idx = 1
        analysis_dependency_ids = []

        # ---------- Repo scan ----------
        if config.ALLOW_LIST_READ_ANALYSIS and self._wants_repo_scan(objective):
            idx = self._add_repo_scan_tasks(tasks, idx, analysis_dependency_ids)

        # ---------- Extra sources ----------
        extra_files = scan_logic._collect_extra_files()
        extra_read_ids = []
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
                extra_read_ids.append(tid)
            analysis_dependency_ids.extend(extra_read_ids)

        # ---------- Deep index ----------
        struct_meta, idx_meta = deep_index_logic.attempt_deep_index(
            tasks, idx, analysis_dependency_ids, lang
        )
        idx = idx_meta["next_idx"]
        index_deps = idx_meta["deps"]
        deep_summary_text = struct_meta.get("summary_inline")

        # ---------- Semantic structural THINK ----------
        struct_semantic_task = None
        if struct_meta["attached"] and config.STRUCT_SEMANTIC_THINK:
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
                sem_prompt_ar = (
                    "حلل الملخص البنيوي وأعد JSON:\n"
                    "{layers:[...],services:[...],infra:[...],utilities:[...],hotspots:[...],duplicates:[...],"
                    "refactor_opportunities:[{item,impact,effort}],risks:[{issue,likelihood,impact}],patterns:[...]}\n\n"
                    f"{utils._truncate(sem_source, config.STRUCT_SEMANTIC_MAX_BYTES)}"
                )
                sem_prompt_en = (
                    "Analyze structural summary -> JSON schema:\n"
                    "{layers:[...],services:[...],infra:[...],utilities:[...],hotspots:[...],duplicates:[...],"
                    "refactor_opportunities:[{item,impact,effort}],risks:[{issue,likelihood,impact}],patterns:[...]}\n\n"
                    f"{utils._truncate(sem_source, config.STRUCT_SEMANTIC_MAX_BYTES)}"
                )
                struct_semantic_task = utils._tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=struct_semantic_task,
                        description="Semantic structural JSON (enriched).",
                        tool_name=config.TOOL_THINK,
                        tool_args={"prompt": sem_prompt_ar if lang == "ar" else sem_prompt_en},
                        dependencies=index_deps,
                    )
                )
                index_deps.append(struct_semantic_task)
                struct_meta["struct_semantic_task"] = struct_semantic_task
            except Exception as e:
                _LOG.warning("Semantic structural step failed: %s", e)

        # ---------- Global code summary (optional) ----------
        global_code_summary_task = None
        if config.GLOBAL_CODE_SUMMARY_EN and extra_read_ids:
            try:
                if len(extra_read_ids) > config.GLOBAL_CODE_SUMMARY_MAX_FILES:
                    use_ids = extra_read_ids[: config.GLOBAL_CODE_SUMMARY_MAX_FILES]
                else:
                    use_ids = extra_read_ids
                refs = []
                for t in use_ids:
                    refs.append(f"[{t}] => {{{{{t}.answer.content}}}}")
                gc_prompt_ar = (
                    "لخص هذه الملفات إلى خريطة وحدات/خدمات/بنية/وظائف حرجة/تكرارات محتملة. "
                    "أعد JSON: {modules:[...],services:[...],infra:[...],utilities:[...],"
                    "notable_functions:[...],potential_containers:[...],global_risks:[...]}.\n"
                    + utils._truncate("\n".join(refs), config.GLOBAL_CODE_SUMMARY_MAX_BYTES)
                )
                gc_prompt_en = (
                    "Summarize files into repository map (modules/services/layers/critical funcs/duplicate hints). "
                    "Return JSON: {modules:[...],services:[...],infra:[...],utilities:[...],"
                    "notable_functions:[...],potential_containers:[...],global_risks:[...]}.\n"
                    + utils._truncate("\n".join(refs), config.GLOBAL_CODE_SUMMARY_MAX_BYTES)
                )
                global_code_summary_task = utils._tid(idx)
                idx += 1
                tasks.append(
                    PlannedTask(
                        task_id=global_code_summary_task,
                        description="Global code semantic summary JSON.",
                        tool_name=config.TOOL_THINK,
                        tool_args={"prompt": gc_prompt_ar if lang == "ar" else gc_prompt_en},
                        dependencies=extra_read_ids,
                    )
                )
            except Exception as e:
                _LOG.warning("Global code summary failed: %s", e)

        # Determine context
        struct_placeholder_ref = None
        context_source = "none"
        if struct_semantic_task:
            struct_placeholder_ref = struct_semantic_task
            context_source = "semantic"
        elif struct_meta.get("md_task"):
            struct_placeholder_ref = struct_meta["md_task"]
            context_source = "deep_index_summary"
        elif global_code_summary_task:
            struct_placeholder_ref = global_code_summary_task
            context_source = "global"
        inline_struct = ""
        struct_meta["struct_context_injected"] = context_source != "none"

        # ---------- Roles ----------
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
                    dependencies=index_deps or analysis_dependency_ids,
                )
            )

        # ---------- Sections ----------
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
                    dependencies=(
                        [role_task_id] if role_task_id else (index_deps or analysis_dependency_ids)
                    ),
                )
            )

        # ---------- File generation ----------
        final_writes = []
        idx = self._add_file_generation_blocks(
            tasks=tasks,
            idx=idx,
            files=files,
            objective=objective,
            lang=lang,
            role_task_id=role_task_id,
            section_task_id=section_task_id,
            analysis_deps=(index_deps or analysis_dependency_ids),
            total_chunks=total_chunks,
            per_chunk=per_chunk,
            use_stream=use_stream,
            final_writes=final_writes,
            struct_placeholder=struct_placeholder_ref,
            inline_struct=inline_struct,
        )

        # ---------- Comprehensive Analysis ----------
        if config.COMPREHENSIVE_MODE:
            idx = self._add_comprehensive_analysis(
                tasks, idx, lang, final_writes, files, struct_meta
            )
        else:
            # Artifact index
            idx = self._maybe_add_artifact_index(tasks, idx, lang, final_writes, files)

            # Architecture deep report
            deep_report_task = None
            if struct_meta["attached"]:
                deep_report_task = self._maybe_add_deep_arch_report(
                    tasks, idx, lang, (index_deps or analysis_dependency_ids), struct_meta
                )
                if deep_report_task:
                    idx = deep_report_task["next_idx"]
                    final_writes.append(deep_report_task["write_id"])

        # ---------- Pruning ----------
        tasks_pruned = []
        idx, tasks_pruned = self._prune_if_needed(tasks, idx, final_writes)

        container_files = scan_logic._container_files_present()
        meta = {
            "language": lang,
            "files": files,
            "requested_lines": req_lines,
            "total_chunks": total_chunks,
            "per_chunk": per_chunk,
            "streaming": use_stream,
            "append_mode": self._append_allowed(),
            "role_task": role_task_id,
            "section_task": section_task_id,
            # index telemetry
            "files_scanned": struct_meta.get("files_scanned"),
            "hotspot_count": struct_meta.get("hotspot_count"),
            "duplicate_groups": struct_meta.get("duplicate_groups"),
            "index_version": struct_meta.get("index_version"),
            "struct_index_attached": struct_meta["attached"],
            "struct_index_json_task": struct_meta.get("json_task"),
            "struct_index_md_task": struct_meta.get("md_task"),
            "struct_semantic_task": struct_meta.get("struct_semantic_task"),
            "global_code_summary_task": global_code_summary_task,
            "struct_context_injected": struct_meta.get("struct_context_injected"),
            "struct_context_source": context_source,
            # extras
            "extra_source_files_count": len(extra_files),
            "container_files_detected": container_files,
            "scan_features_enabled": bool(extra_files),
            # new telemetry
            "tasks_pruned": tasks_pruned,
            "adaptive_chunking": adaptive_chunking,
            "task_budget": {"cap": config.GLOBAL_TASK_CAP, "planned": len(tasks)},
        }

        plan = MissionPlanSchema(objective=objective, tasks=tasks, meta=meta)
        self._validate(plan, files)
        elapsed = (time.perf_counter() - start) * 1000
        _LOG.info(
            "[HyperPlanner v8] tasks=%d pruned=%d streaming=%s ctx=%s ms=%.1f",
            len(tasks),
            len(tasks_pruned),
            use_stream,
            context_source,
            elapsed,
        )
        return plan

    # ----------------------------------------------------------------------------------
    # Internal Steps
    # ----------------------------------------------------------------------------------
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
            else:
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

    def _maybe_add_artifact_index(
        self, tasks: list[PlannedTask], idx: int, lang: str, deps: list[str], files: list[str]
    ) -> int:
        if not (config.INDEX_FILE_EN and len(files) > 1):
            return idx
        idx_think = utils._tid(idx)
        idx += 1
        p_ar = "أنشئ فهرساً موجزاً لكل ملف (سطران: التركيز والاستخدام)."
        p_en = "Create concise artifact index (2 lines per file: focus & usage)."
        tasks.append(
            PlannedTask(
                task_id=idx_think,
                description="Generate artifact index.",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": p_ar if lang == "ar" else p_en},
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
        prompt_ar = (
            "حلل بيانات الفهرس (JSON + ملخص) وقدم تقرير معمارية متقدم "
            "(طبقات، خدمات، تبعيات، نقاط ساخنة، تكرار، أولويات refactor، مخاطر، فرص تحسين). "
            "Markdown منظم مختصر."
        )
        prompt_en = (
            "Analyze structural index (JSON + summary) → advanced architecture report "
            "(layers, services, dependencies, hotspots, duplicates, refactor priorities, risks, improvements). "
            "Return concise structured Markdown."
        )
        think_id = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=think_id,
                description="Synthesize deep architecture report.",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": prompt_ar if lang == "ar" else prompt_en},
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

    def _add_comprehensive_analysis(
        self,
        tasks: list[PlannedTask],
        idx: int,
        lang: str,
        deps: list[str],
        files: list[str],
        struct_meta: dict[str, Any],
    ) -> int:
        prompt_ar = """حلل المشروع بشكل شامل وقدم تقرير واحد متكامل يتضمن:

- طبقات النظام والخدمات (الحاويات الثلاث: db, web, ai_service)
- التبعيات والعلاقات بين المكونات
- النقاط الساخنة والمناطق الحرجة في الكود

- ملخص الملفات الرئيسية ووظائفها
- الفئات والوظائف المهمة
- نقاط الدخول والواجهات البرمجية

- التكرار في الكود وفرص التحسين
- فرص إعادة الهيكلة والتنظيم
- المخاطر المحتملة ونقاط الضعف

- أولويات التحسين والتطوير
- الخطوات التالية المقترحة
- أفضل الممارسات للصيانة

قدم تحليل عميق ومنظم بذكاء خارق في ملف واحد شامل."""

        prompt_en = """Analyze the project comprehensively and provide one integrated report including:

- System layers and services (three containers: db, web, ai_service)
- Dependencies and relationships between components
- Hotspots and critical areas in the code

- Summary of key files and their functions
- Important classes and functions
- Entry points and APIs

- Code duplication and improvement opportunities
- Refactoring and reorganization opportunities
- Potential risks and weaknesses

- Improvement and development priorities
- Suggested next steps
- Best practices for maintenance

Provide deep, organized analysis with superhuman intelligence in one comprehensive file."""

        think_id = utils._tid(idx)
        idx += 1
        tasks.append(
            PlannedTask(
                task_id=think_id,
                description="Generate comprehensive project analysis.",
                tool_name=config.TOOL_THINK,
                tool_args={"prompt": prompt_ar if lang == "ar" else prompt_en},
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

    def _prune_if_needed(
        self, tasks: list[PlannedTask], idx: int, final_writes: list[str]
    ) -> tuple[int, list[str]]:
        if len(tasks) <= config.GLOBAL_TASK_CAP:
            return idx, []
        pruned = []
        group_map = {
            "semantic": lambda t: "Semantic structural JSON" in t.description,
            "global_summary": lambda t: "Global code semantic summary" in t.description,
            "deep_arch_report": lambda t: "deep architecture report" in t.description.lower(),
        }
        # Remove groups until under cap
        for group in config.OPTIONAL_GROUPS:
            if len(tasks) <= config.GLOBAL_TASK_CAP:
                break
            matcher = group_map.get(group)
            if not matcher:
                continue
            removable = [t for t in tasks if matcher(t)]
            if not removable:
                continue
            for rt in removable:
                if rt.task_id in final_writes:
                    continue
                tasks.remove(rt)
                pruned.append(rt.task_id)
                if len(tasks) <= config.GLOBAL_TASK_CAP:
                    break
        return idx, pruned

    # ----------------------------------------------------------------------------------
    # Utilities
    # ----------------------------------------------------------------------------------
    def _read_from_file(self, file_path: str) -> Any:
        if not os.path.exists(file_path):
            return None

        with open(file_path, encoding="utf-8") as f:
            if file_path.endswith((".yaml", ".yml")):
                from app.core.yaml_utils import load_yaml_safely

                try:
                    return load_yaml_safely(f.read())
                except Exception as e:
                    _LOG.warning(f"Failed to load YAML safely from {file_path}: {e}")
                    return None
            if file_path.endswith(".json"):
                try:
                    return json.load(f)
                except Exception:
                    return None
            return f.read()

    def _resolve_target_files(self, objective: str) -> list[str]:
        raw = utils.extract_filenames(objective)
        normalized = []
        for f in raw:
            nf = utils._normalize_filename(f)
            if "." not in nf:
                nf = utils._ensure_ext(nf)
            if nf.lower() not in [x.lower() for x in normalized]:
                normalized.append(nf)
        return normalized[: config.MAX_FILES]

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

    def _validate(self, plan: MissionPlanSchema, files: list[str]):
        if len(plan.tasks) > config.GLOBAL_TASK_CAP:
            raise PlanValidationError("excessive_tasks", self.name, plan.objective)
        ids = {t.task_id for t in plan.tasks}
        for t in plan.tasks:
            for d in t.dependencies:
                if d not in ids:
                    raise PlanValidationError(
                        f"dangling_dependency:{t.task_id}->{d}", self.name, plan.objective
                    )
        if config.STRICT_WRITE_ENF:
            for f in files:
                if not any(
                    (tt.tool_name in (config.TOOL_WRITE, config.TOOL_APPEND))
                    and (tt.tool_args or {}).get("path", "").lower() == f.lower()
                    for tt in plan.tasks
                ):
                    raise PlanValidationError(f"missing_file_write:{f}", self.name, plan.objective)

    def _valid_objective(self, objective: str) -> bool:
        if not objective or len(objective.strip()) < 5:
            return False
        return not objective.strip().isdigit()
