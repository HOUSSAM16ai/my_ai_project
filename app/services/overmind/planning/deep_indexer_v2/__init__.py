"""
Deep Indexer V2 - The Eye of Overmind.
Scans the codebase to produce a concise 'Cognitive Map' (summary).
"""
from .core import build_index
from .models import IndexResult
from .summary import summarize_for_prompt

__all__ = ["build_index", "summarize_for_prompt", "IndexResult"]
