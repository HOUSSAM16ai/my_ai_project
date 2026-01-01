"""
COGNITIVE FINGERPRINTING V1
============================

This module analyzes a prompt and generates a "Cognitive Fingerprint,"
a vector representing the cognitive skills required to fulfill the request.
"""

import re
from dataclasses import dataclass
from enum import Enum

class CognitiveComplexity(Enum):
    """
    Refined Cognitive Complexity Levels.
    """

    REFLEX = 0  # Simple, direct questions.
    THOUGHT = 1  # Requires reasoning, summarization, multi-step instructions.
    DEEP_THOUGHT = 2  # High complexity, deep analysis, code generation.
    CREATIVE = 3  # Poetry, story writing, artistic tasks.
    LOGICAL_REASONING = 4  # Puzzles, math problems, structured logic.

@dataclass
class CognitiveFingerprint:
    """
    Represents the cognitive requirements of a prompt.
    """

    complexity: CognitiveComplexity = CognitiveComplexity.REFLEX
    # Future: Add vectors for creativity, logic, etc.
    # e.g., skill_vectors: dict[str, float] = field(default_factory=dict)

class FingerprintAnalyzer:
    """
    Analyzes prompts to determine their cognitive fingerprint.
    """

    def __init__(self):
        # More sophisticated patterns
        self.code_keywords = re.compile(
            r"\b(def|class|import|function|return|=>|\{|\}|\[|\]|implement|algorithm)\b",
            re.IGNORECASE,
        )
        # V2: Detects word problems with numbers and units (e.g., "60 mph", "10 meters")
        self.math_keywords = re.compile(
            r"\b(calculate|solve|equation|derivative|integral|matrix|vector|proof)\b|\d+\s*(mph|km/h|meters|feet|seconds)",
            re.IGNORECASE,
        )
        self.creative_keywords = re.compile(
            r"\b(write a poem|story|imagine|create a character|dialogue|script|haiku)\b",
            re.IGNORECASE,
        )
        self.reasoning_keywords = re.compile(
            r"\b(explain|analyze|compare|contrast|summarize|what are the implications)\b",
            re.IGNORECASE,
        )

    def assess_complexity(self, prompt: str) -> CognitiveComplexity:
        """
        Heuristic analysis V2 of the prompt.
        This is the new generation of complexity assessment.
        """
        prompt_lower = prompt.lower()
        length = len(prompt)

        # 1. Check for high-complexity indicators first
        if self.creative_keywords.search(prompt_lower):
            return CognitiveComplexity.CREATIVE

        if self.code_keywords.search(prompt) or "```" in prompt:
            return CognitiveComplexity.DEEP_THOUGHT

        if self.math_keywords.search(prompt_lower):
            return CognitiveComplexity.LOGICAL_REASONING

        # 2. Check for mid-level complexity
        if self.reasoning_keywords.search(prompt_lower) or length > 700:
            return CognitiveComplexity.THOUGHT

        # 3. Default to simple
        return CognitiveComplexity.REFLEX

_analyzer = FingerprintAnalyzer()

def assess_cognitive_complexity(prompt: str) -> CognitiveComplexity:
    """
    Singleton access to the analyzer.
    """
    return _analyzer.assess_complexity(prompt)
