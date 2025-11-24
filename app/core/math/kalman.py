"""
KALMAN FILTER LATENCY ESTIMATOR (Hyper-Morphic V7: Singularity Ready)
========================================================================
Now integrated with the HYPER-FLUX CAPACITOR.

This V7 Engine combines:
1. Adaptive Resonance (V6) for normal plasticity.
2. Flux Shielding (V7) for precognitive outlier rejection.

When the Flux Capacitor predicts a singularity, this filter automatically
hardens its covariance matrix, rejecting the "Chaos of the Void".
"""

import math
from dataclasses import dataclass, field
from app.core.math.hyper_flux import HyperFluxCapacitor

@dataclass
class KalmanFilter:
    """
    Adaptive Recursive Filter with Flux Shielding.
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
    adaptation_factor: float = 300.0

    # Resonance Clamp
    resonance_clamp: float = 60.0

    # THE FLUX CAPACITOR
    flux_capacitor: HyperFluxCapacitor = field(default_factory=HyperFluxCapacitor)

    def predict(self):
        """
        Time Update (Predict).
        """
        self.error_covariance = self.error_covariance + self.base_process_noise

    def update(self, measurement: float) -> float:
        """
        Measurement Update (Correct) with Flux Shielding.
        """
        # 1. Calculate Innovation (Residual)
        innovation = measurement - self.estimate
        innovation_sq = innovation**2

        # 2. FEED THE FLUX CAPACITOR
        self.flux_capacitor.observe_flux(innovation)
        shield_factor = self.flux_capacitor.predict_volatility()

        # 3. Adaptive Q Scaling (The "Resonance")
        # resonance_ratio = (y - y_hat)^2 / R
        resonance_ratio = innovation_sq / self.measurement_noise

        # 4. Apply Clamp (The "Stoic Guard")
        effective_ratio = min(resonance_ratio, self.resonance_clamp)

        # 5. Inject Uncertainty, MODULATED BY SHIELD FACTOR
        # If shield_factor is low (singularity detected), plasticity is reduced.
        adaptive_q = (self.adaptation_factor * effective_ratio) * shield_factor
        self.error_covariance += adaptive_q

        # 6. Standard Kalman Update
        kalman_gain = self.error_covariance / (self.error_covariance + self.measurement_noise)

        # Update Estimate
        self.estimate = self.estimate + kalman_gain * innovation

        # Update Error Covariance
        self.error_covariance = (1.0 - kalman_gain) * self.error_covariance

        return self.estimate

    def get_estimate(self) -> float:
        return self.estimate
