# app/core/cognitive_cache.py
"""
THE COGNITIVE RESONANCE ENGINE (V1 - OMEGA).

This module implements a "Hyper-Dimensional Semantic Cache" that transcends
traditional exact-match caching. It utilizes "Resonance Algorithms" to detect
semantic similarity between queries, allowing the system to recall answers
to questions that are "spiritually identical" even if syntactically different.

TECHNOLOGIES:
- Token-Set Holography (Jaccard Similarity on N-grams).
- Structural Echo Detection (Sequence Matching).
- Adaptive Resonance Thresholding.
"""

import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# --- Configuration ---
RESONANCE_THRESHOLD = 0.60  # Tuned for high-recall in V1 (Caveman-speak compatibility)
CACHE_TTL = 3600  # 1 Hour
MAX_MEMORY_SLOTS = 1000  # Max number of semantic patterns to hold


@dataclass
class SemanticEngram:
    """
    Represents a stored memory pattern in the Cognitive Cache.
    """

    original_prompt: str
    context_hash: str  # Hash of the conversation history to ensure context safety
    normalized_tokens: set[str]
    response_payload: list[dict]  # The full chat history or response chunks
    created_at: float = field(default_factory=time.time)
    access_count: int = 0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > CACHE_TTL


class CognitiveResonanceEngine:
    """
    The Brain that remembers.
    Implements fuzzy semantic matching without heavy ML dependencies.
    """

    def __init__(self):
        self.memory: deque[SemanticEngram] = deque(maxlen=MAX_MEMORY_SLOTS)
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _normalize(self, text: str) -> set[str]:
        """
        Reduces text to its atomic semantic tokens.
        - Lowercase
        - Remove punctuation
        - Stop word filtering (basic)
        """
        text = text.lower()
        # Remove non-alphanumeric (keep spaces)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        tokens = set(text.split())
        # Basic stop words (can be expanded)
        stop_words = {"the", "is", "at", "which", "on", "a", "an", "and", "or", "of", "to"}
        return tokens - stop_words

    def _calculate_resonance(
        self, tokens_a: set[str], tokens_b: set[str], text_a: str, text_b: str
    ) -> float:
        """
        Calculates the "Resonance Score" (Similarity) between two inputs.
        Combines Token Overlap (Jaccard) with Structural Similarity.
        """
        if not tokens_a or not tokens_b:
            return 0.0

        # 1. Jaccard Similarity (Token Overlap)
        intersection = len(tokens_a.intersection(tokens_b))
        union = len(tokens_a.union(tokens_b))
        jaccard_score = intersection / union if union > 0 else 0.0

        # 2. Containment Bonus (If one is a subset of the other)
        # Helps with "tell joke computers" vs "tell me a joke about computers"
        min_len = min(len(tokens_a), len(tokens_b))
        containment_score = intersection / min_len if min_len > 0 else 0.0

        # 3. Structural Similarity (Sequence Matcher) - computationally more expensive but more accurate for order
        # We only run this if Jaccard is promising (> 0.3) to save CPU
        structural_score = 0.0
        if jaccard_score > 0.2:
            structural_score = SequenceMatcher(None, text_a, text_b).ratio()

        # Weighted Average:
        # Jaccard: 30%, Containment: 30%, Structure: 40%
        return (jaccard_score * 0.3) + (containment_score * 0.3) + (structural_score * 0.4)

    def _find_best_match(
        self, input_tokens: set[str], prompt: str, context_hash: str
    ) -> tuple[SemanticEngram | None, float]:
        """
        Scans memory for the most resonant engram.
        """
        best_engram = None
        best_score = 0.0

        # Linear scan of memory (acceptable for <1000 items).
        # For larger scales, we would use LSH (Locality Sensitive Hashing).
        for engram in self.memory:
            if engram.is_expired:
                continue

            # Strict Context Check: Different context = Different universe.
            if engram.context_hash != context_hash:
                continue

            score = self._calculate_resonance(
                input_tokens, engram.normalized_tokens, prompt, engram.original_prompt
            )

            if score > best_score:
                best_score = score
                best_engram = engram

        return best_engram, best_score

    def recall(self, prompt: str, context_hash: str) -> list[dict] | None:
        """
        Attempts to recall a memory that resonates with the input prompt.
        Must match context_hash exactly (Safety First!) but allows fuzzy match on prompt.
        """
        input_tokens = self._normalize(prompt)
        if not input_tokens:
            return None

        best_engram, best_score = self._find_best_match(input_tokens, prompt, context_hash)

        if best_score >= RESONANCE_THRESHOLD and best_engram:
            logger.info(
                f"Cognitive Resonance Detected! Score: {best_score:.4f} | "
                f"Query: '{prompt}' matches '{best_engram.original_prompt}'"
            )
            best_engram.access_count += 1
            self._stats["hits"] += 1
            return best_engram.response_payload

        self._stats["misses"] += 1
        return None

    def memorize(self, prompt: str, context_hash: str, response: list[dict]) -> None:
        """
        Stores a new experience in the Cognitive Cache.
        """
        tokens = self._normalize(prompt)
        if not tokens:
            return

        engram = SemanticEngram(
            original_prompt=prompt,
            context_hash=context_hash,
            normalized_tokens=tokens,
            response_payload=response,
        )
        self.memory.appendleft(engram)  # MRU (Most Recently Used) logic via appendleft + maxlen
        logger.debug(f"Memorized new pattern: '{prompt[:30]}...'")

    def get_stats(self) -> None:
        return {**self._stats, "memory_usage": len(self.memory), "capacity": MAX_MEMORY_SLOTS}


# Singleton Instance
_cognitive_engine = CognitiveResonanceEngine()


def get_cognitive_engine() -> CognitiveResonanceEngine:
    return _cognitive_engine
