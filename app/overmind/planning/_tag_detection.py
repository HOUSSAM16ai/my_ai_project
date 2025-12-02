# app/overmind/planning/_tag_detection.py
"""
Tag detection logic extracted from deep_indexer using Strategy pattern.
Provides extensible, data-driven tag classification for code analysis.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TagRule:
    """Rule for detecting a specific tag in code."""

    patterns: tuple[str, ...]
    tag: str

    def matches(self, code_lower: str) -> bool:
        """Check if any pattern matches the code."""
        return any(pattern in code_lower for pattern in self.patterns)


# Registry of tag detection rules (extensible without complexity increase)
TAG_DETECTION_RULES: list[TagRule] = [
    TagRule(patterns=("async def ",), tag="async"),
    TagRule(patterns=(" for ", " while "), tag="iterative"),
    TagRule(patterns=("math.", "import math"), tag="numeric"),
    TagRule(patterns=("re.",), tag="regex"),
    TagRule(patterns=("requests.", "httpx.", "urllib."), tag="network"),
    TagRule(patterns=("flask", "fastapi", "django"), tag="web"),
    TagRule(patterns=("os.", "subprocess"), tag="system"),
    TagRule(patterns=("sklearn", "torch", "tensorflow", "xgboost"), tag="ml"),
    TagRule(patterns=("openai", "anthropic", "gemini", "langchain", "llama"), tag="llm"),
]


def categorize_code(code: str) -> list[str]:
    """
    Categorize code by detecting technology tags.

    Args:
        code: Source code string to analyze

    Returns:
        Sorted list of detected tags
    """
    code_lower = code.lower()
    tags = {rule.tag for rule in TAG_DETECTION_RULES if rule.matches(code_lower)}
    return sorted(tags)


def add_tag_rule(patterns: tuple[str, ...], tag: str) -> None:
    """
    Add a new tag detection rule to the registry.

    Args:
        patterns: Tuple of string patterns to match
        tag: Tag name to assign when matched
    """
    TAG_DETECTION_RULES.append(TagRule(patterns=patterns, tag=tag))
