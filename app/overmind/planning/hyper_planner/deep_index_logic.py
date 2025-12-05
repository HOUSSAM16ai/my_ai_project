
import os
import logging
from typing import Any, Tuple
from .. import deep_indexer
from . import config, utils

_LOG = logging.getLogger("ultra_hyper_planner.deep_index")

# --------------------------------------------------------------------------------------
# Deep Index Imports
# --------------------------------------------------------------------------------------
_DEEP_INDEX_ENABLED = os.getenv("PLANNER_DEEP_INDEX_ENABLE", "1") == "1"
if _DEEP_INDEX_ENABLED:
    try:
        from ..deep_indexer import build_index, summarize_for_prompt

        _HAS_INDEXER = True
    except Exception as _e:
        _LOG.warning("Deep indexer import failed: %s", _e)
        _HAS_INDEXER = False
else:
    _HAS_INDEXER = False


def attempt_deep_index(
    tasks: list[Any], idx: int, base_deps: list[str], lang: str
) -> Tuple[dict[str, Any], dict[str, Any]]:
    # PlannedTask imported inside core to avoid circular dep if needed, but passing Any here
    # Actually we need PlannedTask. We will import from core or schema.
    # To keep this clean, let's assume the caller handles the Task creation or we import schemas.
    # We will import PlannedTask inside function to avoid circular import if schemas are used elsewhere
    # But best practice is to have schemas separate.
    # For now, let's just return data needed to create tasks, or accept a callback?
    # No, let's do what the original did but cleaner.
    from ..schemas import PlannedTask

    struct_meta = {"attached": False}
    deps_out = []
    if not (_DEEP_INDEX_ENABLED and _HAS_INDEXER):
        return struct_meta, {"next_idx": idx, "deps": deps_out}
    try:
        index_data = build_index(".")
        # cache placeholder (future): if INDEX_CACHE_ENABLE: ...
        struct_meta.update(
            {
                "attached": True,
                "files_scanned": index_data.get("files_scanned"),
                "hotspot_count": (
                    len(index_data.get("complexity_hotspots_top50", []))
                    if index_data.get("complexity_hotspots_top50")
                    else None
                ),
                "duplicate_groups": (
                    len(index_data.get("duplicate_function_bodies", {}))
                    if index_data.get("duplicate_function_bodies")
                    else None
                ),
                "index_version": index_data.get("index_version", "ast-deep-v1"),
            }
        )
        # store summary inline (for semantic reuse)
        summary_text = summarize_for_prompt(index_data, max_len=config.DEEP_INDEX_SUMMARY_MAX)
        struct_meta["summary_inline"] = summary_text

        # JSON
        if config.DEEP_INDEX_JSON_EN:
            truncated_json = _truncate_json(index_data, config.DEEP_INDEX_MAX_JSON)
            json_task = utils._tid(idx)
            idx += 1
            tasks.append(
                PlannedTask(
                    task_id=json_task,
                    description="Write structural index JSON.",
                    tool_name=config.TOOL_WRITE,
                    tool_args={"path": config.DEEP_INDEX_JSON_NAME, "content": truncated_json},
                    dependencies=base_deps,
                )
            )
            deps_out.append(json_task)
            struct_meta["json_task"] = json_task
        # MD summary
        if config.DEEP_INDEX_MD_EN:
            header = (
                "## Structural AST Index Summary\n"
                if lang != "ar"
                else "## ملخص الفهرسة البنائية (AST)\n"
            )
            md_content = header + "\n```\n" + summary_text + "\n```\n"
            md_task = utils._tid(idx)
            idx += 1
            tasks.append(
                PlannedTask(
                    task_id=md_task,
                    description="Write structural summary markdown.",
                    tool_name=config.TOOL_WRITE,
                    tool_args={"path": config.DEEP_INDEX_MD_NAME, "content": md_content},
                    dependencies=base_deps,
                )
            )
            deps_out.append(md_task)
            struct_meta["md_task"] = md_task
    except Exception as e:
        _LOG.warning("Deep index failed: %s", e)
    return struct_meta, {"next_idx": idx, "deps": deps_out}

def _truncate_json(data: dict[str, Any], max_bytes: int) -> str:
    import json
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if len(raw.encode("utf-8")) <= max_bytes:
        return raw
    slim = dict(data)
    if "modules" in slim:
        slim["modules"] = [
            {
                "path": m.get("path"),
                "fn_count": len(m.get("functions", [])),
                "class_count": len(m.get("classes", [])),
            }
            for m in slim["modules"][:250]
        ]
    raw2 = json.dumps(slim, ensure_ascii=False, separators=(",", ":"))
    if len(raw2.encode("utf-8")) <= max_bytes:
        return raw2
    return raw2[: max_bytes - 60] + "...TRUNCATED..."
