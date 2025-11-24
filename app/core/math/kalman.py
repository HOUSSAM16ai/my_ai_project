"""
KALMAN FILTER LATENCY ESTIMATOR (Hyper-Morphic V6: Adaptive Resonance)
========================================================================
Implements a 1D Adaptive Kalman Filter that dynamically adjusts its
internal plasticity (Process Noise Q) based on Innovation Magnitude.

This allows the system to:
1. Ignore noise when stable (Low Q, High R).
2. "Wake up" and learn instantly when the environment changes (High Q).
3. "Clamp" extreme outliers to prevent destabilization from single spikes.
"""

import math
from dataclasses import dataclass


@dataclass
class KalmanFilter:
    """
    Adaptive Recursive Filter with Outlier Clamping.
    """

    # Initial State Estimate (x_hat)
    estimate: float = 1000.0

    # Initial Error Covariance (P)
    error_covariance: float = 1000.0

    # Base Process Noise (Q_base) - The "Heartbeat" uncertainty
    base_process_noise: float = 0.01

    # Measurement Noise (R) - High to reject jitter
    measurement_noise: float = 5000.0

    # Adaptation Factor (k_adapt)
    # Scales the Process Noise injection based on the "Resonance Ratio".
    # Increased to 300.0 for aggressive learning of valid shifts.
    adaptation_factor: float = 300.0

    # Resonance Clamp
    # Caps the "Resonance Ratio" (Innovation^2 / R) to prevent infinite Q explosion
    # on massive single-sample outliers (e.g., 100x latency spikes).
    # A value of 60.0 means we stop increasing plasticity after a ~7.7-sigma event.
    resonance_clamp: float = 60.0

    def predict(self):
        """
        Time Update (Predict).
        """
        self.error_covariance = self.error_covariance + self.base_process_noise

    def update(self, measurement: float) -> float:
        """
        Measurement Update (Correct) with Clamped Adaptive Resonance.
        """
        # 1. Calculate Innovation (Residual)
        innovation = measurement - self.estimate
        innovation_sq = innovation**2

        # 2. Adaptive Q Scaling (The "Resonance")
        # resonance_ratio = (y - y_hat)^2 / R
        resonance_ratio = innovation_sq / self.measurement_noise

        # 3. Apply Clamp (The "Stoic Guard")
        # Protects against extreme outliers destabilizing the filter.
        effective_ratio = min(resonance_ratio, self.resonance_clamp)

        # 4. Inject Uncertainty
        adaptive_q = self.adaptation_factor * effective_ratio
        self.error_covariance += adaptive_q

        # 5. Standard Kalman Update
        kalman_gain = self.error_covariance / (self.error_covariance + self.measurement_noise)

        # Update Estimate
        self.estimate = self.estimate + kalman_gain * innovation

        # Update Error Covariance
        self.error_covariance = (1.0 - kalman_gain) * self.error_covariance

        return self.estimate

    def get_estimate(self) -> float:
        return self.estimate
