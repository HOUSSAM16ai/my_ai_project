"""
Planning Logic Module (Controller-free)
========================================
Extracted from core.py to enforce Controller/Service separation.

This module contains pure planning logic functions that operate without
controller/orchestrator concerns, making them easier to test and reuse.
"""
from __future__ import annotations
import logging
import math
import os
from ..schemas import PlannedTask
from . import config, utils
_LOG = logging.getLogger('ultra_hyper_planner.planning_logic')


def calculate_chunking(files: list[str], req_lines: int) ->tuple[int, int, bool
    ]:
    """
    Calculate optimal chunking strategy for the given files and requested lines.

    Returns:
        tuple: (total_chunks, per_chunk, adaptive_chunking)
    """
    total_chunks, per_chunk = utils.compute_chunk_plan(req_lines)
    adaptive_chunking = False
    est_per_file_stream = total_chunks * 2 + (2 if total_chunks > 1 else 1)
    est_tasks_core = 25
    projected = est_tasks_core + len(files) * est_per_file_stream
    if projected > config.GLOBAL_TASK_CAP and total_chunks > 1:
        reduction_factor = projected / float(config.GLOBAL_TASK_CAP)
        new_total = max(1, int(total_chunks / math.ceil(reduction_factor)))
        if new_total < total_chunks:
            total_chunks = new_total
            per_chunk = max(80, math.ceil((req_lines or config.
                CHUNK_SIZE_HINT * 2) / max(1, total_chunks)))
            adaptive_chunking = True
    return total_chunks, per_chunk, adaptive_chunking


def determine_streaming_strategy(total_chunks: int, can_stream: bool) ->bool:
    """
    Determine if streaming should be used based on configuration and chunk count.

    Args:
        total_chunks: Number of chunks to process
        can_stream: Whether streaming is technically possible

    Returns:
        bool: True if streaming should be used
    """
    return (can_stream and config.STREAM_ENABLE and total_chunks >= config.
        STREAM_MIN_CHUNKS)


def can_stream() ->bool:
    """
    Check if streaming/append mode is allowed based on configuration.

    Returns:
        bool: True if streaming is allowed
    """
    mode = config.ALLOW_APPEND_MODE
    if mode == '0':
        return False
    if mode == '1':
        return True
    allowed_env = os.getenv('PLANNER_ALLOWED_TOOLS', '')
    if allowed_env:
        allowed = {t.strip() for t in allowed_env.split(',') if t.strip()}
        return 'append_file' in allowed
    return True


def prune_tasks_if_needed(tasks: list[PlannedTask], idx: int, final_writes:
    list[str]) ->tuple[int, list[str]]:
    """
    Prune optional tasks if the total exceeds the global task cap.

    Args:
        tasks: List of planned tasks (modified in place)
        idx: Current task index
        final_writes: List of final write task IDs that should not be pruned

    Returns:
        tuple: (next_idx, list of pruned task IDs)
    """
    if len(tasks) <= config.GLOBAL_TASK_CAP:
        return idx, []
    pruned = []
    group_map = {'semantic': lambda t: 'Semantic structural JSON' in t.
        description, 'global_summary': lambda t:
        'Global code semantic summary' in t.description, 'deep_arch_report':
        lambda t: 'deep architecture report' in t.description.lower()}
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


def build_plan_metadata(ctx: dict, tasks: list, tasks_pruned: list,
    planned_count: int, container_files: bool, append_allowed: bool) ->dict:
    """
    Build comprehensive metadata for the mission plan.

    Args:
        ctx: Planning context dictionary
        tasks: List of planned tasks
        tasks_pruned: List of pruned task IDs
        planned_count: Total number of tasks planned
        container_files: Whether container files were detected
        append_allowed: Whether append mode is allowed

    Returns:
        dict: Metadata dictionary
    """
    struct_meta = ctx.get('struct_meta', {})
    return {'language': ctx['lang'], 'files': ctx['files'],
        'requested_lines': ctx['req_lines'], 'total_chunks': ctx[
        'total_chunks'], 'per_chunk': ctx['per_chunk'], 'streaming': ctx[
        'use_stream'], 'append_mode': append_allowed, 'role_task': ctx[
        'role_task_id'], 'section_task': ctx['section_task_id'],
        'files_scanned': struct_meta.get('files_scanned'), 'hotspot_count':
        struct_meta.get('hotspot_count'), 'duplicate_groups': struct_meta.
        get('duplicate_groups'), 'index_version': struct_meta.get(
        'index_version'), 'struct_index_attached': struct_meta.get(
        'attached', False), 'struct_index_json_task': struct_meta.get(
        'json_task'), 'struct_index_md_task': struct_meta.get('md_task'),
        'struct_semantic_task': struct_meta.get('struct_semantic_task'),
        'global_code_summary_task': ctx['global_code_summary_task_id'],
        'struct_context_injected': struct_meta.get(
        'struct_context_injected'), 'struct_context_source': ctx[
        'context_source'], 'tasks_pruned': tasks_pruned,
        'adaptive_chunking': ctx['adaptive_chunking'], 'task_budget': {
        'cap': config.GLOBAL_TASK_CAP, 'planned': planned_count},
        'container_files_detected': container_files}


def resolve_target_files(objective: str) ->list[str]:
    """
    Extract and normalize file names from the objective.

    Args:
        objective: The mission objective string

    Returns:
        list: Normalized file names (up to MAX_FILES)
    """
    raw = utils.extract_filenames(objective)
    normalized = []
    for f in raw:
        nf = utils._normalize_filename(f)
        if '.' not in nf:
            nf = utils._ensure_ext(nf)
        if nf.lower() not in [x.lower() for x in normalized]:
            normalized.append(nf)
    return normalized[:config.MAX_FILES]


def validate_objective(objective: str) ->bool:
    """
    Validate that the objective is meaningful and not trivial.

    Args:
        objective: The objective string to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not objective or len(objective.strip()) < 5:
        return False
    return not objective.strip().isdigit()


def validate_plan(tasks: list[PlannedTask], files: list[str], objective:
    str, planner_name: str) ->None:
    """
    Validate the generated plan for consistency and completeness.

    Raises PlanValidationError if validation fails.

    Args:
        tasks: List of planned tasks
        files: List of target files
        objective: The mission objective
        planner_name: Name of the planner (for error reporting)

    Raises:
        PlanValidationError: If validation fails
    """
    from ..base_planner import PlanValidationError
    if len(tasks) > config.GLOBAL_TASK_CAP:
        raise PlanValidationError('excessive_tasks', planner_name, objective)
    ids = {t.task_id for t in tasks}
    for t in tasks:
        for d in t.dependencies:
            if d not in ids:
                raise PlanValidationError(
                    f'dangling_dependency:{t.task_id}->{d}', planner_name,
                    objective)
    if config.STRICT_WRITE_ENF:
        for f in files:
            if not any(tt.tool_name in (config.TOOL_WRITE, config.
                TOOL_APPEND) and (tt.tool_args or {}).get('path', '').lower
                () == f.lower() for tt in tasks):
                raise PlanValidationError(f'missing_file_write:{f}',
                    planner_name, objective)
