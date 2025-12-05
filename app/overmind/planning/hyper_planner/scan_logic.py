
import os
import glob
import logging
from typing import Any

from . import config, utils

_LOG = logging.getLogger("ultra_hyper_planner.scan")

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
    return sorted(collected)[:config.SCAN_MAX_FILES]


def _container_files_present() -> list[str]:
    return [f for f in ("docker-compose.yml", ".env") if os.path.exists(f)]
