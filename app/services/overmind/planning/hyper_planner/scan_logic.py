import glob
import logging
import os

from app.services.overmind.planning.schemas import PlannedTask

from . import config, utils

_LOG = logging.getLogger("ultra_hyper_planner.scan")


# --------------------------------------------------------------------------------------
# Repo Scan Logic (Controller-free)
# --------------------------------------------------------------------------------------
def wants_repo_scan(objective: str) -> bool:
    """Determines if the objective requires a full repository scan."""
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


def generate_repo_scan_tasks(idx: int, deps_accum: list[str]) -> tuple[int, list[PlannedTask]]:
    """Generates the specific tasks required for a repository scan."""
    tasks = []

    # 1. Directory Listing
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

    # 2. Core File Reading
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

    return idx, tasks


# --------------------------------------------------------------------------------------
# Extra Source Scan
# --------------------------------------------------------------------------------------
def _collect_extra_files() -> list[str]:
    collected: set[str] = set()
    # Globs
    for pattern in config.EXTRA_READ_GLOBS:
        for p in glob.glob(pattern, recursive=True):
            if len(collected) >= config.SCAN_MAX_FILES:
                break
            if os.path.isfile(p):
                collected.add(p)
        if len(collected) >= config.SCAN_MAX_FILES:
            break
    # Directories
    for base in config.SCAN_DIRS:
        if not os.path.isdir(base):
            continue
        if config.SCAN_RECURSIVE:
            for root, _, files in os.walk(base):
                for f in files:
                    if len(collected) >= config.SCAN_MAX_FILES:
                        break
                    ext = os.path.splitext(f)[1].lower()
                    if ext in config.SCAN_EXTS:
                        collected.add(os.path.join(root, f))
                if len(collected) >= config.SCAN_MAX_FILES:
                    break
        else:
            for f in os.listdir(base):
                if len(collected) >= config.SCAN_MAX_FILES:
                    break
                fp = os.path.join(base, f)
                if os.path.isfile(fp):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in config.SCAN_EXTS:
                        collected.add(fp)
        if len(collected) >= config.SCAN_MAX_FILES:
            break
    return sorted(collected)[: config.SCAN_MAX_FILES]


def _container_files_present() -> list[str]:
    return [f for f in ("docker-compose.yml", ".env") if os.path.exists(f)]
