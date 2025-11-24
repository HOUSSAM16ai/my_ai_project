"""
KALMAN FILTER LATENCY ESTIMATOR (Hyper-Morphic V5)
==================================================
Implements a 1D Kalman Filter for optimal state estimation of
stochastic latency signals in a noisy network environment.
"""

from dataclasses import dataclass

@dataclass
class KalmanFilter:
    """
    Recursive filter that estimates the internal state of a linear dynamic system
    from a series of noisy measurements.
    """
    # Initial State Estimate (x_hat) - Assume 1000ms start
    estimate: float = 1000.0

    # Initial Error Covariance (P)
    error_covariance: float = 1000.0

    # Process Noise Covariance (Q)
    # How much does true latency drift? Low = stable connection.
    process_noise: float = 1.0

    # Measurement Noise Covariance (R)
    # High R = We treat spikes as noise.
    # Increased to 5000.0 to aggressively reject outliers (e.g. GC pauses).
    measurement_noise: float = 5000.0

    def predict(self):
        """
        Time Update (Predict).
        """
        self.error_covariance = self.error_covariance + self.process_noise

    def update(self, measurement: float) -> float:
        """
        Measurement Update (Correct).
        """
        # Kalman Gain (K)
        kalman_gain = self.error_covariance / (self.error_covariance + self.measurement_noise)

        # Update Estimate
        self.estimate = self.estimate + kalman_gain * (measurement - self.estimate)

        # Update Error Covariance
        self.error_covariance = (1.0 - kalman_gain) * self.error_covariance

        return self.estimate

    def get_estimate(self) -> float:
        return self.estimate
