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
from dataclasses import dataclass, field
from app.core.math.hyper_flux import HyperFluxCapacitor


@dataclass
class KalmanFilter:
    """
    Adaptive Recursive Filter with Flux Shielding.
    """
    estimate: float = 1000.0
    error_covariance: float = 1000.0
    base_process_noise: float = 0.01
    measurement_noise: float = 5000.0
    adaptation_factor: float = 300.0
    resonance_clamp: float = 60.0
    flux_capacitor: HyperFluxCapacitor = field(default_factory=
        HyperFluxCapacitor)

    def predict(self):
        """
        Time Update (Predict).
        """
        self.error_covariance = self.error_covariance + self.base_process_noise

    def update(self, measurement: float) ->float:
        """
        Measurement Update (Correct) with Flux Shielding.
        """
        innovation = measurement - self.estimate
        innovation_sq = innovation ** 2
        self.flux_capacitor.observe_flux(innovation)
        shield_factor = self.flux_capacitor.predict_volatility()
        resonance_ratio = innovation_sq / self.measurement_noise
        effective_ratio = min(resonance_ratio, self.resonance_clamp)
        adaptive_q = self.adaptation_factor * effective_ratio * shield_factor
        self.error_covariance += adaptive_q
        kalman_gain = self.error_covariance / (self.error_covariance + self
            .measurement_noise)
        self.estimate = self.estimate + kalman_gain * innovation
        self.error_covariance = (1.0 - kalman_gain) * self.error_covariance
        return self.estimate
