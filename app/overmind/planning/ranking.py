# app/overmind/planning/ranking.py
# ======================================================================================
# PLANNER FACTORY RANKING - SCORING & SELECTION LOGIC
# Version 5.0.0 - Deterministic Ranking
# ======================================================================================
"""
Ranking and scoring logic for planner selection.
Implements deterministic scoring with deep context awareness.
"""

from typing import Any


def capabilities_match_ratio(required: set[str], offered: set[str]) -> float:
    """
    Calculate match ratio between required and offered capabilities.

    Args:
        required: Set of required capabilities
        offered: Set of offered capabilities

    Returns:
        Match ratio between 0.0 and 1.0
    """
    if not required:
        return 1.0
    if not offered:
        return 0.0
    intersection = required & offered
    return len(intersection) / max(len(required), 1)


def compute_rank_hint(
    objective_length: int,
    capabilities_match_ratio: float,
    reliability_score: float,
    tier: str | None,
    production_ready: bool,
) -> float:
    """
    Compute deterministic rank hint for a planner.

    This is a fallback implementation used when BasePlanner.compute_rank_hint
    is not available or fails.

    Args:
        objective_length: Length of the objective string
        capabilities_match_ratio: Ratio of matching capabilities
        reliability_score: Reliability score of the planner
        tier: Tier of the planner (alpha, beta, stable, gold, vip)
        production_ready: Whether the planner is production ready

    Returns:
        Computed rank hint score
    """
    # Base score from capabilities and reliability
    score = capabilities_match_ratio * 0.6 + reliability_score * 0.35

    # Production ready bonus
    if production_ready:
        score += 0.04

    # Tier bonus
    if tier and isinstance(tier, str):
        tier_map = {
            "alpha": -0.05,
            "beta": 0.0,
            "stable": 0.05,
            "gold": 0.07,
            "vip": 0.08,
        }
        score += tier_map.get(tier.lower(), 0.0)

    # NOTE: We do NOT add hash-based tie-breaking for determinism
    # score += (hash(name) & 0xFFFF) * 1e-10  # REMOVED for determinism

    return score


def compute_deep_boosts(
    capabilities: set[str],
    required_capabilities: set[str],
    deep_context: dict[str, Any] | None,
    deep_index_cap_boost: float,
    hotspot_cap_boost: float,
    hotspot_threshold: int,
) -> tuple[float, dict[str, Any]]:
    """
    Compute deep context-based boost scores.

    Args:
        capabilities: Planner's capabilities
        required_capabilities: Required capabilities
        deep_context: Deep context information
        deep_index_cap_boost: Boost weight for deep_index capability
        hotspot_cap_boost: Boost weight for hotspot capability
        hotspot_threshold: Minimum hotspot count to trigger boost

    Returns:
        Tuple of (total_boost, breakdown_dict)
    """
    breakdown = {"deep_boost": 0.0, "hotspot_boost": 0.0}

    if not deep_context or not isinstance(deep_context, dict):
        return 0.0, breakdown

    # Convert capabilities to lowercase for matching
    caps_lower = {c.lower().strip() for c in capabilities}

    # Deep index boost
    deep_index_summary = bool(deep_context.get("deep_index_summary"))
    if deep_index_summary and "deep_index" in caps_lower:
        boost = max(deep_index_cap_boost, 0.0)
        breakdown["deep_boost"] = boost

    # Hotspot boost
    hotspots_count = _to_int(deep_context.get("hotspots_count"), 0)
    hotspot_related_caps = {"refactor", "risk", "structural"}
    if hotspots_count > hotspot_threshold and (hotspot_related_caps & caps_lower):
        hboost = max(hotspot_cap_boost, 0.0)
        breakdown["hotspot_boost"] = hboost

    total_boost = breakdown["deep_boost"] + breakdown["hotspot_boost"]
    return total_boost, breakdown


def _to_int(value, default: int = 0) -> int:
    """Safe conversion to int with fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def create_sort_key(
    score: float, reliability: float, name: str, reverse_score: bool = True
) -> tuple:
    """
    Create a deterministic sort key for planner candidates.

    Args:
        score: Total score for the planner
        reliability: Reliability score
        name: Planner name
        reverse_score: Whether to reverse score (higher is better)

    Returns:
        Tuple suitable for sorting
    """
    # Deterministic sort order:
    # 1. Score (descending)
    # 2. Reliability (descending)
    # 3. Name (ascending, for tie-breaking)
    return (
        -score if reverse_score else score,
        -reliability,
        name,
    )


def rank_planners(
    candidates: dict[str, Any],
    objective: str,
    required_capabilities: set[str] | None,
    prefer_production: bool,
    deep_context: dict[str, Any] | None,
    config: Any,
) -> list[tuple[float, str, dict[str, Any]]]:
    """
    Rank a collection of planner candidates.

    Args:
        candidates: Dictionary of planner records
        objective: Objective string
        required_capabilities: Required capabilities
        prefer_production: Whether to prefer production-ready planners
        deep_context: Deep context for boosting
        config: FactoryConfig instance

    Returns:
        List of (score, name, breakdown) tuples, sorted by score descending
    """
    req_set = required_capabilities or set()
    ranked = []

    for name, rec in candidates.items():
        # Get reliability
        reliability = (
            rec.reliability_score
            if rec.reliability_score is not None
            else config.default_reliability
        )

        # Apply production penalty if needed
        if prefer_production and not rec.production_ready and req_set:
            reliability *= 0.97

        # Calculate capability match
        cap_ratio = capabilities_match_ratio(req_set, rec.capabilities or set())

        # Compute base score
        base_score = compute_rank_hint(
            objective_length=len(objective or ""),
            capabilities_match_ratio=cap_ratio,
            reliability_score=reliability,
            tier=rec.tier,
            production_ready=bool(rec.production_ready),
        )

        # Compute deep context boosts
        add_score, boost_breakdown = compute_deep_boosts(
            capabilities=rec.capabilities or set(),
            required_capabilities=req_set,
            deep_context=deep_context,
            deep_index_cap_boost=config.deep_index_cap_boost,
            hotspot_cap_boost=config.hotspot_cap_boost,
            hotspot_threshold=config.hotspot_threshold,
        )

        total_score = base_score + add_score

        # Create breakdown for telemetry
        breakdown = {
            "base_score": base_score,
            "cap_ratio": round(cap_ratio, 4),
            "reliability": reliability,
            "tier": rec.tier,
            "production_ready": bool(rec.production_ready),
            "deep_boost": boost_breakdown["deep_boost"],
            "hotspot_boost": boost_breakdown["hotspot_boost"],
            "total_score": total_score,
        }

        ranked.append((total_score, name, breakdown))

    # Deterministic sort
    ranked.sort(
        key=lambda x: create_sort_key(
            x[0], candidates[x[1]].reliability_score or config.default_reliability, x[1]
        )
    )

    return ranked


__all__ = [
    "capabilities_match_ratio",
    "compute_deep_boosts",
    "compute_rank_hint",
    "create_sort_key",
    "rank_planners",
]
