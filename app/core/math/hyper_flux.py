"""
HYPER-FLUX CAPACITOR (Singularity Matrix Engine)
================================================
This module implements the "Singularity Matrix" algorithm for predictive
outlier detection. It uses a rolling window of "Flux Vectors" (Innovation History)
to calculate a "Dimensional Z-Score".

When the Dimensional Z-Score exceeds the "Event Horizon", the system predicts
an incoming volatility storm and pre-emptively stiffens the Kalman Filter's
plasticity (lowers Q), effectively "shielding" the state estimate from chaos.
"""

import statistics
from collections import deque
from dataclasses import dataclass, field

@dataclass
class HyperFluxCapacitor:
    """
    Manages the Flux State of the system.
    """

    # The Event Horizon (Z-Score Threshold)
    # If the flux exceeds this, we are in a volatility storm.
    event_horizon: float = 2.5

    # Memory Depth (How far back we look into the abyss)
    memory_depth: int = 20

    # The Flux History (Rolling window of squared innovations)
    _flux_history: deque[float] = field(default_factory=lambda: deque(maxlen=20))

    def observe_flux(self, innovation: float) -> None:
        """
        Record a new flux vector (innovation).
        """
        # We store the magnitude of the flux (squared innovation)
        self._flux_history.append(innovation**2)

    def predict_volatility(self) -> float:
        """
        Returns the 'Flux Shielding Factor'.
        Range: [0.0, 1.0]
        1.0 = Total Calm (Normal Operation)
        0.0 = Singularity (Maximum Shielding / Minimum Plasticity)
        """
        if len(self._flux_history) < 5:
            return 1.0

        # Calculate Dimensional Z-Score of the recent flux
        mean_flux = statistics.mean(self._flux_history)
        stdev_flux = statistics.stdev(self._flux_history) if len(self._flux_history) > 1 else 0.0

        if stdev_flux == 0:
            return 1.0

        recent_flux = self._flux_history[-1]
        z_score = (recent_flux - mean_flux) / stdev_flux

        if z_score > self.event_horizon:
            # We are approaching the singularity!
            # Shielding active!
            # The higher the Z-Score, the stronger the shield (lower factor)
            shield_strength = max(0.0, 1.0 - (z_score - self.event_horizon))
            return shield_strength

        return 1.0
