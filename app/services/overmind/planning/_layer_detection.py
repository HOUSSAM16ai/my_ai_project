"""
Layer detection logic extracted from deep_indexer using Chain of Responsibility pattern.
Classifies file paths into architectural layers based on ordered rules.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class LayerRule:
    """Rule for detecting architectural layer from path."""
    keywords: frozenset[str]
    layer: str

    def matches(self, segments_lower: list[str]) ->bool:
        """Check if any keyword matches any path segment."""
        return any(keyword in seg for seg in segments_lower for keyword in
            self.keywords)


LAYER_DETECTION_RULES: list[LayerRule] = [LayerRule(keywords=frozenset([
    'test']), layer='tests'), LayerRule(keywords=frozenset(['migrations']),
    layer='migrations'), LayerRule(keywords=frozenset(['api', 'routes']),
    layer='api'), LayerRule(keywords=frozenset(['services', 'service']),
    layer='service'), LayerRule(keywords=frozenset(['models', 'schemas']),
    layer='model'), LayerRule(keywords=frozenset(['utils', 'helpers']),
    layer='utility'), LayerRule(keywords=frozenset(['scripts', 'cli']),
    layer='script'), LayerRule(keywords=frozenset(['config', 'settings']),
    layer='config')]


def detect_layer(path: str, enabled: bool=True) ->(str | None):
    """
    Detect architectural layer from file path.

    Args:
        path: File path to analyze
        enabled: Whether layer detection is enabled

    Returns:
        Layer name or None if no match found
    """
    if not enabled:
        return None
    segments = path.replace('\\', '/').split('/')
    segments_lower = [s.lower() for s in segments]
    for rule in LAYER_DETECTION_RULES:
        if rule.matches(segments_lower):
            return rule.layer
    return None
