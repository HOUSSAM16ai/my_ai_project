"""
A/B Test Repository Implementation
===================================
Concrete implementation for A/B test data storage and retrieval.

Uses in-memory storage. Production systems should use PostgreSQL,
Redis, or specialized experimentation platforms.
"""
from __future__ import annotations
import hashlib
import threading
from datetime import datetime
from typing import Any
from app.services.analytics.domain.models import ABTestVariant
from app.services.analytics.domain.ports import ABTestManagerPort


class InMemoryABTestRepository(ABTestManagerPort):
    """
    In-memory A/B test repository.

    Features:
    - Thread-safe test management
    - Deterministic user assignment
    - Conversion tracking
    - Statistical analysis
    """

    def __init__(self):
        """Initialize A/B test repository."""
        self._tests: dict[str, dict[str, Any]] = {}
        self._user_assignments: dict[str, dict[int, ABTestVariant]] = {}
        self._conversions: dict[str, dict[ABTestVariant, set[int]]] = {}
        self._lock = threading.RLock()

    def create_test(self, test_id: str, test_name: str, variants: list[
        ABTestVariant]) ->None:
        """
        Create a new A/B test.

        Args:
            test_id: Test identifier
            test_name: Test name
            variants: List of test variants
        """
        with self._lock:
            if test_id in self._tests:
                raise ValueError(f'Test {test_id} already exists')
            self._tests[test_id] = {'test_id': test_id, 'test_name':
                test_name, 'variants': variants, 'created_at': datetime.
                utcnow(), 'status': 'active'}
            self._user_assignments[test_id] = {}
            self._conversions[test_id] = {variant: set() for variant in
                variants}

    def assign_variant(self, test_id: str, user_id: int) ->ABTestVariant:
        """
        Assign user to a test variant.

        Uses deterministic hash-based assignment to ensure
        consistent variant assignment for the same user.

        Args:
            test_id: Test identifier
            user_id: User identifier

        Returns:
            Assigned variant
        """
        with self._lock:
            if test_id not in self._tests:
                raise ValueError(f'Test {test_id} not found')
            if user_id in self._user_assignments[test_id]:
                return self._user_assignments[test_id][user_id]
            variants = self._tests[test_id]['variants']
            hash_val = hashlib.md5(f'{test_id}:{user_id}'.encode()).hexdigest()
            index = int(hash_val, 16) % len(variants)
            variant = variants[index]
            self._user_assignments[test_id][user_id] = variant
            return variant

    def record_conversion(self, test_id: str, user_id: int, variant:
        ABTestVariant) ->None:
        """
        Record conversion for test variant.

        Args:
            test_id: Test identifier
            user_id: User identifier
            variant: Test variant
        """
        with self._lock:
            if test_id not in self._tests:
                raise ValueError(f'Test {test_id} not found')
            assigned_variant = self._user_assignments[test_id].get(user_id)
            if assigned_variant != variant:
                raise ValueError(
                    f'User {user_id} not assigned to variant {variant} in test {test_id}'
                    )
            self._conversions[test_id][variant].add(user_id)

    def get_test_results(self, test_id: str) ->dict[str, Any]:
        """
        Get A/B test results with statistical analysis.

        Args:
            test_id: Test identifier

        Returns:
            Dictionary with test results including:
            - test_id: Test identifier
            - test_name: Test name
            - variants: Statistics for each variant
            - winner: Best performing variant
            - confidence: Statistical confidence level
        """
        with self._lock:
            if test_id not in self._tests:
                raise ValueError(f'Test {test_id} not found')
            test = self._tests[test_id]
            variants = test['variants']
            variant_stats = {}
            for variant in variants:
                assigned_count = sum(1 for v in self._user_assignments[
                    test_id].values() if v == variant)
                conversion_count = len(self._conversions[test_id][variant])
                conversion_rate = (conversion_count / assigned_count if
                    assigned_count > 0 else 0.0)
                variant_stats[variant.value] = {'variant': variant.value,
                    'assigned': assigned_count, 'conversions':
                    conversion_count, 'conversion_rate': conversion_rate}
            winner = None
            max_rate = 0.0
            for variant_name, stats in variant_stats.items():
                if stats['conversion_rate'] > max_rate:
                    max_rate = stats['conversion_rate']
                    winner = variant_name
            total_samples = sum(s['assigned'] for s in variant_stats.values())
            confidence = self._calculate_confidence(total_samples)
            return {'test_id': test_id, 'test_name': test['test_name'],
                'status': test['status'], 'created_at': test['created_at'].
                isoformat(), 'variants': variant_stats, 'winner': winner,
                'confidence': confidence}

    def _calculate_confidence(self, total_samples: int) ->float:
        """
        Calculate statistical confidence level.

        Simplified calculation based on sample size.
        Production systems should use proper statistical tests.

        Args:
            total_samples: Total number of samples

        Returns:
            Confidence level (0.0 to 1.0)
        """
        if total_samples < 100:
            return 0.0
        elif total_samples < 500:
            return 0.5
        elif total_samples < 1000:
            return 0.7
        elif total_samples < 5000:
            return 0.85
        else:
            return 0.95

    def get_all_tests(self) ->list[dict[str, Any]]:
        """
        Get all A/B tests.

        Returns:
            List of test metadata
        """
        with self._lock:
            return [{'test_id': test_id, 'test_name': test['test_name'],
                'status': test['status'], 'created_at': test['created_at'].
                isoformat(), 'variant_count': len(test['variants'])} for
                test_id, test in self._tests.items()]


__all__ = ['InMemoryABTestRepository']
