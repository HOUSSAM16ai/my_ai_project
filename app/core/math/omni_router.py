"""
OMNI-COGNITIVE ROUTING ENGINE (Hyper-Morphic V7: Singularity Ready)
================================================
The "God-Mode" Router.
"""

import math
import random
import threading
import time
from dataclasses import dataclass, field

from app.core.math.cognitive_fingerprint import (
    CognitiveComplexity,
    assess_cognitive_complexity,
)
from app.core.math.kalman import KalmanFilter


@dataclass
class ContextualBeliefState:
    """
    Belief state for a specific Context Bucket.
    """

    alpha: float = 1.0
    beta: float = 1.0
    failure_streak: int = 0
    last_decay: float = field(default_factory=time.time)


@dataclass
class OmniNodeState:
    """
    The brain of a single provider.
    """

    model_id: str
    kalman_filter: KalmanFilter = field(default_factory=KalmanFilter)

    # The Skill Tree: Map[Complexity -> Belief]
    skills: dict[CognitiveComplexity, ContextualBeliefState] = field(default_factory=dict)

    _lock: threading.Lock = field(default_factory=threading.Lock)

    def __post_init__(self):
        # Initialize all skills
        for level in CognitiveComplexity:
            self.skills[level] = ContextualBeliefState()

    def update(self, complexity: CognitiveComplexity, success: bool, raw_latency_ms: float):
        """
        Update the specific skill belief based on outcome.
        """
        with self._lock:
            # 1. Update Latency Belief (Global for the node)
            self.kalman_filter.predict()
            true_latency = self.kalman_filter.update(raw_latency_ms)

            # 2. Get the specific skill belief
            belief = self.skills[complexity]

            # 3. Temporal Decay
            now = time.time()
            if now - belief.last_decay > 3600:
                decay = 0.95
                belief.alpha = max(1.0, belief.alpha * decay)
                belief.beta = max(1.0, belief.beta * decay)
                belief.last_decay = now

            # 4. Calculate Reward based on Kalman-Filtered Latency
            if success:
                # Latency Penalty
                # < 2000ms = Good reward. > 2000ms = Lower reward.
                latency_penalty = 1.0 / (1.0 + math.exp((true_latency - 2000) / 1000))

                # Boost reward: Range [0.5, 2.0]
                # If fast (penalty ~ 1.0) -> reward 2.0 (Alpha grows fast)
                # If slow (penalty ~ 0.5) -> reward 1.25
                weighted_reward = 1.0 + (1.0 * latency_penalty)

                belief.alpha += weighted_reward
                belief.failure_streak = 0
            else:
                # Penalty
                belief.beta += 2.0  # Stronger penalty for failure
                belief.failure_streak += 1

                if belief.failure_streak >= 3:
                    belief.alpha = max(1.0, belief.alpha * 0.5)

    def sample(self, complexity: CognitiveComplexity) -> float:
        """
        Sample from the specific skill distribution.
        """
        belief = self.skills.get(complexity, self.skills[CognitiveComplexity.REFLEX])
        return random.betavariate(belief.alpha, belief.beta)


class OmniCognitiveRouter:
    """
    The Router.
    """

    def __init__(self):
        self.nodes: dict[str, OmniNodeState] = {}
        self._lock = threading.Lock()

    def reset(self):
        """Reset state for testing."""
        with self._lock:
            self.nodes = {}

    def register_node(self, model_id: str):
        with self._lock:
            if model_id not in self.nodes:
                self.nodes[model_id] = OmniNodeState(model_id=model_id)

    def get_ranked_nodes(self, available_model_ids: list[str], prompt: str) -> list[str]:
        """
        Context-Aware Ranking.
        """
        complexity = assess_cognitive_complexity(prompt)

        candidates = []
        for mid in available_model_ids:
            if mid not in self.nodes:
                self.register_node(mid)

            node = self.nodes[mid]
            score = node.sample(complexity)
            candidates.append((mid, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates]

    def record_outcome(self, model_id: str, prompt: str, success: bool, latency_ms: float):
        if model_id not in self.nodes:
            self.register_node(model_id)

        complexity = assess_cognitive_complexity(prompt)
        self.nodes[model_id].update(complexity, success, latency_ms)


# Singleton
_omni_router = OmniCognitiveRouter()


def get_omni_router() -> OmniCognitiveRouter:
    return _omni_router
