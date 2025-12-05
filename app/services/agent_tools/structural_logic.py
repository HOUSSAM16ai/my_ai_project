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
    if not DEEP_MAP_PATH or not os.path.isfile(DEEP_MAP_PATH):
        return False
    with g._DEEP_LOCK:
        if (
            not force
            and DEEP_MAP_TTL > 0
            and (_now() - g._DEEP_STRUCT_LOADED_AT) < DEEP_MAP_TTL
            and g._DEEP_STRUCT_MAP is not None
        ):
            return False
        try:
            with open(DEEP_MAP_PATH, encoding="utf-8") as f:
                raw = f.read()
            new_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            if new_hash == g._DEEP_STRUCT_HASH and g._DEEP_STRUCT_MAP is not None and not force:
                g._DEEP_STRUCT_LOADED_AT = _now()
                return False
            data = json.loads(raw)
            files = data.get("files") or {}
            norm_files = {}
            for k, v in files.items():
                if isinstance(k, str):
                    norm_files[os.path.abspath(k).lower()] = v
            data["files"] = norm_files
            g._DEEP_STRUCT_MAP = data
            g._DEEP_STRUCT_HASH = new_hash
            g._DEEP_STRUCT_LOADED_AT = _now()
            _dbg(f"[deep_struct_map] loaded entries={len(norm_files)} hash={new_hash[:10]}")
            return True
        except Exception as e:
            _dbg(f"[deep_struct_map] load failed: {e}")
            return False


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
