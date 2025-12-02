# app/overmind/planning/_structural_scoring.py
"""
Structural scoring logic extracted from base_planner for reduced complexity.
Computes quality scores based on structural metrics (grade, entropy, density, diversity).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ._configs import StructuralScoringConfig


def safe_numeric(value: Any, default: float = 0.0) -> float:
    """Safely convert value to numeric, returning default if not a number."""
    return value if isinstance(value, (int, float)) and value is not None else default


@dataclass
class StructuralEnrichmentResult:
    """Result of structural enrichment computation."""

    struct_base_score: float
    grade: str | None
    struct_bonus: float
    reliability_nudge_applied: bool = False
    reliability_score_apparent: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for metadata updates."""
        result = {
            "struct_base_score": round(self.struct_base_score, 4),
            "struct_grade": self.grade,
            "struct_bonus": round(self.struct_bonus, 4),
        }
        if self.reliability_nudge_applied:
            result["reliability_nudge_applied"] = True
            if self.reliability_score_apparent is not None:
                result["reliability_score_apparent"] = round(self.reliability_score_apparent, 4)
        return result


def compute_structural_base_score(
    plan_meta: Any, config: StructuralScoringConfig
) -> tuple[float, str | None]:
    """
    Compute base structural score from plan metadata.

    Args:
        plan_meta: PlanMeta object with structural metrics
        config: Scoring configuration

    Returns:
        Tuple of (base_score, grade_used)
    """
    grade = getattr(plan_meta, "structural_quality_grade", None)

    hotspot_density = safe_numeric(getattr(plan_meta, "hotspot_density", None))
    layer_diversity = safe_numeric(getattr(plan_meta, "layer_diversity", None))
    entropy = safe_numeric(getattr(plan_meta, "structural_entropy", None))

    grade_component = config.grade_components.get(grade, config.default_grade_component)

    # Compute composite score (normalized 0-1)
    struct_base = (
        grade_component + (1 - abs(hotspot_density - 0.25)) + layer_diversity + entropy
    ) / 4.0
    struct_base = max(0.0, min(1.0, struct_base))

    return struct_base, grade


def compute_grade_bonus(grade: str | None, config: StructuralScoringConfig) -> float:
    """Compute additive bonus based on grade."""
    if grade is None:
        return config.grade_bonuses.get("C", 0.0)
    return config.grade_bonuses.get(grade, 0.0)


def apply_reliability_adjustments(
    grade: str | None, reliability_score: float, config: StructuralScoringConfig
) -> tuple[bool, float | None]:
    """
    Apply reliability nudge for grade A outputs.

    Args:
        grade: Structural quality grade
        reliability_score: Current reliability score
        config: Scoring configuration

    Returns:
        Tuple of (nudge_applied, apparent_score)
    """
    if grade == "A" and config.reliability_nudge > 0:
        apparent_score = min(1.0, reliability_score + config.reliability_nudge)
        return True, apparent_score
    return False, None


def compute_structural_enrichment(
    plan_meta: Any, reliability_score: float, config: StructuralScoringConfig
) -> StructuralEnrichmentResult:
    """
    Main orchestrator for structural enrichment computation.

    Args:
        plan_meta: PlanMeta object with structural metrics
        reliability_score: Current planner reliability score
        config: Scoring configuration

    Returns:
        StructuralEnrichmentResult with all computed values
    """
    struct_base, grade = compute_structural_base_score(plan_meta, config)
    struct_bonus = compute_grade_bonus(grade, config)
    nudge_applied, apparent_score = apply_reliability_adjustments(
        grade, reliability_score, config
    )

    return StructuralEnrichmentResult(
        struct_base_score=struct_base,
        grade=grade,
        struct_bonus=struct_bonus,
        reliability_nudge_applied=nudge_applied,
        reliability_score_apparent=apparent_score,
    )


def compute_final_selection_score(
    base_selection: float,
    struct_base: float,
    struct_bonus: float,
    struct_enabled: bool,
    config: StructuralScoringConfig,
) -> float:
    """
    Compute final selection score with structural augmentation.

    Args:
        base_selection: Base selection score from planner
        struct_base: Structural base score
        struct_bonus: Grade bonus
        struct_enabled: Whether structural scoring is enabled
        config: Scoring configuration

    Returns:
        Final selection score (clamped to 0-1)
    """
    if not struct_enabled or not struct_base:
        return base_selection

    final = base_selection + struct_base * config.struct_weight + struct_bonus
    return min(1.0, final)
