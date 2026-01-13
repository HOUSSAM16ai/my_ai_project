"""
Semantic Cache Module (Cognitive Resonance Engine).

This module implements a "Hyper-Dimensional Semantic Cache" that transcends
traditional exact-match caching. It utilizes "Resonance Algorithms" to detect
semantic similarity between queries.

Refactored to be Async and Type-Safe (Harvard/Berkeley Standards).
"""

import logging
import re
import time
from collections import deque
from difflib import SequenceMatcher
from typing import ClassVar

from pydantic import BaseModel, Field

from app.core.types import JSONDict

logger = logging.getLogger(__name__)

# --- Configuration ---
RESONANCE_THRESHOLD = 0.60
CACHE_TTL = 3600  # 1 Hour
MAX_MEMORY_SLOTS = 1000


class SemanticEngram(BaseModel):
    """
    Represents a stored memory pattern in the Cognitive Cache.
    Using Pydantic for validation.
    """

    original_prompt: str
    context_hash: str
    normalized_tokens: set[str]
    response_payload: list[JSONDict]
    created_at: float = Field(default_factory=time.time)
    access_count: int = 0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > CACHE_TTL


class SemanticCache:
    """
    The Brain that remembers.
    Implements fuzzy semantic matching asynchronously.
    """

    # Singleton instance holder
    _instance: ClassVar["SemanticCache | None"] = None

    def __init__(self) -> None:
        self.memory: deque[SemanticEngram] = deque(maxlen=MAX_MEMORY_SLOTS)
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    @classmethod
    def get_instance(cls) -> "SemanticCache":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _normalize(self, text: str) -> set[str]:
        """
        Reduces text to its atomic semantic tokens.
        CPU-bound, but fast enough for now.
        """
        text = text.lower()
        # Remove non-alphanumeric (keep spaces)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        tokens = set(text.split())
        # Basic stop words
        stop_words = {
            "the",
            "is",
            "at",
            "which",
            "on",
            "a",
            "an",
            "and",
            "or",
            "of",
            "to",
            "in",
            "for",
            "with",
        }
        return tokens - stop_words

    def _calculate_resonance(
        self, tokens_a: set[str], tokens_b: set[str], text_a: str, text_b: str
    ) -> float:
        """
        Calculates the "Resonance Score" (Similarity) between two inputs.
        """
        if not tokens_a or not tokens_b:
            return 0.0

        # 1. Jaccard Similarity (Token Overlap)
        intersection = len(tokens_a.intersection(tokens_b))
        union = len(tokens_a.union(tokens_b))
        jaccard_score = intersection / union if union > 0 else 0.0

        # 2. Containment Bonus
        min_len = min(len(tokens_a), len(tokens_b))
        containment_score = intersection / min_len if min_len > 0 else 0.0

        # 3. Structural Similarity (Sequence Matcher)
        # Only run if Jaccard is promising (> 0.2) to save CPU
        structural_score = 0.0
        if jaccard_score > 0.2:
            structural_score = SequenceMatcher(None, text_a, text_b).ratio()

        # Weighted Average:
        # Jaccard: 30%, Containment: 30%, Structure: 40%
        return (jaccard_score * 0.3) + (containment_score * 0.3) + (structural_score * 0.4)

    async def recall(self, prompt: str, context_hash: str) -> list[JSONDict] | None:
        """
        Attempts to recall a memory that resonates with the input prompt.
        Async to allow for potential future database offloading without changing API.
        """
        input_tokens = self._normalize(prompt)
        if not input_tokens:
            return None

        # In a real async scenario with a DB, we would await a DB call here.
        # For in-memory deque, we just run it. If it becomes slow, we can
        # offload to a thread pool.
        best_engram: SemanticEngram | None = None
        best_score = 0.0

        for engram in self.memory:
            if engram.is_expired:
                continue

            if engram.context_hash != context_hash:
                continue

            score = self._calculate_resonance(
                input_tokens, engram.normalized_tokens, prompt, engram.original_prompt
            )

            if score > best_score:
                best_score = score
                best_engram = engram

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

    async def memorize(
        self, prompt: str, context_hash: str, response: list[JSONDict]
    ) -> None:
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
        self.memory.appendleft(engram)
        logger.debug(f"Memorized new pattern: '{prompt[:30]}...'")

    def get_stats(self) -> dict[str, int]:
        return {
            **self._stats,
            "memory_usage": len(self.memory),
            "capacity": MAX_MEMORY_SLOTS,
        }


def get_semantic_cache() -> SemanticCache:
    """Dependency Injection Provider"""
    return SemanticCache.get_instance()
