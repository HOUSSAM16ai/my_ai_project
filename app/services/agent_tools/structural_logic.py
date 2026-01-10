"""
Hyper-Structural Logic
======================
Logic for managing deep structural maps and layer stats.
Separated from tools to allow usage in other modules.
"""

import hashlib
import json
import os
from typing import Any

# Redefining to use direct module access for re-assignment compatibility
from . import globals as g
from .definitions import (
    DEEP_LIMIT_KEYS,
    DEEP_MAP_PATH,
    DEEP_MAP_TTL,
    HASH_AFTER_WRITE,
)
from .utils import _dbg, _file_hash, _now


def _touch_layer(layer: str, op: str):
    if not layer:
        return
    with g._LAYER_LOCK:
        d = g._LAYER_STATS.setdefault(
            layer, {"reads": 0, "writes": 0, "appends": 0, "ensures": 0, "last_ts": 0.0}
        )
        if op in d:
            d[op] += 1
        d["last_ts"] = _now()

def _load_deep_struct_map_logic(force: bool = False) -> bool:
    """
    Load deep structure map from file with caching.

    تحميل خريطة البنية العميقة من الملف مع التخزين المؤقت.

    Args:
        force: Force reload even if cached

    Returns:
        True if map was loaded/reloaded, False if using cache
    """
    if not DEEP_MAP_PATH or not os.path.isfile(DEEP_MAP_PATH):
        return False

    with g._DEEP_LOCK:
        # Check if cache is still valid
        if _should_use_cached_map(force):
            return False

        # Load and parse file
        return _load_and_update_map(force)


def _should_use_cached_map(force: bool) -> bool:
    """
    Check if cached map is still valid.

    التحقق مما إذا كانت الخريطة المخزنة مؤقتاً لا تزال صالحة.
    """
    if force:
        return False

    if DEEP_MAP_TTL <= 0:
        return False

    time_since_load = _now() - g._DEEP_STRUCT_LOADED_AT
    if time_since_load >= DEEP_MAP_TTL:
        return False

    return g._DEEP_STRUCT_MAP is not None


def _load_and_update_map(force: bool) -> bool:
    """
    Load map file and update global state.

    تحميل ملف الخريطة وتحديث الحالة العامة.
    """
    try:
        # Read and hash file content
        with open(DEEP_MAP_PATH, encoding="utf-8") as f:
            raw = f.read()
        new_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        # Check if content has changed
        if _is_same_content(new_hash, force):
            g._DEEP_STRUCT_LOADED_AT = _now()
            return False

        # Parse and normalize data
        data = json.loads(raw)
        norm_files = _normalize_file_paths(data.get("files") or {})
        data["files"] = norm_files

        # Update global state
        _update_global_map_state(data, new_hash, len(norm_files))
        return True

    except Exception as e:
        _dbg(f"[deep_struct_map] load failed: {e}")
        return False


def _is_same_content(new_hash: str, force: bool) -> bool:
    """
    Check if content hash matches cached version.

    التحقق مما إذا كان تجزئة المحتوى يطابق النسخة المخزنة مؤقتاً.
    """
    if force:
        return False

    return (
        new_hash == g._DEEP_STRUCT_HASH
        and g._DEEP_STRUCT_MAP is not None
    )


def _normalize_file_paths(files: dict) -> dict:
    """
    Normalize file paths to absolute lowercase.

    تطبيع مسارات الملفات إلى مسارات مطلقة بأحرف صغيرة.
    """
    norm_files = {}
    for k, v in files.items():
        if isinstance(k, str):
            norm_files[os.path.abspath(k).lower()] = v
    return norm_files


def _update_global_map_state(data: dict, new_hash: str, file_count: int) -> None:
    """
    Update global map state with new data.

    تحديث حالة الخريطة العامة بالبيانات الجديدة.
    """
    g._DEEP_STRUCT_MAP = data
    g._DEEP_STRUCT_HASH = new_hash
    g._DEEP_STRUCT_LOADED_AT = _now()
    _dbg(f"[deep_struct_map] loaded entries={file_count} hash={new_hash[:10]}")

def _maybe_reload_struct_map():
    if not DEEP_MAP_PATH:
        return
    if DEEP_MAP_TTL == 0:
        if g._DEEP_STRUCT_MAP is None:
            _load_deep_struct_map_logic(force=True)
        return
    if (_now() - g._DEEP_STRUCT_LOADED_AT) >= DEEP_MAP_TTL:
        _load_deep_struct_map_logic(force=False)

def _annotate_struct_meta(abs_path: str, meta: dict[str, Any]):
    _maybe_reload_struct_map()
    if not g._DEEP_STRUCT_MAP:
        return
    info = g._DEEP_STRUCT_MAP.get("files", {}).get(abs_path.lower())
    if not info:
        return
    layer = info.get("layer")
    hotspot = info.get("hotspot")
    dup_group = info.get("dup_group")
    meta.update({"struct_layer": layer, "struct_hotspot": hotspot, "struct_dup_group": dup_group})

def _maybe_hash_and_size(abs_path: str, result_data: dict[str, Any]):
    if HASH_AFTER_WRITE and os.path.isfile(abs_path):
        try:
            result_data["sha256"] = _file_hash(abs_path)
            result_data["size_after"] = os.path.getsize(abs_path)
        except Exception:
            pass

def _apply_struct_limit(meta: dict[str, Any]):
    if not DEEP_LIMIT_KEYS or not meta:
        return
    keys = list(meta.keys())
    if len(keys) <= DEEP_LIMIT_KEYS:
        return
    priority = {"struct_layer", "struct_hotspot", "struct_dup_group"}
    ordered = [k for k in keys if k in priority] + [k for k in keys if k not in priority]
    trimmed = ordered[:DEEP_LIMIT_KEYS]
    for k in keys:
        if k not in trimmed:
            meta.pop(k, None)
    meta["_struct_limited"] = True
