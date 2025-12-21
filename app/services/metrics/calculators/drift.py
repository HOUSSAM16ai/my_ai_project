import statistics
from abc import ABC, abstractmethod
from collections import Counter
from typing import Any


class DriftCalculationStrategy(ABC):
    """Abstract Strategy for Drift Calculation"""

    @abstractmethod
    def calculate_drift(self, baseline: list[Any], current: list[Any]) -> float:
        """Calculate drift score between 0.0 and 1.0"""
        pass


class NumericDriftStrategy(DriftCalculationStrategy):
    """Calculates drift for numeric data using statistical moments"""

    def calculate_drift(self, baseline: list[Any], current: list[Any]) -> float:
        baseline_nums = [float(x) for x in baseline]
        current_nums = [float(x) for x in current]

        baseline_mean = statistics.mean(baseline_nums)
        current_mean = statistics.mean(current_nums)
        baseline_std = statistics.stdev(baseline_nums) if len(baseline_nums) > 1 else 1.0
        current_std = statistics.stdev(current_nums) if len(current_nums) > 1 else 1.0

        # Normalized difference in means
        mean_shift = abs(baseline_mean - current_mean) / (baseline_std + 1e-10)

        # Difference in standard deviations
        std_shift = abs(baseline_std - current_std) / (baseline_std + 1e-10)

        # Combined drift score (0-1)
        drift = min(1.0, (mean_shift + std_shift) / 4.0)

        return drift


class CategoricalDriftStrategy(DriftCalculationStrategy):
    """Calculates drift for categorical data using distribution comparison"""

    def calculate_drift(self, baseline: list[Any], current: list[Any]) -> float:
        baseline_dist = Counter(baseline)
        current_dist = Counter(current)

        all_keys = set(baseline_dist.keys()) | set(current_dist.keys())
        total_diff = 0.0

        for key in all_keys:
            baseline_prob = baseline_dist.get(key, 0) / len(baseline)
            current_prob = current_dist.get(key, 0) / len(current)
            total_diff += abs(baseline_prob - current_prob)

        # Total variation distance (0-1)
        return total_diff / 2.0


class DriftCalculatorContext:
    """Context to select the appropriate drift strategy"""

    def calculate_drift(self, baseline: list[Any], current: list[Any]) -> float:
        # Simple heuristic to determine type: check if the first element is a number
        # In a real system, schema metadata would be better.
        try:
            if baseline and isinstance(baseline[0], (int, float)):
                # Try converting to float to be sure it's numeric logic
                float(baseline[0])
                strategy = NumericDriftStrategy()
            else:
                # If conversion fails or it's not a number, treat as categorical
                strategy = CategoricalDriftStrategy()
        except (ValueError, TypeError):
            strategy = CategoricalDriftStrategy()

        # Fallback if first item check isn't enough (e.g. mixed types),
        # the Numeric strategy might still fail if later elements are strings.
        # So we wrap execution.
        try:
            return strategy.calculate_drift(baseline, current)
        except (ValueError, TypeError):
            # Fallback to categorical if numeric fails on data issues
            return CategoricalDriftStrategy().calculate_drift(baseline, current)
