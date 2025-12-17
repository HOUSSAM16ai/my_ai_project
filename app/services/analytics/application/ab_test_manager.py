# app/services/analytics/application/ab_test_manager.py
"""
A/B Test Manager Service
=========================
Single Responsibility: Manage A/B testing experiments.
"""

from __future__ import annotations

import hashlib
from typing import Any


class ABTestManager:
    """
    A/B test experiment manager.

    Responsibilities:
    - Create A/B tests
    - Assign variants to users
    - Track conversions
    - Calculate statistical significance
    """

    def __init__(self):
        self._tests: dict[str, dict[str, Any]] = {}
        self._user_assignments: dict[str, dict[int, str]] = {}  # test_id -> {user_id -> variant}
        self._conversions: dict[str, dict[str, set[int]]] = {}  # test_id -> {variant -> user_ids}

    def create_test(
        self,
        test_name: str,
        variants: list[str],
        traffic_split: dict[str, float] | None = None,
    ) -> str:
        """Create new A/B test"""
        test_id = hashlib.sha256(f"{test_name}{len(self._tests)}".encode()).hexdigest()[:16]

        # Default equal split if not provided
        if traffic_split is None:
            split_percent = 1.0 / len(variants)
            traffic_split = {v: split_percent for v in variants}

        self._tests[test_id] = {
            "test_name": test_name,
            "variants": variants,
            "traffic_split": traffic_split,
            "created_at": None,  # Could add datetime
        }

        self._user_assignments[test_id] = {}
        self._conversions[test_id] = {v: set() for v in variants}

        return test_id

    def assign_variant(self, test_id: str, user_id: int) -> str:
        """Assign variant to user (deterministic based on user_id)"""
        if test_id not in self._tests:
            raise ValueError(f"Test {test_id} not found")

        # Check if user already assigned
        if user_id in self._user_assignments[test_id]:
            return self._user_assignments[test_id][user_id]

        # Deterministic assignment based on user_id hash
        variants = self._tests[test_id]["variants"]
        hash_val = hashlib.md5(f"{test_id}{user_id}".encode()).hexdigest()
        index = int(hash_val, 16) % len(variants)
        variant = variants[index]

        self._user_assignments[test_id][user_id] = variant
        return variant

    def record_conversion(self, test_id: str, user_id: int) -> None:
        """Record conversion for user"""
        if test_id not in self._tests:
            raise ValueError(f"Test {test_id} not found")

        # Get user's assigned variant
        variant = self._user_assignments[test_id].get(user_id)
        if variant:
            self._conversions[test_id][variant].add(user_id)

    def get_results(self, test_id: str) -> dict[str, Any] | None:
        """Get A/B test results"""
        if test_id not in self._tests:
            return None

        test = self._tests[test_id]
        variants = test["variants"]

        # Calculate conversion rates per variant
        variant_stats = {}
        for variant in variants:
            assigned = sum(
                1 for v in self._user_assignments[test_id].values() if v == variant
            )
            conversions = len(self._conversions[test_id][variant])
            conversion_rate = conversions / assigned if assigned > 0 else 0.0

            variant_stats[variant] = {
                "assigned": assigned,
                "conversions": conversions,
                "conversion_rate": conversion_rate,
            }

        # Find winner (highest conversion rate)
        winner = max(
            variants,
            key=lambda v: variant_stats[v]["conversion_rate"],
        ) if variant_stats else None

        # Calculate improvement vs control (first variant)
        control = variants[0] if variants else None
        improvement_percent = 0.0
        if control and winner and winner != control:
            control_rate = variant_stats[control]["conversion_rate"]
            winner_rate = variant_stats[winner]["conversion_rate"]
            if control_rate > 0:
                improvement_percent = ((winner_rate - control_rate) / control_rate) * 100

        # Statistical significance (simplified)
        statistical_significance = self._calculate_significance(variant_stats)

        return {
            "test_id": test_id,
            "test_name": test["test_name"],
            "variants": variant_stats,
            "winner": winner,
            "improvement_percent": improvement_percent,
            "statistical_significance": statistical_significance,
        }

    def _calculate_significance(self, variant_stats: dict[str, Any]) -> float:
        """Calculate statistical significance (simplified p-value)"""
        # Simplified calculation - in production use proper statistical tests
        # like chi-square or z-test
        total_samples = sum(v["assigned"] for v in variant_stats.values())

        if total_samples < 100:
            return 0.0  # Not enough data
        elif total_samples < 1000:
            return 0.5  # Low confidence
        elif total_samples < 5000:
            return 0.8  # Medium confidence
        else:
            return 0.95  # High confidence
