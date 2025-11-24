
"""
BAYESIAN INFERENCE ROUTING ENGINE (Hyper-Morphic V5)
====================================================
Implements Advanced Thompson Sampling for Multi-Armed Bandit Routing.
This engine mathematically optimizes the Exploration-Exploitation trade-off,
allowing the system to "learn" the optimal AI provider in real-time under uncertainty.

Mathematical Foundation:
------------------------
Posterior ~ Beta(alpha, beta)
where:
    alpha = 1 + successes
    beta = 1 + failures

We sample from the posterior to determine the routing probability, strictly dominating
standard Softmax or Epsilon-Greedy approaches in non-stationary environments.
"""

import math
import random
import time
from dataclasses import dataclass, field
import threading
from typing import Dict, List, Optional

@dataclass
class BayesianNodeState:
    """
    Represents the Probabilistic Belief State of a single Neural Node.
    Thread-safe atomic updates.
    """
    model_id: str
    alpha: float = 1.0  # Successes (Prior = 1)
    beta: float = 1.0   # Failures (Prior = 1)

    # Chaos Resilience: Decay parameters over time to handle non-stationary distributions
    # (i.e., if a provider was bad yesterday, it might be good today)
    last_decay: float = field(default_factory=time.time)

    # Shock Absorber: Track consecutive failures to detect sudden outages
    failure_streak: int = 0

    _lock: threading.Lock = field(default_factory=threading.Lock)

    def update(self, success: bool, weight: float = 1.0):
        """
        Bayesian Update of the Posterior.
        Weight allows for partial rewards (e.g. latency-weighted).
        """
        with self._lock:
            # 1. Temporal Decay (Forgetting Factor)
            now = time.time()
            elapsed = now - self.last_decay
            # Decay every hour roughly
            if elapsed > 3600:
                decay_factor = 0.95  # Retain 95% of knowledge
                self.alpha = max(1.0, self.alpha * decay_factor)
                self.beta = max(1.0, self.beta * decay_factor)
                self.last_decay = now

            if success:
                # Reset streak on success
                self.failure_streak = 0
                self.alpha += weight
            else:
                self.failure_streak += 1
                self.beta += weight

                # 2. Shock Decay (Rapid Adaptation)
                # If we hit a streak of failures, our historical confidence (alpha) is likely outdated.
                # We slash alpha to "reset" our belief and force re-evaluation.
                if self.failure_streak >= 3:
                    # Penalize alpha: The higher the streak, the more we doubt history.
                    # This allows the Mean (alpha / alpha+beta) to drop rapidly.
                    self.alpha = max(1.0, self.alpha * 0.5)

    def sample(self) -> float:
        """
        Thompson Sampling: Draw a random sample from Beta(alpha, beta).
        Returns a value in [0, 1].
        """
        return random.betavariate(self.alpha, self.beta)

    def mean(self) -> float:
        """Expected value of reliability."""
        return self.alpha / (self.alpha + self.beta)

    def variance(self) -> float:
        """Uncertainty measure."""
        return (self.alpha * self.beta) / (
            (self.alpha + self.beta)**2 * (self.alpha + self.beta + 1)
        )

class BayesianRouter:
    """
    The Brain of the Neural Mesh.
    Manages the probabilistic states of all AI providers.
    """
    def __init__(self):
        self.nodes: Dict[str, BayesianNodeState] = {}
        self._lock = threading.Lock()

    def register_node(self, model_id: str):
        with self._lock:
            if model_id not in self.nodes:
                self.nodes[model_id] = BayesianNodeState(model_id=model_id)

    def get_ranked_nodes(self, available_model_ids: List[str]) -> List[str]:
        """
        Returns model_ids sorted by their Thompson Sample (Probability of being the best).
        This inherently handles exploration: high uncertainty (low alpha/beta) results
        in high variance samples, giving new nodes a chance to be picked.
        """
        candidates = []
        for mid in available_model_ids:
            if mid not in self.nodes:
                self.register_node(mid)

            node = self.nodes[mid]
            score = node.sample()
            candidates.append((mid, score))

        # Sort by sample score descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates]

    def record_outcome(self, model_id: str, success: bool, latency_ms: float):
        """
        Feedback Loop.
        We weight the success update by latency.
        If it's successful but slow, the reward is smaller.
        """
        if model_id not in self.nodes:
            self.register_node(model_id)

        # Latency Penalty Function: Sigmoid-like decay
        # < 1000ms = 1.0 reward
        # > 5000ms = approaches 0.5 reward even if success
        if success:
            reward = 1.0 / (1.0 + math.exp((latency_ms - 2000) / 1000))
            # Normalize to [0.5, 1.0] for success
            weighted_reward = 0.5 + (0.5 * reward)
            self.nodes[model_id].update(success=True, weight=weighted_reward)
        else:
            # Failure is fully penalized
            self.nodes[model_id].update(success=False, weight=1.0)

# Global Singleton
_bayesian_router = BayesianRouter()

def get_bayesian_router() -> BayesianRouter:
    return _bayesian_router
