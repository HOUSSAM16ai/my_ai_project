"""
Cost Manager Module for LLM Services
====================================
Tracks token usage, estimates costs, and enforces budget limits.
"""

import json
import logging
import os
from typing import Any

_LOG = logging.getLogger(__name__)

class CostManager:
    """
    Singleton Cost Manager for LLM calls.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CostManager, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self._stats = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "calls": 0,
            "errors": 0,
            "last_error_kind": None,
            "latencies_ms": [],
            "cost_usd": 0.0,
        }
        self._latency_window = 300

    def estimate_cost(
        self, model: str, prompt_tokens: int | None, completion_tokens: int | None
    ) -> float | None:
        try:
            cost_table = json.loads(os.getenv("MODEL_COST_TABLE_JSON", "{}"))
            alias_map = json.loads(os.getenv("MODEL_ALIAS_MAP_JSON", "{}"))
        except Exception:
            cost_table = {}
            alias_map = {}

        if not model:
            return None
        model_key = alias_map.get(model, model)
        data = cost_table.get(model_key)
        if not data:
            return None
        p_rate = data.get("prompt", 0)
        c_rate = data.get("completion", 0)
        pt = prompt_tokens or 0
        ct = completion_tokens or 0
        return round(pt * p_rate + ct * c_rate, 6)

    def update_metrics(
        self,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        total_tokens: int | None,
        latency_ms: float,
        cost: float | None,
        error_kind: str | None = None
    ):
        self._stats["calls"] += 1
        if prompt_tokens:
            self._stats["prompt_tokens"] += prompt_tokens
        if completion_tokens:
            self._stats["completion_tokens"] += completion_tokens
        if total_tokens:
            self._stats["total_tokens"] += total_tokens

        if error_kind:
             self._stats["errors"] += 1
             self._stats["last_error_kind"] = error_kind

        self._stats["latencies_ms"].append(latency_ms)
        if len(self._stats["latencies_ms"]) > self._latency_window:
             self._stats["latencies_ms"][:] = self._stats["latencies_ms"][-self._latency_window:]

        if cost:
            self._stats["cost_usd"] += cost
            self._enforce_budget(cost)

    def _enforce_budget(self, new_cost: float) -> None:
        budget_session = float(os.getenv("LLM_COST_BUDGET_SESSION", "0") or 0.0)
        hard_fail = os.getenv("LLM_COST_BUDGET_HARD_FAIL", "0") == "1"

        if budget_session <= 0:
            return

        projected = self._stats["cost_usd"]
        # Note: we already added new_cost to cost_usd in update_metrics,
        # so projected is just current total.

        if projected > budget_session:
            msg = (
                f"LLM session cost budget exceeded: projected={projected:.6f} > "
                f"budget={budget_session:.6f}"
            )
            if hard_fail:
                raise RuntimeError(msg)
            _LOG.warning("[LLM] %s (soft warn).", msg)

    def get_stats(self) -> dict[str, Any]:
        lat = self._stats["latencies_ms"]
        avg_lat = round(sum(lat) / len(lat), 2) if lat else None

        return {
            "cumulative": {
                "prompt_tokens": self._stats["prompt_tokens"],
                "completion_tokens": self._stats["completion_tokens"],
                "total_tokens": self._stats["total_tokens"],
                "calls": self._stats["calls"],
                "errors": self._stats["errors"],
                "last_error_kind": self._stats["last_error_kind"],
                "avg_latency_ms": avg_lat,
                "cost_usd": round(self._stats["cost_usd"], 6),
            },
            "latencies_raw": lat
        }
