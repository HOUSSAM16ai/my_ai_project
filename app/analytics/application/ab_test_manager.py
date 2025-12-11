"""A/B testing use case."""

import hashlib
import time
from datetime import UTC, datetime

from app.analytics.domain import ABTestResults, ABTestStorePort


class ABTestManager:
    """Handles A/B testing logic"""

    def __init__(self, ab_test_store: ABTestStorePort):
        self.ab_test_store = ab_test_store

    def create_ab_test(
        self,
        test_name: str,
        variants: list[str],
        traffic_split: dict[str, float] | None = None,
    ) -> str:
        """Create a new A/B test"""
        test_id = hashlib.sha256(f"{test_name}{time.time_ns()}".encode()).hexdigest()[:16]

        if traffic_split is None:
            split = 1.0 / len(variants)
            traffic_split = dict.fromkeys(variants, split)

        test_data = {
            "test_name": test_name,
            "variants": variants,
            "traffic_split": traffic_split,
            "created_at": datetime.now(UTC),
            "results": {variant: {"users": set(), "conversions": 0} for variant in variants},
        }

        self.ab_test_store.add_test(test_id, test_data)
        return test_id

    def assign_variant(self, test_id: str, user_id: int) -> str:
        """Assign user to A/B test variant"""
        test = self.ab_test_store.get_test(test_id)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        # Check if user already assigned
        for variant, data in test["results"].items():
            if user_id in data["users"]:
                return variant

        # Assign based on user_id hash (deterministic)
        hash_val = int(hashlib.md5(f"{user_id}{test_id}".encode()).hexdigest(), 16)
        cumulative = 0.0
        normalized_hash = (hash_val % 10000) / 10000.0

        for variant, split in test["traffic_split"].items():
            cumulative += split
            if normalized_hash <= cumulative:
                test["results"][variant]["users"].add(user_id)
                self.ab_test_store.update_test(test_id, test)
                return variant

        # Fallback
        first_variant = test["variants"][0]
        test["results"][first_variant]["users"].add(user_id)
        self.ab_test_store.update_test(test_id, test)
        return first_variant

    def record_ab_conversion(self, test_id: str, user_id: int) -> None:
        """Record conversion for A/B test"""
        test = self.ab_test_store.get_test(test_id)
        if not test:
            return

        # Find user's variant
        for _variant, data in test["results"].items():
            if user_id in data["users"]:
                data["conversions"] += 1
                self.ab_test_store.update_test(test_id, test)
                break

    def get_ab_test_results(self, test_id: str) -> ABTestResults | None:
        """Get A/B test results"""
        test = self.ab_test_store.get_test(test_id)
        if not test:
            return None

        control_variant = test["variants"][0]
        test_variants = test["variants"][1:]
        results = test["results"]

        # Calculate conversion rates
        control_users = len(results[control_variant]["users"])
        control_conversions = results[control_variant]["conversions"]
        control_rate = control_conversions / control_users if control_users > 0 else 0.0

        variant_rates = {}
        variant_sizes = {}
        for variant in test_variants:
            users = len(results[variant]["users"])
            conversions = results[variant]["conversions"]
            variant_rates[variant] = conversions / users if users > 0 else 0.0
            variant_sizes[variant] = users

        # Find winner
        best_rate = control_rate
        winner = control_variant
        for variant, rate in variant_rates.items():
            if rate > best_rate:
                best_rate = rate
                winner = variant

        improvement = (best_rate - control_rate) / control_rate * 100 if control_rate > 0 else 0.0

        # Statistical significance (simplified)
        statistical_significance = 0.95 if control_users > 100 else 0.0

        return ABTestResults(
            test_id=test_id,
            test_name=test["test_name"],
            control_variant=control_variant,
            test_variants=test_variants,
            control_conversion_rate=control_rate,
            variant_conversion_rates=variant_rates,
            control_sample_size=control_users,
            variant_sample_sizes=variant_sizes,
            statistical_significance=statistical_significance,
            winner=winner if improvement > 5 else None,
            improvement_percent=improvement,
        )
